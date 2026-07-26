# Quickstart Validation Guide: Enhanced Expense Tracker

This guide provides a set of runnable scenarios to verify the end-to-end functionality of the enhanced expense tracker.

## Prerequisites
- Python 3.10+ installed.
- `pytest` installed for running automated checks.

## Setup
The system automatically initializes a local SQLite database on the first command execution.

## Validation Scenarios

### Scenario 1: Basic Create & Read (Happy Path)
**Goal**: Verify that a valid expense can be added and then retrieved.
1. **Command**: `python main.py add 15.50 Food 2026-07-25 "Lunch at Bistro"`
2. **Expected**: "Expense added successfully. ID: 1"
3. **Command**: `python main.py list`
4. **Expected**: A table showing the record with ID 1, amount 15.50, and category Food.

### Scenario 2: Input Validation (Error Path)
**Goal**: Verify that the Service layer correctly rejects invalid data.
1. **Command**: `python main.py add -5.00 Food 2026-07-25 "Invalid amount"`
2. **Expected**: "Amount must be strictly positive."
3. **Command**: `python main.py add 10.00 Magic 2026-07-25 "Invalid category"`
4. **Expected**: "Invalid category. Allowed: Food, Transport, Bills, Utilities."
5. **Command**: `python main.py add 10.00 Food 25-07-2026 "Invalid date"`
6. **Expected**: "Date must be in ISO format (YYYY-MM-DD)."

### Scenario 3: Advanced Filtering & Totals
**Goal**: Verify category and date-range filtering logic.
1. **Setup**: Add 3 expenses:
    - 10.00 Food (2026-07-01)
    - 20.00 Food (2026-07-05)
    - 50.00 Bills (2026-07-10)
2. **Command**: `python main.py list --category Food`
3. **Expected**: Only the 2 Food expenses are shown. Total: 30.00.
4. **Command**: `python main.py list --start 2026-07-01 --end 2026-07-06`
5. **Expected**: Only expenses on July 1st and 5th are shown. Total: 30.00.
6. **Command**: `python main.py list --category Food --start 2026-07-02 --end 2026-07-06`
7. **Expected**: Only the Food expense from July 5th is shown. Total: 20.00.

### Scenario 4: Deletion & Data Integrity
**Goal**: Verify that expenses are permanently removed and IDs are handled correctly.
1. **Command**: `python main.py delete 1` (Assuming ID 1 exists)
2. **Expected**: "Expense 1 deleted successfully."
3. **Command**: `python main.py list`
4. **Expected**: Expense 1 no longer appears in the list.
5. **Command**: `python main.py delete 999`
6. **Expected**: "Expense not found. Please check the ID."
