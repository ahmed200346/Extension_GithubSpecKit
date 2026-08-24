# Research: Article Management System

**Date**: 2026-08-11
**Feature**: Article Management System (001) & PostgreSQL Integration (002)

## Resolved Technical Decisions

### 1. Backend Framework
- **Decision**: Flask
- **Rationale**: The user described this as a "mini projet". Flask is a micro-framework that provides the necessary routing and request handling without the overhead of Django, perfectly aligning with the project's "Simplicity & YAGNI" constitution principle.
- **Alternatives considered**: Django (Too heavy for a mini-project), FastAPI (Excellent, but Flask is more traditional for simple HTML/JS projects).

### 2. Data Access Layer
- **Decision**: SQLAlchemy (ORM)
- **Rationale**: Provides a clean abstraction over PostgreSQL, supports migrations (via Alembic), and ensures that the "MVC pattern" mentioned in the constitution is followed by separating the data model from the API logic.
- **Alternatives considered**: Raw SQL via `psycopg2` (Harder to maintain and prone to errors).

### 3. Dynamic Filtering Implementation
- **Decision**: API-driven filtering with JSON responses.
- **Rationale**: To achieve "updates without a full page reload" (spec FR-007), the frontend will send AJAX requests to a `/api/articles` endpoint with query parameters. The backend will perform the filtering in SQL for efficiency.
- **Alternatives considered**: Client-side filtering (Only viable for very small datasets; API-side is more scalable).

### 4. PostgreSQL Schema Pattern
- **Decision**: One-to-Many relationship between Categories and Articles.
- **Rationale**: An article belongs to one category, while a category can have many articles. This is the most efficient relational structure for this scope.
- **Schema**:
  - `categories` table: `id` (PK), `name` (Unique, Not Null).
  - `articles` table: `id` (PK), `title` (Not Null), `description`, `price` (Numeric, > 0), `category_id` (FK $\rightarrow$ categories.id, Not Null), `created_at` (Timestamp).

## Best Practices Applied
- **Input Validation**: Use `pydantic` or Flask-WTF for backend validation and HTML5/JS for frontend validation to meet the "Robust Validation" constitution principle.
- **Security**: Use parameterized queries (via SQLAlchemy) to prevent SQL Injection.
- **Performance**: Index the `title` and `category_id` columns in PostgreSQL to ensure searches return results in under 1 second.
