# Tasks: Expense Tracker

**Input**: Design documents from `specs/001-expense-tracker/`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create `src/server/types.ts` with `Expense` type
- [x] T002 Create `src/server/validators.ts` with `validateExpense` helper
- [x] T003 [P] Create UI components folder and stubs: `app/components/ExpenseForm.tsx`, `app/components/ExpenseList.tsx`, `app/components/Summary.tsx`
- [x] T004 Create `src/server/storage.ts` — localStorage adapter (load/save/delete/list)
- [x] T005 Update `app/page.tsx` to import and render the new components (wiring)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T006 [P] Implement `src/server/storage.ts` persistence functions: `loadExpenses()`, `saveExpenses()`, `addExpense()`, `deleteExpense()`
- [x] T007 [P] Add `src/server/categories.ts` with predefined categories: Food, Transport, Entertainment, Shopping, Utilities, Other
- [x] T008 [P] Add basic tests scaffold and validator unit test: `src/server/__tests__/validators.test.ts`
- [x] T009 [P] Ensure Tailwind/global styles are present and accessible in `app/globals.css`

---

## Phase 3: User Story 1 - Add an Expense (Priority: P1) 🎯 MVP

**Goal**: Allow users to add a new expense with amount, date, category, and description.

**Independent Test**: Fill the form in `app/components/ExpenseForm.tsx` and verify the new expense appears in `app/components/ExpenseList.tsx` and persists after reload.

- [x] T010 [US1] Implement `app/components/ExpenseForm.tsx` (client component) with fields: amount, date, category (select), description
- [x] T011 [US1] Use `src/server/validators.ts` in the form to validate input before save
- [x] T012 [US1] Implement add logic calling `src/server/storage.ts` (`addExpense`) and update UI state
- [x] T013 [US1] Add unit tests for form validation in `src/server/__tests__/validators.test.ts`

---

## Phase 4: User Story 2 - View Expenses (Priority: P1)

**Goal**: Display recent expenses sorted newest-first with empty state and "Load more" for older items.

**Independent Test**: Add multiple expenses and verify `app/components/ExpenseList.tsx` shows newest first, shows empty state when none, and loads 50 items with a "Load more" button.

 - [x] T014 [US2] Implement `app/components/ExpenseList.tsx` to render expenses, newest-first, limit initial 50 items
 - [x] T015 [US2] Implement `app/components/EmptyState.tsx` and use it when no expenses exist
 - [x] T016 [US2] Implement "Load more" button behavior to reveal older items in `ExpenseList.tsx`
 - [x] T017 [US2] Implement client-side hydration: load expenses from `src/server/storage.ts` on app start (in `app/page.tsx` or a client provider)

---

## Phase 5: User Story 3 - Delete an Expense (Priority: P1)

**Goal**: Allow users to delete an expense with confirmation and update totals/list.

**Independent Test**: Add an expense, delete it via `ExpenseList.tsx`, and verify it no longer appears after reload.

 - [x] T018 [US3] Add delete controls and confirmation UI in `app/components/ExpenseList.tsx`
 - [x] T019 [US3] Implement delete logic in `src/server/storage.ts` (`deleteExpense(id)`) and ensure UI updates
 - [x] T020 [US3] Add integration test that adds then deletes an expense and verifies absence: `src/server/__tests__/storage.integration.test.ts`

---

## Phase 6: User Story 4 - View Dashboard Totals (Priority: P2)

**Goal**: Show total amount spent and count of expenses in `app/components/Summary.tsx` and update in real time.

**Independent Test**: Add multiple expenses and verify totals in `Summary.tsx` equal sum and count, and update on add/delete.

 - [x] T021 [US4] Implement `app/components/Summary.tsx` to compute and render total and count
 - [x] T022 [US4] Wire real-time updates between `Summary.tsx` and the list (lift state to `app/page.tsx` or use React context)
 - [x] T023 [US4] Add unit tests validating totals calculation: `src/server/__tests__/totals.test.ts`

---

## Phase 7: Polish & Cross-Cutting Concerns

 - [x] T024 [P] Add ARIA labels and accessibility improvements to form and list components in `app/components/*`
 - [x] T025 [P] Update `specs/001-expense-tracker/quickstart.md` with run & verification steps
 - [x] T026 [P] Add documentation comments and inline TSDoc for `src/server/*`
 - [x] T027 [P] Performance: ensure initial render limits to 50 items in `app/components/ExpenseList.tsx` and lazy-load older items

---

## Dependencies & Execution Order

- Phase 1 must complete before Phase 2.
- Phase 2 (Foundational) must complete before user story implementation (Phases 3-6).
- User Stories 1-3 (P1) are MVP; US4 (P2) follows but can be implemented in parallel after foundation.

---

## Parallel Opportunities Identified

- Tasks marked `[P]` (T003, T006, T007, T008, T024-T027) can run in parallel.
- After foundational tasks (T006-T009) complete, user story phases can proceed in parallel by separate developers.

---

## Implementation Strategy

MVP First: implement Phase 1 → Phase 2 → Phase 3 (US1 Add Expense) → validate and demo.

---

