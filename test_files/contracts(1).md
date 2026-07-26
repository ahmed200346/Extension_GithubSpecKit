# API Contracts: CourseHub

**Created**: 2026-06-27

**Reference**: [spec.md](spec.md) | [plan.md](plan.md)

---

## API Overview

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **Version**: v1 (all endpoints under `/api/v1/`)
- **Authentication**: JWT Bearer tokens in `Authorization: Bearer <token>` header

---

## Response Envelope

All responses follow a consistent envelope shape per constitution:

```json
{
  "data": <T>,
  "meta": {
    "timestamp": "2026-06-27T12:00:00Z",
    "path": "/api/v1/courses",
    "status": 200
  },
  "errors": []
}
```

**Error envelope** (when errors occur):

```json
{
  "data": null,
  "meta": {
    "timestamp": "2026-06-27T12:00:00Z",
    "path": "/api/v1/auth/register",
    "status": 400
  },
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Email already registered",
      "field": "email"
    }
  ]
}
```

---

## Authentication Endpoints

### POST `/api/v1/auth/register`

**Role**: Student (self-registration)

**Request**:

```json
{
  "email": "student@example.com",
  "password": "securepassword123",
  "display_name": "Alice Student"
}
```

**Response** (201 Created):

```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "student@example.com",
      "display_name": "Alice Student",
      "role": "student",
      "created_at": "2026-06-27T12:00:00Z"
    },
    "tokens": {
      "access_token": "eyJhbGc...",
      "refresh_token": "eyJhbGc...",
      "token_type": "bearer",
      "expires_in": 900
    }
  },
  "meta": {...},
  "errors": []
}
```

**Side Effects**:
- Welcome email sent via Resend (async BackgroundTask) with student's name and link to browse courses
- Email does NOT block response

**Errors**:
- `400 Bad Request`: Email invalid or already registered
- `400 Bad Request`: Password too weak
- `400 Bad Request`: Display name missing

---

### POST `/api/v1/auth/login`

**Role**: Public (student or instructor)

**Request**:

```json
{
  "email": "student@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):

```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "student@example.com",
      "display_name": "Alice Student",
      "role": "student"
    },
    "tokens": {
      "access_token": "eyJhbGc...",
      "refresh_token": "eyJhbGc...",
      "token_type": "bearer",
      "expires_in": 900
    }
  },
  "meta": {...},
  "errors": []
}
```

**Errors**:
- `401 Unauthorized`: Invalid email or password

---

### POST `/api/v1/auth/refresh`

**Role**: Public (with valid refresh token)

**Request**:

```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response** (200 OK):

```json
{
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {...},
  "errors": []
}
```

**Token Expiry**:
- Access token: 15 minutes
- Refresh token: 7 days

**Errors**:
- `401 Unauthorized`: Refresh token invalid or expired

---

## Courses Endpoints

### POST `/api/v1/courses`

**Role**: Instructor-only

**Authorization Header**: `Authorization: Bearer <access_token>`

**Request**:

```json
{
  "title": "Introduction to Python",
  "description": "Learn Python basics",
  "price_cents": 9999,
  "published": false,
  "modules": [
    { "title": "Module 1: Basics", "order": 1 },
    { "title": "Module 2: Advanced", "order": 2 }
  ]
}
```

**Response** (201 Created):

```json
{
  "data": {
    "id": "course-uuid",
    "instructor_id": "user-uuid",
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "price_cents": 9999,
    "published": false,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:00:00Z",
    "modules": [
      { "id": "module-uuid-1", "title": "Module 1: Basics", "order": 1 },
      { "id": "module-uuid-2", "title": "Module 2: Advanced", "order": 2 }
    ]
  },
  "meta": {...},
  "errors": []
}
```

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not an instructor
- `400 Bad Request`: Invalid course data or modules

---

### GET `/api/v1/courses`

**Role**: Instructor-only (returns own courses)

**Authorization Header**: `Authorization: Bearer <access_token>`

**Query Parameters**: (optional)
- `skip`: int (default 0)
- `limit`: int (default 10)

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": "course-uuid",
      "instructor_id": "user-uuid",
      "title": "Introduction to Python",
      "description": "Learn Python basics",
      "price_cents": 9999,
      "published": false,
      "created_at": "2026-06-27T12:00:00Z",
      "updated_at": "2026-06-27T12:00:00Z",
      "modules": [...]
    }
  ],
  "meta": {
    "total": 5,
    "skip": 0,
    "limit": 10,
    ...
  },
  "errors": []
}
```

**Behavior**: Only returns courses owned by the current instructor.

---

### GET `/api/v1/courses/{course_id}`

**Role**: Public (published courses) or Instructor (own courses)

**Authorization Header**: (optional; used to distinguish instructor)

**Response** (200 OK):

```json
{
  "data": {
    "id": "course-uuid",
    "instructor_id": "user-uuid",
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "price_cents": 9999,
    "published": true,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:00:00Z",
    "modules": [...]
  },
  "meta": {...},
  "errors": []
}
```

**Behavior**:
- If unauthenticated or student: return only if `published == true`
- If authenticated instructor: return if owner or if `published == true`

**Errors**:
- `404 Not Found`: Course not found or not published (for non-instructors/non-owners)

---

### PUT `/api/v1/courses/{course_id}`

**Role**: Instructor-only (owner only)

**Authorization Header**: `Authorization: Bearer <access_token>`

**Request**:

```json
{
  "title": "Advanced Python",
  "description": "Deep dive into Python",
  "price_cents": 14999,
  "published": true
}
```

**Response** (200 OK):

```json
{
  "data": {
    "id": "course-uuid",
    "instructor_id": "user-uuid",
    "title": "Advanced Python",
    "description": "Deep dive into Python",
    "price_cents": 14999,
    "published": true,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:01:00Z",
    "modules": [...]
  },
  "meta": {...},
  "errors": []
}
```

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not the course owner
- `404 Not Found`: Course not found
- `400 Bad Request`: Invalid data

---

### DELETE `/api/v1/courses/{course_id}`

**Role**: Instructor-only (owner only)

**Authorization Header**: `Authorization: Bearer <access_token>`

**Business Rule**: "ActiveEnrollmentConstraint"
- If the course has active enrollments, deletion is rejected with 409 Conflict
- If no enrollments exist, course and its modules are deleted

**Response** (204 No Content) — if successful

**Error Response** (409 Conflict) — if active enrollments exist:

```json
{
  "data": null,
  "meta": {...},
  "errors": [
    {
      "code": "ACTIVE_ENROLLMENT_CONSTRAINT",
      "message": "Cannot delete course with active enrollments",
      "business_rule": "ActiveEnrollmentConstraint"
    }
  ]
}
```

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not the course owner
- `404 Not Found`: Course not found
- `409 Conflict`: Course has active enrollments

---

## Enrollments Endpoints

### POST `/api/v1/enrollments`

**Role**: Student-only

**Authorization Header**: `Authorization: Bearer <access_token>`

**Request**:

```json
{
  "course_id": "course-uuid"
}
```

**Response** (201 Created):

```json
{
  "data": {
    "id": "enrollment-uuid",
    "student_id": "user-uuid",
    "course_id": "course-uuid",
    "progress": 0,
    "completed_at": null,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:00:00Z"
  },
  "meta": {...},
  "errors": []
}
```

**Validation**:
- Course must be published
- Student cannot enroll twice in the same course (unique constraint)

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not a student
- `404 Not Found`: Course not found
- `409 Conflict`: Course is not published
- `409 Conflict`: Student already enrolled in course

---

### GET `/api/v1/enrollments`

**Role**: Student-only

**Authorization Header**: `Authorization: Bearer <access_token>`

**Query Parameters**: (optional)
- `skip`: int (default 0)
- `limit`: int (default 10)

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": "enrollment-uuid",
      "student_id": "user-uuid",
      "course_id": "course-uuid",
      "progress": 45,
      "completed_at": null,
      "created_at": "2026-06-27T12:00:00Z",
      "updated_at": "2026-06-27T12:30:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "skip": 0,
    "limit": 10,
    ...
  },
  "errors": []
}
```

**Behavior**: Only returns enrollments for the current student.

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not a student

---

### GET `/api/v1/enrollments/{enrollment_id}`

**Role**: Student-only (owner only)

**Authorization Header**: `Authorization: Bearer <access_token>`

**Response** (200 OK):

```json
{
  "data": {
    "id": "enrollment-uuid",
    "student_id": "user-uuid",
    "course_id": "course-uuid",
    "progress": 45,
    "completed_at": null,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:30:00Z"
  },
  "meta": {...},
  "errors": []
}
```

**Behavior**: Verifies enrollment belongs to current student before returning.

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Enrollment belongs to another student
- `404 Not Found`: Enrollment not found

---

### PUT `/api/v1/enrollments/{enrollment_id}`

**Role**: Student-only (owner only)

**Authorization Header**: `Authorization: Bearer <access_token>`

**Request**:

```json
{
  "progress": 75,
  "completed_at": null
}
```

**Response** (200 OK):

```json
{
  "data": {
    "id": "enrollment-uuid",
    "student_id": "user-uuid",
    "course_id": "course-uuid",
    "progress": 75,
    "completed_at": null,
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:45:00Z"
  },
  "meta": {...},
  "errors": []
}
```

**Auto-completion**:
- If `progress == 100` and `completed_at == null`, the system automatically sets `completed_at` to the current timestamp

**Example of auto-completion**:

```json
{
  "progress": 100,
  "completed_at": null
}
```

**Response**:

```json
{
  "data": {
    "id": "enrollment-uuid",
    "student_id": "user-uuid",
    "course_id": "course-uuid",
    "progress": 100,
    "completed_at": "2026-06-27T12:46:00Z",
    "created_at": "2026-06-27T12:00:00Z",
    "updated_at": "2026-06-27T12:46:00Z"
  },
  "meta": {...},
  "errors": []
}
```

**Validation**:
- Progress must be 0–100 (inclusive)

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Enrollment belongs to another student
- `404 Not Found`: Enrollment not found
- `400 Bad Request`: Progress outside 0–100 range

---

## HTTP Status Codes

| Code | Meaning | Common Scenarios |
|------|---------|-----------------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input, validation error, malformed JSON |
| 401 | Unauthorized | Missing/invalid token, token expired |
| 403 | Forbidden | Authenticated but lacks role/permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate enrollment, course with active enrollments, unpublished course enrollment attempt |
| 500 | Internal Server Error | Unexpected error |

---

## Authentication & Authorization Summary

| Endpoint | Auth Required | Role | Ownership Check |
|----------|---------------|------|-----------------|
| POST `/auth/register` | No | N/A | N/A |
| POST `/auth/login` | No | N/A | N/A |
| POST `/auth/refresh` | No | N/A | N/A |
| POST `/courses` | Yes | Instructor | N/A |
| GET `/courses` | Yes | Instructor | Own courses only |
| GET `/courses/{id}` | Optional | N/A | Published OR own (if instructor) |
| PUT `/courses/{id}` | Yes | Instructor | Must be owner |
| DELETE `/courses/{id}` | Yes | Instructor | Must be owner; reject if active enrollments |
| POST `/enrollments` | Yes | Student | N/A |
| GET `/enrollments` | Yes | Student | Own enrollments only |
| GET `/enrollments/{id}` | Yes | Student | Must be owner |
| PUT `/enrollments/{id}` | Yes | Student | Must be owner |

---

## Data Type Reference

### User

```typescript
{
  "id": "uuid",
  "email": "string (unique, valid email)",
  "display_name": "string",
  "role": "student" | "instructor",
  "created_at": "ISO 8601 timestamp",
  "hashed_password": "bcrypt hash (not returned in responses)"
}
```

### Course

```typescript
{
  "id": "uuid",
  "instructor_id": "uuid (FK → User)",
  "title": "string",
  "description": "string",
  "price_cents": "integer (>= 0)",
  "published": "boolean",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",
  "modules": "array of Module"
}
```

### Module

```typescript
{
  "id": "uuid",
  "course_id": "uuid (FK → Course)",
  "title": "string",
  "order": "integer (>= 1)",
  "created_at": "ISO 8601 timestamp"
}
```

### Enrollment

```typescript
{
  "id": "uuid",
  "student_id": "uuid (FK → User)",
  "course_id": "uuid (FK → Course)",
  "progress": "integer (0-100)",
  "completed_at": "ISO 8601 timestamp | null",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

---

## Error Code Reference

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| VALIDATION_ERROR | Input validation failed | 400 |
| UNAUTHORIZED | Missing or invalid token | 401 |
| FORBIDDEN | Authenticated but lacks permission | 403 |
| NOT_FOUND | Resource not found | 404 |
| CONFLICT | Conflict (duplicate, constraint violation) | 409 |
| ACTIVE_ENROLLMENT_CONSTRAINT | Course has active enrollments; cannot delete | 409 |
| INTERNAL_ERROR | Unexpected server error | 500 |

---

## Examples

### Full Workflow: Register → Create Course → Enroll → Progress

**1. Student registers**

```bash
POST /api/v1/auth/register
{
  "email": "alice@example.com",
  "password": "pass123",
  "display_name": "Alice"
}

Response: 201
{
  "data": {
    "user": {..., "role": "student"},
    "tokens": {"access_token": "ACCESS_TOKEN_1", "refresh_token": "REFRESH_1", ...}
  }
}
```

**2. Instructor creates course**

```bash
POST /api/v1/courses
Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN
{
  "title": "Python 101",
  "description": "Learn Python",
  "price_cents": 9999,
  "published": true,
  "modules": [
    {"title": "Module 1", "order": 1}
  ]
}

Response: 201
{
  "data": {"id": "COURSE_ID", ...}
}
```

**3. Student enrolls in published course**

```bash
POST /api/v1/enrollments
Authorization: Bearer ACCESS_TOKEN_1
{
  "course_id": "COURSE_ID"
}

Response: 201
{
  "data": {"id": "ENROLLMENT_ID", "progress": 0, ...}
}
```

**4. Student updates progress**

```bash
PUT /api/v1/enrollments/ENROLLMENT_ID
Authorization: Bearer ACCESS_TOKEN_1
{
  "progress": 100
}

Response: 200
{
  "data": {
    "id": "ENROLLMENT_ID",
    "progress": 100,
    "completed_at": "2026-06-27T12:46:00Z"
  }
}
```

**5. Instructor attempts to delete course with active enrollment**

```bash
DELETE /api/v1/courses/COURSE_ID
Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN

Response: 409 Conflict
{
  "data": null,
  "errors": [
    {
      "code": "ACTIVE_ENROLLMENT_CONSTRAINT",
      "message": "Cannot delete course with active enrollments",
      "business_rule": "ActiveEnrollmentConstraint"
    }
  ]
}
```
