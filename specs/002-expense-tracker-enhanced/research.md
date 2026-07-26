# Research: Enhanced Expense Tracker Technical Design

## 1. Repository Pattern with SQLite in Python

**Decision**: Use a Class-based Repository that manages a `sqlite3.Connection` object.

**Rationale**: 
- Separates SQL dialect from business logic.
- Allows for easy mocking of the database layer during service-level unit tests.
- Centralizes all query logic, making schema changes easier to manage.

**Alternatives considered**:
- *Direct SQL in Service*: Rejected; violates the Constitution's modular architecture principle.
- *SQLAlchemy ORM*: Rejected; violates Simplicity/YAGNI for a tool of this scale. Raw SQL provides better control over transactions and minimal overhead.

## 2. 3-Layer Architecture Communication

**Decision**: Use a "Bottom-Up Exception" strategy.
- **Repository**: Throws low-level exceptions (e.g., `sqlite3.OperationalError` $\rightarrow$ `DatabaseLockedError`).
- **Service**: Catches repository errors and throws business exceptions (e.g., `EntityNotFoundError`, `ValidationError`).
- **CLI**: Catches service exceptions and maps them to user-friendly strings.

**Rationale**: Prevents leaking implementation details (like SQL errors) to the user and keeps the service layer agnostic of the UI.

## 3. Atomic Transactions

**Decision**: Implement transactions using Python's `with connection:` context manager or explicit `begin/commit/rollback` blocks within the Repository.

**Rationale**: Ensures that if a multi-step write fails, the database is not left in a partial state. This directly satisfies the "Data Integrity" principle of the Constitution.

## 4. TDD Workflow with Pytest

**Decision**: 
- **Repository Tests**: Use an in-memory SQLite database (`:memory:`) for fast, isolated unit tests of CRUD operations.
- **Service Tests**: Mock the Repository layer to test business validation and orchestration logic without disk I/O.
- **Integration Tests**: Run the actual CLI commands against a temporary file-based SQLite database to verify the full stack.

**Rationale**: Provides the fastest feedback loop while ensuring high confidence in the final product.
