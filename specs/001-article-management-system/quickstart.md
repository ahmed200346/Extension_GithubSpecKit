# Quickstart Validation Guide: Article Management System

**Date**: 2026-08-11
**Feature**: Article Management System (001) & PostgreSQL (002)

## Validation Scenarios

### Scenario 1: End-to-End Article Lifecycle
**Goal**: Prove that an admin can create an article and a user can view it.
- **Setup**: 
  - Start PostgreSQL server.
  - Run schema initialization script.
  - Start Flask backend and serve frontend.
- **Steps**:
  1. Navigate to `/admin`.
  2. Create a new article: Title="Test Article", Price=10.00, Category="General".
  3. Navigate to the home page.
  4. Verify "Test Article" appears in the list.
  5. Click the article and verify the detailed view shows "Price: 10.00".
- **Expected Outcome**: Article is persisted in DB and visible in UI.

### Scenario 2: Dynamic Search & Filtering
**Goal**: Prove that searching and filtering work without page reloads.
- **Setup**: Ensure at least 5 articles across 2 different categories exist in the DB.
- **Steps**:
  1. Load the home page.
  2. Type a known keyword in the search bar.
  3. Select a specific category from the dropdown.
- **Expected Outcome**: The article grid updates instantly to show only matching items.

### Scenario 3: Data Integrity & Validation
**Goal**: Prove that invalid data is rejected.
- **Setup**: Standard running environment.
- **Steps**:
  1. Attempt to create an article with a negative price (-5.00).
  2. Attempt to create an article with an empty title.
- **Expected Outcome**: Both attempts are rejected by the API with a `400 Bad Request` and the UI displays a validation error.

## Technical References
- **Data Model**: See [data-model.md](data-model.md) for entity definitions.
- **API Contract**: See [contracts/api.md](contracts/api.md) for endpoint specifications.
