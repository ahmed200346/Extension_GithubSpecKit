# CLI Contract: Enhanced Expense Tracker

This document defines the command-line interface for the Expense Tracker. The CLI is the primary entry point for users.

## Command Schema

All commands are executed as `expense-tracker <command> [args]`.

### 1. `add`
Creates a new expense record.
- **Usage**: `add <amount> <category> <date> ["description"]`
- **Arguments**:
    - `amount`: Float (strictly > 0)
    - `category`: String (Food | Transport | Bills | Utilities)
    - `date`: String (YYYY-MM-DD)
    - `description`: String (Optional, defaults to empty string)
- **Success**: Displays "Expense added successfully. ID: [id]"
- **Errors**:
    - Invalid amount: "Amount must be strictly positive."
    - Invalid category: "Invalid category. Allowed: Food, Transport, Bills, Utilities."
    - Invalid date: "Date must be in ISO format (YYYY-MM-DD)."

### 2. `list`
Retrieves and displays expenses.
- **Usage**: `list [--category <cat>] [--start <date>] [--end <date>]`
- **Flags**:
    - `--category`: Filter by one of the allowed categories.
    - `--start`: Start date for interval filter (YYYY-MM-DD).
    - `--end`: End date for interval filter (YYYY-MM-DD).
- **Output**: Tabular list containing `ID | Date | Category | Amount | Description` and a `Total: [sum]` at the bottom.
- **Empty Result**: Displays "No expenses found for the selected criteria. Total: 0.00"

### 3. `delete`
Removes an expense by its ID.
- **Usage**: `delete <id>`
- **Arguments**:
    - `id`: Integer (Primary Key)
- **Success**: Displays "Expense [id] deleted successfully."
- **Errors**:
    - Not found: "Expense not found. Please check the ID."

## Error Mapping Table

| Service Exception | CLI Output Message |
| :--- | :--- |
| `ValidationError` | [The specific validation message from the service] |
| `EntityNotFoundError` | "Expense not found. Please check the ID." |
| `DatabaseLockedError` | "The database is currently busy. Please try again in a few seconds." |
| `UnexpectedError` | "An internal error occurred. Please try again." |
