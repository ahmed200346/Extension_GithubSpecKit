# Data Model: Enhanced Expense Tracker

## Entities

### Expense
Represents a single financial expenditure record.

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| `amount` | REAL | MUST be > 0 | Cost of the expense |
| `category` | TEXT | MUST be in {"Food", "Transport", "Bills", "Utilities"} | Spending category |
| `description` | TEXT | Optional | Brief detail about the expense |
| `date` | TEXT | MUST be ISO 8601 (YYYY-MM-DD) | Date the expense occurred |
| `created_at` | TEXT | Managed by DB (DEFAULT CURRENT_TIMESTAMP) | Internal record creation time |

## Validation Rules

- **Amount**: Strictly positive. Any value $\le 0$ must trigger a `ValidationError`.
- **Date**: Must strictly match the `YYYY-MM-DD` regex.
- **Category**: Must be one of the four allowed strings. Case-sensitive.
- **Description**: Allowed to be empty, but must be a string.

## State Transitions

The data model is purely CRUD; there are no complex state transitions (e.g., "Pending" $\rightarrow$ "Approved").

## Relationships

- **User to Expense**: 1:N (Implicitly, as this is a single-user local tool, all expenses belong to the current user).
