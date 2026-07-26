# Tasks: CourseHub API Implementation

**Feature**: CourseHub API (`001-coursehub-api`)

**Created**: 2026-06-27

**Status**: Ready for Implementation

**Reference**: [spec.md](spec.md) | [plan.md](plan.md)

---

## Implementation Strategy

This task list follows a dependency-ordered, phase-based approach:

1. **Phase 1 (Setup)**: Project initialization, database schema, migrations
2. **Phase 2 (Foundation)**: Auth layer with JWT and role-based access control
3. **Phase 3 (Integration)**: Resend email service via BackgroundTask
4. **Phase 4 (Domain - US1)**: Instructor course management (CRUD, ownership, deletion constraint)
5. **Phase 5 (Domain - US2)**: Student registration, enrollment, discovery
6. **Phase 6 (Domain - US3)**: Progress tracking and student data isolation
7. **Phase 7 (Testing)**: Comprehensive test suite and coverage validation
8. **Phase 8 (Polish)**: Error handling, response envelope, observability

Each phase is independently testable. Phases 4–6 map to user stories and can be developed in parallel after Phase 3.

---

## Phase 1: Project Setup & Database Schema

- [ ] T001 Create project structure: `app/`, `app/core/`, `app/models/`, `app/schemas/`, `app/routers/`, `app/services/`, `tests/`
- [ ] T002 Initialize Python project: `pyproject.toml` or `requirements.txt` with FastAPI, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, Alembic, pytest, httpx, python-jose, passlib, resend
- [ ] T003 Configure database connection: `app/core/config.py` with async PostgreSQL URL, connection pool settings, environment variable support
- [ ] T004 Initialize Alembic: `alembic init` with async template, configure `alembic.ini` for async execution
- [ ] T005 Define ORM models in `app/models.py`:
  - User (id: UUID, email: string unique, hashed_password: string, display_name: string, role: Enum["student", "instructor"], created_at: datetime)
  - Course (id: UUID, instructor_id: FK→User, title: string, description: string, price_cents: integer, published: boolean, created_at: datetime, updated_at: datetime)
  - Module (id: UUID, course_id: FK→Course, title: string, order: integer, created_at: datetime) — enforce unique(course_id, order)
  - Enrollment (id: UUID, student_id: FK→User, course_id: FK→Course, progress: integer 0-100, completed_at: datetime nullable, created_at: datetime, updated_at: datetime) — enforce unique(student_id, course_id)
- [ ] T006 Create initial Alembic migration with all four tables and relationships
- [ ] T007 Set up async database session factory in `app/core/database.py`: AsyncSession context, dependency injection for FastAPI
- [ ] T008 Verify schema: Run migration on test PostgreSQL instance and confirm all tables exist

**Dependencies**: None (Phase 1 blocks all others)

**Test Criteria**: 
- `alembic upgrade head` succeeds
- All four tables present in test DB with correct columns and FK constraints
- AsyncSession can be created and cleaned up without errors

---

## Phase 2: Auth Router & JWT Flow

- [ ] T009 Create `app/core/security.py`:
  - `create_access_token(data: dict, expires_delta: timedelta=15min)` → JWT string
  - `create_refresh_token(data: dict, expires_delta: timedelta=7days)` → JWT string
  - `verify_token(token: str, token_type: str)` → dict (async-safe)
  - `get_password_hash(password: str)` → bcrypt hash
  - `verify_password(plain: str, hashed: str)` → bool

- [ ] T010 Create `app/core/dependencies.py`:
  - `get_db()` → AsyncSession (FastAPI Depends)
  - `get_current_user(token: str = Depends(HTTPBearer()))` → User (async, validates access token, raises HTTPException 401 if invalid)
  - `get_current_instructor(current_user: User = Depends(get_current_user))` → User (assert role == "instructor", raise 403 if not)
  - `get_current_student(current_user: User = Depends(get_current_user))` → User (assert role == "student", raise 403 if not)

- [ ] T011 Create `app/schemas/envelope.py`:
  - `APIResponse[T]` (Pydantic v2) with fields: data: T, meta: dict (timestamp, path, status), errors: list[dict]
  - Ensure all endpoints wrap responses in this envelope

- [ ] T012 Create `app/schemas/auth.py` (Pydantic v2):
  - `UserRegister` (email: EmailStr, password: str with validation, display_name: str)
  - `UserLogin` (email: EmailStr, password: str)
  - `TokenResponse` (access_token: str, refresh_token: str, token_type: str = "bearer", expires_in: int)
  - `UserResponse` (id: UUID, email: str, display_name: str, role: Enum)

- [ ] T013 Create `app/routers/auth.py` with endpoints:
  - `POST /api/v1/auth/register`:
    - Validate email uniqueness (query User by email)
    - Hash password with bcrypt
    - Create User with role="student"
    - Generate access + refresh tokens
    - Return TokenResponse + UserResponse
    - Return 201 Created wrapped in APIResponse
    - Do NOT send email (deferred to Phase 3)
  - `POST /api/v1/auth/login`:
    - Query User by email
    - Verify password with bcrypt
    - Generate access + refresh tokens (no role distinction in login)
    - Return TokenResponse + UserResponse
    - Return 200 OK wrapped in APIResponse
  - `POST /api/v1/auth/refresh`:
    - Accept refresh_token from request body
    - Validate refresh_token (verify_token with token_type="refresh")
    - Extract user_id and role from token
    - Generate new access_token
    - Return TokenResponse
    - Return 200 OK wrapped in APIResponse

- [ ] T014 Create `app/main.py`:
  - Initialize FastAPI app
  - Register auth router at `/api/v1`
  - Add global exception handler (stub for Phase 8)

**Dependencies**: Phase 1 (DB schema must exist)

**Test Criteria**:
- `POST /auth/register` creates user and returns tokens (201)
- `POST /auth/login` accepts valid credentials and returns tokens (200)
- `POST /auth/login` rejects invalid credentials (401)
- `POST /auth/refresh` returns new access token (200)
- `POST /auth/refresh` rejects invalid refresh token (401)
- Access token expires after 15 minutes (verify JWT exp claim)
- Refresh token expires after 7 days (verify JWT exp claim)

---

## Phase 3: Resend Email Integration & BackgroundTask

- [ ] T015 Create `app/services/email.py`:
  - `send_welcome_email_async(email: str, name: str, course_browse_link: str)` → async function
  - Load `RESEND_API_KEY` from environment; raise ConfigError if missing
  - Use Resend Python SDK to send email
  - Template body: "Welcome, {name}! Browse published courses at {course_browse_link}"
  - Handle Resend exceptions gracefully (log error, do not raise)

- [ ] T016 Integrate email into auth register endpoint:
  - In `app/routers/auth.py`, POST `/auth/register`:
    - After user creation and token generation
    - Create `background_tasks.add_task(send_welcome_email_async, email=user.email, name=user.display_name, course_browse_link="http://localhost:8000/api/v1/courses")`
    - Return response immediately (email sent after response)

- [ ] T017 Create test mock fixture for Resend in `tests/conftest.py`:
  - Mock `resend.Emails.send()` to avoid real API calls
  - Track calls for assertion in tests

**Dependencies**: Phase 2 (auth register endpoint must exist)

**Test Criteria**:
- Registration endpoint returns 201 before email is sent
- BackgroundTask is queued with correct email parameters
- Resend SDK is called with correct template and recipient
- Missing RESEND_API_KEY raises ConfigError at startup (not at request time)

---

## Phase 4: Courses Router — Instructor Management (US1)

**User Story**: Instructor manages courses

- [ ] T018 [P] Create `app/schemas/courses.py` (Pydantic v2):
  - `ModuleCreate` (title: str, order: int)
  - `ModuleResponse` (id: UUID, course_id: UUID, title: str, order: int, created_at: datetime)
  - `CourseCreate` (title: str, description: str, price_cents: int, published: bool, modules: list[ModuleCreate])
  - `CourseUpdate` (title: str, description: str, price_cents: int, published: bool)
  - `CourseResponse` (id: UUID, instructor_id: UUID, title: str, description: str, price_cents: int, published: bool, created_at: datetime, updated_at: datetime, modules: list[ModuleResponse])

- [ ] T019 [US1] Create `app/services/courses.py`:
  - `get_course_by_id(session: AsyncSession, course_id: UUID)` → Course | None (async)
  - `verify_course_ownership(session: AsyncSession, course_id: UUID, instructor_id: UUID)` → None or raise PermissionError (async)
  - `check_course_has_enrollments(session: AsyncSession, course_id: UUID)` → bool (async)
  - `delete_course_with_ownership_check(session: AsyncSession, course_id: UUID, instructor_id: UUID)` → None or raise BusinessRuleViolation (async, enforces ActiveEnrollmentConstraint)

- [ ] T020 [US1] Create `app/routers/courses.py` with endpoints:
  - `POST /api/v1/courses` (instructor-only):
    - Require `get_current_instructor` dependency
    - Accept CourseCreate payload
    - Create Course row with instructor_id = current_user.id
    - Create Module rows for each module in payload (in a single async transaction)
    - Return CourseResponse (201 Created)
  - `GET /api/v1/courses` (instructor-only):
    - Require `get_current_instructor` dependency
    - Query all courses where instructor_id == current_user.id
    - Support pagination: skip, limit query params
    - Return list[CourseResponse] (200 OK)
  - `GET /api/v1/courses/{course_id}` (public for published, instructor for own):
    - If authenticated instructor: return course if owner or if published
    - If student/unauthenticated: return only if published
    - Return CourseResponse (200 OK) or 404 Not Found
  - `PUT /api/v1/courses/{course_id}` (instructor-only, owner):
    - Require `get_current_instructor` dependency
    - Verify ownership using service
    - Accept CourseUpdate payload
    - Update course fields
    - Return CourseResponse (200 OK)
  - `DELETE /api/v1/courses/{course_id}` (instructor-only, owner):
    - Require `get_current_instructor` dependency
    - Call `delete_course_with_ownership_check` service
    - If no enrollments: delete course (FK cascade deletes modules)
    - If active enrollments: raise BusinessRuleViolation → 409 Conflict with "ACTIVE_ENROLLMENT_CONSTRAINT" error code
    - Return 204 No Content if successful, 409 Conflict if active enrollments

**Dependencies**: Phase 2 (auth dependencies), Phase 1 (DB models)

**Test Criteria**:
- Instructor can create course with modules (201)
- Instructor can list only their own courses
- Student cannot see unpublished courses (404)
- Instructor can update own course (200)
- Instructor cannot update another instructor's course (403)
- DELETE with active enrollments returns 409 Conflict with "ACTIVE_ENROLLMENT_CONSTRAINT" error
- DELETE without enrollments succeeds (204)

---

## Phase 5: Enrollments Router — Student Discovery & Enrollment (US2)

**User Story**: Student registers and enrols

- [ ] T021 [P] [US2] Create `app/schemas/enrolments.py` (Pydantic v2):
  - `EnrollmentCreate` (course_id: UUID)
  - `EnrollmentUpdate` (progress: int, completed_at: datetime | None)
  - `EnrollmentResponse` (id: UUID, student_id: UUID, course_id: UUID, progress: int, completed_at: datetime | None, created_at: datetime, updated_at: datetime)

- [ ] T022 [US2] Create `app/services/enrolments.py`:
  - `get_user_enrollment(session: AsyncSession, enrollment_id: UUID, student_id: UUID)` → Enrollment | None (async, enforces student ownership)
  - `create_enrollment_if_published(session: AsyncSession, student_id: UUID, course_id: UUID)` → Enrollment (async, verifies course is published, checks unique constraint)
  - `validate_progress(progress: int)` → None or raise ValueError if not 0-100 (sync)

- [ ] T023 [US2] Create `app/routers/enrolments.py` with endpoints:
  - `POST /api/v1/enrollments` (student-only):
    - Require `get_current_student` dependency
    - Accept EnrollmentCreate payload
    - Verify course exists and is published (raise 409 Conflict if not published)
    - Check unique(student_id, course_id) constraint (raise 409 Conflict if already enrolled)
    - Create Enrollment with progress=0, completed_at=None
    - Return EnrollmentResponse (201 Created)
  - `GET /api/v1/enrollments` (student-only):
    - Require `get_current_student` dependency
    - Query all enrollments where student_id == current_user.id
    - Support pagination: skip, limit query params
    - Return list[EnrollmentResponse] (200 OK)
  - `GET /api/v1/enrollments/{enrollment_id}` (student-only, owner):
    - Require `get_current_student` dependency
    - Use service to get enrollment with ownership check
    - Return EnrollmentResponse (200 OK) or 403 Forbidden or 404 Not Found
  - `PUT /api/v1/enrollments/{enrollment_id}` (student-only, owner):
    - Require `get_current_student` dependency
    - Use service to get enrollment with ownership check
    - Accept EnrollmentUpdate payload
    - Validate progress is 0–100
    - If progress == 100 and completed_at is None: set completed_at = now()
    - Update and return EnrollmentResponse (200 OK)

**Dependencies**: Phase 2 (auth dependencies), Phase 1 (DB models), Phase 4 (courses must exist)

**Test Criteria**:
- Student can enroll in published course (201)
- Student cannot enroll in unpublished course (409)
- Student cannot enroll twice in same course (409)
- Student can list only their own enrollments
- Student can update own enrollment progress (200)
- Student cannot update another student's enrollment (403)
- Progress == 100 auto-sets completed_at (200)

---

## Phase 6: Progress Tracking & Data Isolation (US3)

**User Story**: Progress is tracked and exposed safely

- [ ] T024 [US3] Implement progress validation in enrolments service:
  - `validate_progress(progress: int)` rejects values outside 0-100

- [ ] T025 [US3] Implement student data isolation in enrollments router:
  - Verify all GET/PUT operations check student_id == current_user.id
  - Raise 403 Forbidden if student attempts to access another student's enrollment

- [ ] T026 [US3] Test end-to-end: Student enrolls → updates progress 0% → 50% → 100% → completed_at is set

**Dependencies**: Phase 5 (enrollment endpoints must exist)

**Test Criteria**:
- Progress values outside 0-100 are rejected (400)
- Student cannot access another student's enrollment (403)
- Progress update to 100 sets completed_at automatically
- Student cannot update another student's progress (403)

---

## Phase 7: Testing & Coverage

- [ ] T027 Create `tests/conftest.py`:
  - Pytest fixtures for async test support (`pytest-asyncio`)
  - Test PostgreSQL fixture (separate test DB)
  - `async_session` fixture (AsyncSession scoped to test)
  - `client` fixture (AsyncClient with FastAPI app and dependency overrides)
  - Resend mock fixture

- [ ] T028 Create `tests/test_auth.py`:
  - Test register: Valid input → 201, user created, tokens returned, email queued
  - Test register: Duplicate email → 400 Conflict
  - Test register: Weak password → 400 Validation error
  - Test login: Valid email/password → 200, tokens returned
  - Test login: Invalid credentials → 401 Unauthorized
  - Test refresh: Valid refresh token → 200, new access token
  - Test refresh: Invalid refresh token → 401 Unauthorized

- [ ] T029 Create `tests/test_courses.py`:
  - Test POST: Instructor creates course with modules → 201
  - Test GET: Instructor lists only own courses
  - Test GET: Student sees only published courses
  - Test GET by ID: Published course visible to student, unpublished only to owner
  - Test PUT: Instructor updates own course → 200
  - Test PUT: Instructor cannot update other instructor's course → 403
  - Test DELETE: Instructor deletes course without enrollments → 204
  - **Test DELETE: Instructor attempts to delete course with active enrollments → 409 Conflict with ACTIVE_ENROLLMENT_CONSTRAINT**

- [ ] T030 Create `tests/test_enrolments.py`:
  - Test POST: Student enrolls in published course → 201
  - Test POST: Student cannot enroll in unpublished course → 409
  - Test POST: Student cannot enroll twice → 409
  - Test GET: Student lists only own enrollments
  - Test GET by ID: Student accesses own enrollment → 200
  - Test GET by ID: Student cannot access other student's enrollment → 403
  - Test PUT: Student updates own enrollment progress → 200
  - Test PUT: Progress == 100 sets completed_at
  - Test PUT: Student cannot update other student's enrollment → 403

- [ ] T031 Create `tests/test_integration.py`:
  - End-to-end workflow:
    1. Register student (POST /auth/register)
    2. Create instructor + login
    3. Instructor creates published course
    4. Student browses courses (GET /courses)
    5. Student enrolls (POST /enrollments)
    6. Student updates progress (PUT /enrollments/{id})
    7. Verify completion flow

- [ ] T032 Run pytest with coverage:
  - `pytest tests/ --cov=app --cov-report=term-missing --cov-report=html`
  - Target 80%+ coverage on business logic
  - Verify all routers, services, and security functions are tested

**Dependencies**: All phases 2–6

**Test Criteria**:
- All tests pass
- 80%+ coverage on business logic (routes, services, security)
- DELETE course with active enrollments explicitly tested and passes
- No mocking of PostgreSQL; uses real test instance

---

## Phase 8: Response Envelope & Error Handling

- [ ] T033 [P] Create global exception handler in `app/main.py`:
  - Catch `PermissionError` → 403 Forbidden with "FORBIDDEN" error code
  - Catch `BusinessRuleViolation` → 409 Conflict with specific error code (e.g., "ACTIVE_ENROLLMENT_CONSTRAINT")
  - Catch `ValueError` (validation errors) → 400 Bad Request with "VALIDATION_ERROR" code
  - Catch Pydantic `ValidationError` → 400 Bad Request with field-level errors
  - Catch `HTTPException` (from dependencies) → pass through
  - Catch unexpected exceptions → 500 Internal Server Error with "INTERNAL_ERROR" code
  - Wrap all error responses in APIResponse envelope

- [ ] T034 [P] Create response middleware in `app/main.py`:
  - Intercept all responses
  - Wrap successful responses in APIResponse envelope (if not already wrapped)
  - Add timestamp and path to meta
  - Ensure consistent error envelope format

- [ ] T035 [P] Verify HTTP status codes are consistent:
  - 200 OK: GET, PUT successful
  - 201 Created: POST successful (resource created)
  - 204 No Content: DELETE successful
  - 400 Bad Request: Validation errors
  - 401 Unauthorized: Missing/invalid/expired token
  - 403 Forbidden: Authenticated but lacks role/permission
  - 404 Not Found: Resource doesn't exist
  - 409 Conflict: Business rule violation, duplicate, unpublished course
  - 500 Internal Server Error: Unexpected errors

- [ ] T036 Verify all responses follow envelope format:
  - Success: `{"data": <T>, "meta": {...}, "errors": []}`
  - Error: `{"data": null, "meta": {...}, "errors": [{"code": "...", "message": "...", ...}]}`

**Dependencies**: All routers (Phases 2–6)

**Test Criteria**:
- All error paths return wrapped APIResponse
- HTTP status codes match contract (see contracts.md)
- Envelope format consistent across all endpoints

---

## Dependency Graph

```
Phase 1 (Setup)
  ↓
Phase 2 (Auth)
  ↓
Phase 3 (Email)
  ↓
├→ Phase 4 (Courses - US1) →→┐
├→ Phase 5 (Enrollments - US2)→ Phase 6 (Progress - US3)
└────────────────────────────→┘
  ↓
Phase 7 (Testing)
  ↓
Phase 8 (Error Handling)
```

**Parallelization Opportunities**:
- Phases 4, 5, 6 can run in parallel after Phase 3
- Phase 8 can be integrated incrementally throughout other phases

---

## Success Criteria

- All 36 tasks completed
- All tests pass (`pytest tests/`)
- 80%+ coverage on business logic
- DELETE course with active enrollments returns 409 with ACTIVE_ENROLLMENT_CONSTRAINT
- Full end-to-end workflow testable: register → create course → enroll → track progress
- All responses wrapped in APIResponse envelope
- HTTP status codes match contract

---

## MVP Scope (Phase 1 Delivery)

For a minimal viable product, focus on:

1. **Phases 1–3**: Database, auth, email integration (foundation)
2. **Phase 4**: Course CRUD with ownership (instructor workflow)
3. **Phase 5**: Student enrollment (student workflow)
4. **Phase 7**: Core tests (coverage on auth, courses, enrollments)

Phases 6 and 8 can be incrementally added post-MVP.
