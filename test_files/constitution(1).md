# Learning Platform API Constitution

## Core Principles

### I. Technology Standardization
All implementation work must use the approved stack: Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy 2.0 with async execution, Alembic for migrations, and Pydantic v2 for validation. New features must align with this stack and avoid introducing alternative frameworks or synchronous database access patterns.

### II. Authentication and Authorization
Authentication must use JWT access tokens with a 15-minute expiry and refresh tokens with a 7-day expiry. The system supports exactly two roles: student and instructor. Instructors are authorized to create, edit, and delete courses. Students are authorized to enroll in courses and submit progress.

### III. API Contract and Response Shape
The API must be RESTful, return JSON, and be versioned under /api/v1/. All responses must use a consistent envelope of the form {"data": ..., "meta": ..., "errors": []}. API changes must preserve backward compatibility unless a new version is introduced.

### IV. Data Access and Persistence
All database access must be asynchronous. SQLAlchemy sessions must never be used synchronously, and all data access must be performed through the ORM. Raw SQL is prohibited. Schema changes must be handled through Alembic migrations.

### V. Quality and Testing
Testing must use pytest with httpx AsyncClient. Business logic coverage should target 80% or higher. Database tests must use a real PostgreSQL test instance and must not mock the database layer.

## Additional Constraints

- Transactional email delivery must use the Resend Python SDK.
- The Resend API key must be provided through the RESEND_API_KEY environment variable.
- A welcome email must be sent to students upon registration.
- Security-sensitive behavior must be validated through integration-style tests wherever practical.

## Development Workflow

- Features must be implemented and validated through tests before being considered complete.
- Any schema or contract change must include the corresponding migration and API documentation updates.
- Changes that affect authentication, authorization, or response envelopes require explicit review.

## Governance
This constitution supersedes ad hoc implementation choices. Any deviation from these standards requires documented justification and review before merge.

**Version**: 1.0.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
