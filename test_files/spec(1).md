# Feature Specification: CourseHub API

**Feature Branch**: `001-coursehub-api`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Build CourseHub, a REST API for an online learning platform. Instructors can create courses with a title, description, price (in cents), and a published flag. Each course has multiple modules in a fixed order. Students can register with email and password, then enrol in published courses. Enrolment tracks progress (0–100%) and completion date. Instructors should only be able to manage their own courses. Students should only be able to see their own enrolments. Both roles share the same user table but are distinguished by a role field. On successful student registration, send a welcome email via Resend containing the student's name and a link to browse published courses. The API must handle the case where an instructor tries to delete a course that has active enrolments — this should be rejected with a clear error message."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instructor manages courses (Priority: P1)

An instructor can create a course with ordered modules, publish it, and manage that course without affecting other instructors' content.

**Why this priority**: Course creation and ownership control are central to the platform's value and establish the core instructor workflow.

**Independent Test**: A single instructor can create a course, publish it, and update or delete it while the API enforces ownership boundaries.

**Acceptance Scenarios**:

1. **Given** an authenticated instructor, **When** they create a course with a title, description, price, published flag, and ordered modules, **Then** the course is created and associated with that instructor.
2. **Given** an instructor owns a course with active enrolments, **When** they attempt to delete it, **Then** the delete is rejected with a clear error message and the course remains available.

---

### User Story 2 - Student registers and enrols (Priority: P1)

A student can register, receive a welcome email, enroll in a published course, and view only their own enrolment records.

**Why this priority**: Registration and enrolment are the primary student journey and the basis for progress tracking.

**Independent Test**: A new student can sign up, receive a welcome email, and enroll in a published course successfully.

**Acceptance Scenarios**:

1. **Given** a new student submits a valid registration request, **When** the registration succeeds, **Then** an account is created as a student and a welcome email is sent through Resend.
2. **Given** a student is authenticated, **When** they enroll in a published course, **Then** an enrolment is created for that student and the course is marked as enrolled.

---

### User Story 3 - Progress is tracked and exposed safely (Priority: P2)

Students can update their own enrolment progress and completion status without accessing other students' enrolment data.

**Why this priority**: Progress tracking is essential for learner engagement and complements the core enrolment flow.

**Independent Test**: A student can update their enrolment progress from 0% to 100% and the completion date is recorded correctly.

**Acceptance Scenarios**:

1. **Given** a student has an active enrolment, **When** they submit a progress value between 0 and 100, **Then** the progress is stored and returned for that enrolment only.
2. **Given** a student attempts to access another student's enrolment, **When** the request is processed, **Then** the API denies access and returns an authorization error.

---

### Edge Cases

- Deleting a course with one or more active enrolments must fail with a clear validation error instead of silently succeeding.
- Progress values outside the 0–100% range must be rejected.
- Students must not be able to enroll in unpublished courses.
- Instructors must not be able to manage courses they do not own.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow instructors to create courses with a title, description, price in cents, a published flag, and multiple modules in a fixed order.
- **FR-002**: The system MUST associate each course with a single instructor and restrict course management actions to that instructor.
- **FR-003**: The system MUST reject course deletion when the course has active enrolments and return a clear error message.
- **FR-004**: The system MUST allow students to register with email and password and assign them the student role.
- **FR-005**: The system MUST send a welcome email through Resend after successful student registration, including the student's name and a link to browse published courses.
- **FR-006**: The system MUST allow students to enroll only in published courses.
- **FR-007**: The system MUST track enrolment progress as a value between 0 and 100 percent and record a completion date when progress reaches 100 percent.
- **FR-008**: The system MUST ensure students can view and update only their own enrolments.
- **FR-009**: The system MUST expose REST endpoints under /api/v1/ and return JSON responses using the envelope {"data": ..., "meta": ..., "errors": []}.
- **FR-010**: The system MUST use a shared user table with a role field to distinguish students and instructors.
- **FR-011**: The system MUST preserve the defined ordering of modules within each course.

### Key Entities *(include if feature involves data)*

- **User**: A shared account identity with role, email, password credential, and display name.
- **Course**: A learning offering owned by an instructor, with title, description, price in cents, published status, and ordered modules.
- **Module**: A child record of a course that represents a lesson or section in a fixed sequence.
- **Enrollment**: A student-course relationship that records progress and completion date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An instructor can publish a course and make it available to students through the API in a single workflow.
- **SC-002**: A student can register, enroll in a published course, and update progress without accessing another student's enrolment data.
- **SC-003**: At least 90% of the core course, enrollment, and authorization behaviors are covered by automated end-to-end tests.
- **SC-004**: The system returns a clear, consistent error when an instructor attempts to delete a course with active enrolments.

## Assumptions

- Each course has one instructor owner, while an instructor may own multiple courses.
- Published courses are the only courses available for student enrollment in the initial release.
- Student and instructor accounts are created through the platform's API and authenticated with the standard role-based access model.
- The Resend integration is available when the RESEND_API_KEY environment variable is configured.
