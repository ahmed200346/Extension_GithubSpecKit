# Feature Specification: Enhanced Expense Tracker

**Feature Branch**: `002-expense-tracker-enhanced`

**Created**: 2026-07-24
**Updated**: 2026-07-25

**Status**: Draft

**Input**: User description: "update feature spec for '002-expense-tracker-enhanced'
Ajoute un niveau de détail exhaustif en appliquant strictly tous les principes de la Constitution :
1. Nouveaux cas d'usage : Ajout, listing, suppression et filtrage des dépenses par catégorie (Food, Transport, Bills, Utilities) et par intervalle de dates (ISO YYYY-MM-DD).
2. Architecture technique détaillée : Séparation stricte à 3 niveaux : CLI -> Service Layer (Valideur métier) -> Repository Pattern (Gestion des transactions SQLite). Définition explicite du schéma SQLite (id, amount, category, description, date, created_at).
3. Règles de gestion et cas limites : Transactions atomiques obligatoires (commit / rollback automatique en cas d'erreur). Validation de saisie : Montants strictement positifs (> 0), format de date ISO (YYYY-MM-DD). Gestion des exceptions : Produit/Entity introuvable, SQLite locked, saisie CLI invalide.
4. Exigences de test (TDD) : Spécification des suites de tests Pytest obligatoires pour chaque méthode CRUD du Repository et du Service avant toute implémentation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a New Expense (Priority: P1)

As a user, I want to record a new expense by providing the amount, category, description, and date, so that I can keep track of my spending.

**Why this priority**: Core functionality. Without the ability to add expenses, the system provides no value.

**Independent Test**: Can be fully tested by adding a valid expense via the CLI and verifying its existence in the data store.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** the user adds an expense with a positive amount (e.g., 12.50), a valid category (Food), a description, and an ISO date (2026-07-24), **Then** the expense is successfully saved and a confirmation message is displayed.
2. **Given** the application is running, **When** the user attempts to add an expense with a negative amount (-5.00) or zero (0), **Then** the system rejects the input with a "Amount must be strictly positive" validation error message.
3. **Given** the application is running, **When** the user provides an invalid date format (e.g., "24-07-2026" or "July 24th"), **Then** the system rejects the input with a "Date must be in ISO format (YYYY-MM-DD)" error message.
4. **Given** the application is running, **When** the user provides a category not in the allowed list (e.g., "Entertainment"), **Then** the system rejects the input with a list of valid categories.

---

### User Story 2 - View and Filter Expenses (Priority: P1)

As a user, I want to list my expenses and filter them by category, date range, or a combination of both, so that I can analyze my spending patterns and get totals.

**Why this priority**: Critical for the "tracking" aspect of the expense tracker.

**Independent Test**: Can be fully tested by adding several expenses and then querying them using different filters and verifying the resulting list and total.

**Acceptance Scenarios**:

1. **Given** existing expenses in the system, **When** the user requests a list of all expenses, **Then** all recorded expenses are displayed in a structured format including ID, date, category, amount, and description, and a grand total of all amounts is displayed.
2. **Given** existing expenses in the system, **When** the user filters by a specific category (e.g., "Transport"), **Then** only expenses belonging to that category are displayed, and the total for that category is shown.
3. **Given** existing expenses in the system, **When** the user filters by a date interval (e.g., from 2026-07-01 to 2026-07-31), **Then** only expenses whose date falls within that inclusive range are displayed, and the total for that period is shown.
4. **Given** existing expenses in the system, **When** the user applies both a category filter (e.g., "Food") AND a date range filter, **Then** only expenses matching BOTH criteria are displayed, and the combined total is shown.
5. **Given** no expenses match the filter criteria, **When** the user applies the filter, **Then** the system displays a "No expenses found for the selected criteria" message and a total of 0.00.

---

### User Story 3 - Remove an Expense (Priority: P2)

As a user, I want to delete an expense by its ID, so that I can correct mistakes in my records.

**Why this priority**: Essential for data maintenance.

**Independent Test**: Can be fully tested by adding an expense, noting its ID, and then deleting it, verifying it no longer appears in the list.

**Acceptance Scenarios**:

1. **Given** an existing expense with a known ID, **When** the user deletes that ID, **Then** the expense is permanently removed from the database and a confirmation message is displayed.
2. **Given** a non-existent expense ID, **When** the user attempts to delete it, **Then** the system displays an "Expense not found" error message and no data is modified.

---

### Edge Cases

- **SQLite Locked**: If the database is locked by another process during a transaction, the system must catch the exception and notify the user that the database is currently unavailable.
- **Invalid Category**: Any input for category that is not exactly "Food", "Transport", "Bills", or "Utilities" must be rejected.
- **Leap Years/Invalid Calendar Dates**: Dates like "2026-02-30" must be rejected by the ISO date validator.
- **Non-Numeric Amount**: If the user enters non-numeric characters in the amount field, the CLI must handle the input error gracefully.
- **Empty Description**: The system should allow empty descriptions but must ensure all other mandatory fields are present.
- **Concurrent Access**: If two CLI instances attempt to write simultaneously, the Repository layer must handle the SQLite locking mechanism and the Service layer must provide a retry or error notification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create an expense record containing `amount`, `category`, `description`, and `date`.
- **FR-002**: System MUST validate that the `amount` is strictly positive (`amount > 0`).
- **FR-003**: System MUST validate that the `date` strictly follows the ISO 8601 format (`YYYY-MM-DD`).
- **FR-004**: System MUST restrict categories strictly to the set: {"Food", "Transport", "Bills", "Utilities"}.
- **FR-005**: System MUST allow users to retrieve a complete list of all stored expenses.
- **FR-006**: System MUST allow filtering expenses by a single category.
- **FR-007**: System MUST allow filtering expenses by a date range (inclusive start and end dates).
- **FR-008**: System MUST allow combined filtering by both category and date range.
- **FR-009**: System MUST calculate and display the total sum of expenses for any requested list or filtered view.
- **FR-010**: System MUST allow users to delete an expense record by its unique integer ID.
- **FR-011**: System MUST perform all database write operations (Create, Delete) within atomic transactions, ensuring a `commit` on success and an automatic `rollback` on any error.
- **FR-012**: System MUST implement a strict 3-level layered architecture:
    - **CLI Layer**: Handles user input/output, command parsing, and mapping Service exceptions to user-friendly messages.
    - **Service Layer**: Handles business logic, input validation, and orchestrates calls to the Repository. It MUST NOT contain any SQL or CLI-specific logic.
    - **Repository Layer**: Handles all raw SQLite database interactions, SQL query execution, and transaction management. It MUST NOT contain business logic.
- **FR-013**: System MUST handle the following error mappings:
    - `EntityNotFoundError` (Service) $\rightarrow$ "Expense not found. Please check the ID." (CLI)
    - `DatabaseLockedError` (Repository) $\rightarrow$ "The database is currently busy. Please try again in a few seconds." (CLI)
    - `ValidationError` (Service) $\rightarrow$ "[Specific validation error message]" (CLI)
- **FR-014**: System MUST adhere to TDD principles: exhaustive `pytest` suites MUST be defined for every CRUD method in the Repository and Service layers *prior* to implementation.

### Key Entities *(include if feature involves data)*

- **Expense**: A financial record of a cost incurred.
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `amount`: REAL (must be > 0)
  - `category`: TEXT (restricted to "Food", "Transport", "Bills", "Utilities")
  - `description`: TEXT
  - `date`: TEXT (ISO 8601 format: YYYY-MM-DD)
  - `created_at`: TEXT (Timestamp of record creation - managed by the database/repository)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of invalid inputs (negative/zero amounts, wrong date formats, invalid categories) are intercepted by the Service Layer validator before reaching the Repository.
- **SC-002**: 100% of data modifications are atomic; verified by ensuring no partial records exist after a simulated crash during a write operation.
- **SC-003**: Filtering by category and date range (including combined filters) returns 100% accurate results relative to the dataset.
- **SC-004**: Zero leakage of implementation details: No SQL queries in the CLI or Service layers; no CLI logic in the Repository or Service layers.
- **SC-005**: Total calculations for any view (all, filtered) are mathematically correct.
- **SC-006**: System responsiveness: Listing and filtering expenses in a dataset of up to 1,000 records takes less than 1 second.

## Assumptions

- The application is a standalone CLI tool.
- Local persistence is managed by a single SQLite database file.
- The predefined category list is static for this version.
- All dates are stored and handled in the user's local timezone.
- **Out of Scope**:
    - Updating/Editing existing expenses.
    - Multi-currency support.
    - User authentication and multiple user accounts.
    - Exporting data to other formats (CSV, Excel).
    - Graphical User Interface (GUI).

### Technical Constraints
- **Architecture**: CLI $\rightarrow$ Service Layer $\rightarrow$ Repository Pattern.
- **Database**: SQLite used for all persistence.
- **Data Integrity**: Mandatory use of transactions for all write operations.
- **Testing**: `pytest` is the mandatory framework for all unit and integration tests.
- **Language**: Python 3.10+.
