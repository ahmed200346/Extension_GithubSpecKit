# Feature Specification: Expense Tracker CLI

**Feature Branch**: `feature/001-expense-tracker-cli`

**Created**: 2026-07-24
**Updated**: 2026-07-25

**Status**: Draft

**Input**: User description: "Ajoutez plus detaill pour spec du projet 001-Expense-tracker"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a New Expense (Priority: P1)

As a user, I want to record a spending event by providing a description and an amount via the command line so that I can track my expenses.

**Why this priority**: This is the core functionality of the application. Without the ability to add expenses, the tracker serves no purpose.

**Independent Test**: Execute a command to add an expense (e.g., `add "Lunch" 15.50`) and verify that the data is persisted in the database and a confirmation is shown.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** I provide a valid description (non-empty string) and a positive numeric amount, **Then** the expense is saved to the database and a success message is displayed.
2. **Given** the application is running, **When** I provide a non-numeric amount, **Then** an error message is displayed explaining the input is invalid, and no record is created.
3. **Given** the application is running, **When** I provide an empty description, **Then** an error message is displayed and no record is created.

---

### User Story 2 - List All Expenses (Priority: P1)

As a user, I want to view a list of all my recorded expenses so that I can review what I have spent.

**Why this priority**: Adding data is useless if the user cannot retrieve and view it.

**Independent Test**: Add two expenses, then run the list command and verify that both expenses appear with their correct descriptions and amounts.

**Acceptance Scenarios**:

1. **Given** there are recorded expenses in the database, **When** I request the list of expenses, **Then** the system displays all expenses in a clear, tabular or list format including their unique ID, description, and amount.
2. **Given** the database is empty, **When** I request the list of expenses, **Then** the system informs me that no expenses have been recorded yet.

---

### User Story 3 - Calculate Total Spending (Priority: P2)

As a user, I want to see the total sum of all my expenses so that I can understand my overall expenditure.

**Why this priority**: Providing a summary is a key goal of any expense tracker, turning a list of items into a meaningful number.

**Independent Test**: Add expenses of 10.00 and 20.00, then run the total command and verify the result is 30.00.

**Acceptance Scenarios**:

1. **Given** there are recorded expenses, **When** I request the total spending, **Then** the system calculates the sum of all amounts and displays it clearly (e.g., "Total Spending: 30.00").
2. **Given** the database is empty, **When** I request the total spending, **Then** the system displays a total of 0.00.

---

### User Story 4 - Remove an Expense (Priority: P2)

As a user, I want to delete a specific expense by its ID so that I can correct mistakes in my entries.

**Why this priority**: Users will inevitably make mistakes; the ability to remove an entry is essential for data integrity.

**Independent Test**: Add an expense, note its ID, delete it using that ID, and verify it no longer appears in the list.

**Acceptance Scenarios**:

1. **Given** an existing expense with a known ID, **When** I provide that ID to the delete command, **Then** the expense is permanently removed from the database and a confirmation is shown.
2. **Given** a non-existent ID, **When** I attempt to delete it, **Then** the system displays an error message stating the expense was not found and no data is modified.

---

### Edge Cases

- **Negative Amounts**: The system must treat negative amounts as invalid inputs for adding expenses.
- **Zero Amount**: Expenses of 0.00 should be accepted as they may represent free items tracked for record-keeping.
- **Large Numbers**: Ensure the system handles large numeric values (e.g., millions) without precision loss using appropriate numeric types (e.g., Decimals).
- **Special Characters**: Descriptions containing quotes, emoji, or special characters should be handled without crashing the CLI.
- **Database Locking**: If the SQLite database is locked, the system should notify the user gracefully rather than crashing.
- **ID Collision/Wraparound**: Ensure the ID generation (AUTOINCREMENT) is robust.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to add a new expense by providing a description and an amount via the CLI.
- **FR-002**: System MUST allow users to retrieve a complete list of all stored expenses.
- **FR-003**: System MUST calculate and display the total sum of all stored expense amounts.
- **FR-004**: System MUST allow users to delete a specific expense record by its unique identifier (ID).
- **FR-005**: System MUST persist every successfully added or deleted expense in a SQLite database.
- **FR-006**: System MUST validate that the amount is a valid positive number (>= 0).
- **FR-007**: System MUST validate that the description is not empty.
- **FR-008**: System MUST provide immediate visual confirmation (success or error) to the user after any attempt to add, list, total, or delete an expense.

### Key Entities *(include if feature involves data)*

- **Expense**: Represents a single financial expenditure.
  - `id`: Unique identifier (Primary Key, Integer).
  - `description`: A brief text description of the expense (Text).
  - `amount`: The numeric cost of the expense (Decimal/Real).
  - `created_at`: Timestamp of when the expense was recorded (Timestamp/Text).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully add a valid expense in under 10 seconds from command execution to confirmation.
- **SC-002**: 100% of validated and "successfully added" expenses are retrievable from the SQLite database.
- **SC-003**: 100% of invalid inputs (e.g., text in amount field, empty description) result in a user-facing error message rather than a system crash.
- **SC-004**: Total spending calculations are mathematically accurate to 2 decimal places across all datasets.
- **SC-005**: Deleting a non-existent expense ID results in a clear error message 100% of the time.

## Assumptions

- **Environment**: The user has Python 3.10+ installed and is running the application in a standard terminal/shell.
- **Persistence**: The SQLite database file is automatically created in the project root or a designated data folder on first execution.
- **Scope**: This specification covers basic CRUD (Create, Read, Delete) and a total summary. Categories, date-based filtering, and updating existing expenses are out of scope for this version (reserved for "Enhanced" versions).
- **Data Types**: Amounts are handled as decimals to ensure financial precision.
- **Timezone**: All timestamps are recorded in the system's local timezone.
