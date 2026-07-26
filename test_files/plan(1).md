# Plan: CourseHub API Implementation

## TL;DR
Implement a FastAPI + PostgreSQL REST API with three routers (auth, courses, enrolments). Start with the auth layer (JWT + refresh tokens) to establish role-based access control before touching domain logic. Use async SQLAlchemy throughout, structure enrolments to enforce course ownership and student data isolation, and integrate Resend email via BackgroundTask to prevent registration blocking. Flag the course deletion constraint (active enrolments → 409) as a named business rule.

## Steps

### Phase 1: Project Foundation & Database Schema
1. Create project structure: `app/`, `app/core/`, `app/models/`, `app/schemas/`, `app/routers/`, `app/services/`, `tests/`
2. Initialize dependencies: FastAPI, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, Alembic, pytest, httpx, python-jose, passlib, python-multipart, resend
3. Configure database connection pool with async PostgreSQL (asyncpg)
4. Set up Alembic migrations directory and initial migration scaffolding
5. Define core models:
   - `User` (id, email, hashed_password, display_name, role: "student" | "instructor", created_at)
   - `Course` (id, instructor_id: FK→User, title, description, price_cents, published, created_at, updated_at)
   - `Module` (id, course_id: FK→Course, title, order, created_at) — enforce ordering
   - `Enrollment` (id, student_id: FK→User, course_id: FK→Course, progress: int (0-100), completed_at, created_at, updated_at) — unique(student_id, course_id)
6. Create initial Alembic migration to create all tables
7. Set up database session factory (`AsyncSession` context) with dependency injection pattern

**Dependencies**: None. Can run independently.

---

### Phase 2: Auth Router — JWT & Refresh Token Flow
1. Create `app/core/security.py`:
   - `create_access_token(data, expires_delta=15 min)` 
   - `create_refresh_token(data, expires_delta=7 days)`
   - `verify_token(token, token_type)` — async JWT verification
   - `get_password_hash(password)` and `verify_password(plain, hashed)`

2. Create `app/core/dependencies.py`:
   - `get_db()` — async session dependency
   - `get_current_user(token: str)` — extract and validate access token, return User object
   - `get_current_instructor(current_user)` — assert role == "instructor"
   - `get_current_student(current_user)` — assert role == "student"

3. Create `app/schemas/auth.py` (Pydantic v2):
   - `UserRegister` (email, password, display_name)
   - `UserLogin` (email, password)
   - `TokenResponse` (access_token, refresh_token, token_type)
   - `UserResponse` (id, email, display_name, role)

4. Create `app/routers/auth.py`:
   - `POST /api/v1/auth/register` (student-only):
     - Validate email uniqueness, hash password, create User with role="student"
     - Return access + refresh tokens
     - **Do NOT send email here** — defer to Phase 3
   - `POST /api/v1/auth/login`:
     - Verify email + password, return tokens (no role distinction in login)
   - `POST /api/v1/auth/refresh`:
     - Accept refresh_token, validate, return new access_token

5. Create response envelope wrapper (`app/schemas/envelope.py`):
   - `APIResponse(data=T, meta=dict, errors=list)` — apply to all endpoints

**Dependencies**: None. Blocks domain routers until complete.

---

### Phase 3: Resend Email Integration as Service
1. Create `app/services/email.py`:
   - `send_welcome_email_async(email: str, name: str, course_browse_link: str)` — calls Resend SDK
   - Load `RESEND_API_KEY` from environment; raise ConfigError if missing
   - Template: "Welcome, {name}! Browse courses: {link}"

2. Wrap the email call in a FastAPI `BackgroundTask` that runs **after** registration response is sent:
   - In auth router's register endpoint, create `background_tasks.add_task(send_welcome_email_async, ...)`
   - This ensures registration completes and returns tokens before email is attempted

3. Create test fixture for Resend mock (for testing without API calls)

**Dependencies**: Phase 2 (auth router must exist). Blocks enrolment tests that validate email behavior.

---

### Phase 4: Courses Router — CRUD with Ownership
1. Create `app/schemas/courses.py` (Pydantic v2):
   - `ModuleCreate` (title, order)
   - `CourseCreate` (title, description, price_cents, published, modules: list[ModuleCreate])
   - `CourseUpdate` (title, description, price_cents, published)
   - `CourseResponse` (id, instructor_id, title, description, price_cents, published, modules: list[ModuleResponse])

2. Create `app/routers/courses.py`:
   - `POST /api/v1/courses` (instructor-only):
     - Requires `get_current_instructor` dependency
     - Create Course + child Modules in a single async transaction
     - Return CourseResponse with modules
   - `GET /api/v1/courses/{course_id}` (public):
     - Return published courses only for students (check role in query)
   - `GET /api/v1/courses` (instructor-only):
     - Return only instructor's own courses (filter by instructor_id == current_user.id)
   - `PUT /api/v1/courses/{course_id}` (instructor-only):
     - Verify ownership, update course fields
   - `DELETE /api/v1/courses/{course_id}` (instructor-only):
     - **NAMED BUSINESS RULE: "ActiveEnrollmentConstraint"**
     - Check if any Enrollment rows exist for this course
     - If yes: return 409 Conflict with message "Cannot delete course with active enrollments"
     - If no: delete course (cascading delete modules via FK)

3. Create `app/services/courses.py`:
   - `get_course_by_id(session, course_id)` — async
   - `verify_course_ownership(session, course_id, instructor_id)` — async, raises PermissionError if not owner
   - `check_course_has_enrollments(session, course_id)` — async, returns bool
   - `delete_course_with_ownership_check(session, course_id, instructor_id)` — async, enforces ActiveEnrollmentConstraint, raises BusinessRuleViolation if active enrollments

**Dependencies**: Phase 2 (auth roles). Blocks enrolment router.

---

### Phase 5: Enrolments Router — Student Access & Progress
1. Create `app/schemas/enrolments.py` (Pydantic v2):
   - `EnrollmentCreate` (course_id)
   - `EnrollmentUpdate` (progress: int, completed_at: datetime | null)
   - `EnrollmentResponse` (id, student_id, course_id, progress, completed_at, created_at)

2. Create `app/routers/enrolments.py`:
   - `POST /api/v1/enrollments` (student-only):
     - Validate course is published
     - Check unique(student_id, course_id) constraint
     - Create Enrollment with progress=0, completed_at=None
   - `GET /api/v1/enrollments` (student-only):
     - Return only current_user's enrollments (filter by student_id == current_user.id)
   - `GET /api/v1/enrollments/{enrollment_id}` (student-only):
     - Verify the enrollment belongs to current_user, return it
   - `PUT /api/v1/enrollments/{enrollment_id}` (student-only):
     - Verify ownership (student_id == current_user.id)
     - Validate progress is 0–100
     - If progress == 100 and completed_at is None: set completed_at to now()
     - Update and return

3. Create `app/services/enrolments.py`:
   - `get_user_enrollment(session, enrollment_id, student_id)` — async, enforces access control
   - `create_enrollment_if_published(session, student_id, course_id)` — async, verifies course is published
   - `validate_progress(progress: int)` — raises ValueError if not 0–100

**Dependencies**: Phase 2 (student role), Phase 4 (courses exist).

---

### Phase 6: Testing & Verification
1. Set up pytest configuration:
   - Use `pytest-asyncio` for async test support
   - Configure test PostgreSQL fixture (separate DB from dev)
   - Create `conftest.py` with session scope fixtures: `async_session`, `client` (AsyncClient with override dependencies)

2. Create test suite (`tests/`):
   - `test_auth.py`: Registration (with email background task mock), login, refresh, role isolation
   - `test_courses.py`: Create course, list (instructor vs student views), update, **test DELETE with active enrollments (expect 409)**
   - `test_enrolments.py`: Create enrollment (published courses only), list (own only), update progress, access control
   - End-to-end integration test: Register student → browse published courses → enroll → update progress

3. Target 80%+ coverage on business logic (use pytest-cov)

4. Mock Resend email calls in tests (use monkeypatch or dependency override)

**Dependencies**: All routers (Phase 2–5). Can run in parallel once Phase 1 DB is ready.

---

### Phase 7: Response Envelope & Error Handling
1. Create global exception handler in `app/main.py`:
   - Catch `PermissionError`, `BusinessRuleViolation`, `ValueError`, etc.
   - Return APIResponse with errors field populated
2. Middleware to wrap all responses in envelope shape
3. Consistent HTTP status codes: 200 (success), 201 (created), 400 (validation), 401 (auth), 403 (forbidden), 409 (conflict), 500 (error)

**Dependencies**: All routers.

---

## Relevant Files

- **Database & models**: `app/models.py` — define User, Course, Module, Enrollment ORM classes (async SQLAlchemy)
- **Auth layer**: `app/core/security.py`, `app/core/dependencies.py` — JWT, tokens, role checks
- **Routers**: `app/routers/auth.py`, `app/routers/courses.py`, `app/routers/enrolments.py` — REST endpoints
- **Services**: `app/services/` — business logic, async DB helpers, Resend integration
- **Schemas**: `app/schemas/` — Pydantic v2 request/response models, envelope wrapper
- **Main**: `app/main.py` — FastAPI app init, middleware, global exception handlers
- **Config**: `app/core/config.py` — environment variables, database URL, Resend API key
- **Migrations**: `alembic/versions/` — Alembic-managed schema changes
- **Tests**: `tests/conftest.py`, `tests/test_auth.py`, `tests/test_courses.py`, `tests/test_enrolments.py` — pytest suite with real PostgreSQL

## Verification

1. **Phase 1**: Run Alembic migrate; verify all tables exist in test DB
2. **Phase 2**: Run `pytest tests/test_auth.py`; verify tokens are issued and validated correctly
3. **Phase 3**: Mock Resend call; verify BackgroundTask is queued; email sent after response returned
4. **Phase 4**: Run `pytest tests/test_courses.py`; **specifically test DELETE with active enrollments returns 409**
5. **Phase 5**: Run `pytest tests/test_enrolments.py`; verify student isolation and progress validation
6. **Phase 6**: Run full suite: `pytest tests/ --cov=app --cov-report=term-missing`; verify 80%+ coverage
7. **Phase 7**: Test all error paths return wrapped APIResponse

## Decisions

- **Auth first**: JWT + refresh tokens before any domain logic to establish trust boundary and role-based access control.
- **Async throughout**: All DB calls use `AsyncSession` and async/await; no synchronous SQLAlchemy.
- **Background email**: Resend integration deferred via BackgroundTask so registration API call completes before email attempt; prevents blocking on external service latency.
- **Named business rule**: "ActiveEnrollmentConstraint" explicitly flagged in courses router delete logic; 409 Conflict returned when violated.
- **Shared user table**: Single `User` table with `role` field (not separate instructor/student tables) to simplify foreign keys and keep schema lean.
- **Async ORM only**: No raw SQL; SQLAlchemy ORM used exclusively for all persistence.

## Further Considerations

1. **Refresh token storage**: Current design stores refresh tokens in JWT; for higher security, consider persisting them in a `RefreshToken` table with revocation support.
2. **Email template**: Email body is hardcoded in `send_welcome_email_async`; consider moving to a template file or Resend template if complexity grows.
3. **Course ordering**: Module ordering is enforced at schema level (order column); if modules can be reordered post-creation, consider adding a reorder endpoint or bulk update endpoint.
