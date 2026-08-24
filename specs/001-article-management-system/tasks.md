---

description: "Task list for Article Management System implementation"
---

# Tasks: Article Management System

**Input**: Design documents from `/specs/001-article-management-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure (backend/ and frontend/ directories)
- [X] T002 Initialize Python environment and install Flask, SQLAlchemy, psycopg2
- [X] T003 [P] Initialize frontend project structure with basic HTML/CSS/JS files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story implementation

- [X] T004 Configure Flask app and PostgreSQL connection in `backend/src/app.py`
- [X] T005 [P] Setup database migration framework using Flask-Migrate in `backend/src/migrations/`
- [X] T006 [P] Implement base error handling and logging in `backend/src/api/errors.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 4 - Data Persistence via PostgreSQL (Priority: P1) 🚀 MVP

**Goal**: Ensure all article data is durably stored in PostgreSQL.

**Independent Test**: Create an article via API and verify its existence in the database using a SQL client.

### Implementation for User Story 4

- [X] T007 [P] [US4] Create Article model in `backend/src/models/article.py`
- [X] T008 [US4] Implement Article persistence service in `backend/src/services/article_service.py`
- [X] T009 [US4] Create API endpoint for creating articles in `backend/src/api/articles.py`

**Checkpoint**: Basic persistence working.

---

## Phase 4: User Story 5 - Relational Integrity (Priority: P2)

**Goal**: Maintain strict data integrity between Articles and Categories.

**Independent Test**: Attempt to link an article to a non-existent category ID and verify the DB rejects the operation.

### Implementation for User Story 5

- [ ] T010 [P] [US5] Create Category model in `backend/src/models/category.py`
- [ ] T011 [US5] Implement foreign key relationship between Article and Category in `backend/src/models/article.py`
- [ ] T012 [US5] Create API endpoint for managing categories in `backend/src/api/categories.py`

**Checkpoint**: Relational integrity enforced.

---

## Phase 5: User Story 2 - Article Administration (Priority: P1) 🚀 MVP

**Goal**: Allow administrators to perform full CRUD operations on the catalog.

**Independent Test**: Add, edit, and delete an article via the admin panel and verify changes in the public catalog.

### Implementation for User Story 2

- [ ] T013 [US2] Implement Update and Delete logic in `backend/src/services/article_service.py`
- [ ] T014 [US2] Create Admin API endpoints (PUT, DELETE) in `backend/src/api/articles.py`
- [ ] T015 [P] [US2] Create Admin Page UI in `frontend/src/pages/admin.html`
- [ ] T016 [US2] Implement Admin form handling and API integration in `frontend/src/services/admin_service.js`

**Checkpoint**: Admin panel fully functional.

---

## Phase 6: User Story 1 - Article Catalog Browsing (Priority: P1) 🚀 MVP

**Goal**: Enable potential buyers to browse the article catalog and view details.

**Independent Test**: Navigate to the home page and verify that a list of articles is displayed and details are accessible.

### Implementation for User Story 1

- [ ] T017 [P] [US1] Create public API endpoint for listing articles in `backend/src/api/articles.py`
- [ ] T018 [P] [US1] Create public API endpoint for article details in `backend/src/api/articles.py`
- [ ] T019 [P] [US1] Create Home Page (Article List) in `frontend/src/pages/index.html`
- [ ] T020 [P] [US1] Create Article Detail Page in `frontend/src/pages/detail.html`
- [ ] T021 [US1] Implement API client for catalog browsing in `frontend/src/services/catalog_service.js`

**Checkpoint**: Public catalog browsing working.

---

## Phase 7: User Story 3 - Dynamic Article Filtering (Priority: P2)

**Goal**: Provide real-time filtering by category and search by name without page reloads.

**Independent Test**: Use the search bar or category filter and verify the list updates instantly via AJAX.

### Implementation for User Story 3

- [ ] T022 [US3] Implement search and category filtering logic in `backend/src/services/article_service.py`
- [ ] T023 [US3] Update API endpoint to support query parameters for filtering in `backend/src/api/articles.py`
- [ ] T024 [US3] Implement dynamic JS filtering on Home Page in `frontend/src/pages/index.js`

**Checkpoint**: Dynamic filtering functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation

- [ ] T025 [P] Add input validation for prices and titles in `backend/src/api/articles.py`
- [ ] T026 [P] Implement responsive CSS for the article grid in `frontend/src/css/style.css`
- [ ] T027 [P] Add "No articles available" empty state to the home page in `frontend/src/pages/index.html`
- [ ] T028 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase
  - Recommended sequence: US4 $\rightarrow$ US5 $\rightarrow$ US2 $\rightarrow$ US1 $\rightarrow$ US3
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Foundational tasks T005, T006 can run in parallel
- Once Foundational is done, US2 and US1 can be worked on in parallel by different developers
- Frontend tasks T015, T019, T020 can be started in parallel once API contracts are agreed

---

## Implementation Strategy

### MVP First (User Stories 4, 2, 1)

1. Complete Setup + Foundational
2. Complete US4 (Persistence) $\rightarrow$ Core data layer ready
3. Complete US2 (Admin) $\rightarrow$ Catalog can be populated
4. Complete US1 (Browsing) $\rightarrow$ Value delivered to end user
5. **VALIDATE**: Run Quickstart Scenario 1

### Incremental Delivery

1. Foundational $\rightarrow$ Persistence (US4) $\rightarrow$ Admin (US2) $\rightarrow$ Browsing (US1) $\rightarrow$ Filtering (US3)
2. Each phase adds a fully testable increment of value.
