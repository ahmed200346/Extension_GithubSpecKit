# Ticket Templates — Standard Format for Tasks

**Purpose:** Defines the exact format for writing tasks in `tasks.md` so they parse correctly into tickets.

---

## Task Line Format (MANDATORY)

Every task in `tasks.md` MUST follow this pattern:

```markdown
- [ ] T001 Task title here
```

### Breakdown
| Component | Pattern | Example | Required |
|-----------|---------|---------|----------|
| Checkbox | `- [ ]` or `- [x]` or `- [~]` | `- [ ]` | YES |
| Task ID | `T` + 3+ digits | `T001`, `T012`, `T100` | YES |
| Title | Any text after ID | `Implement user auth` | YES |
| Description | Following lines (indented) | See below | NO |

---

## Complete Examples

### Minimal Task
```markdown
- [ ] T001 Setup project structure
```

### Task with Description
```markdown
- [ ] T002 Implement user authentication
  Add JWT-based auth with login/register endpoints.
  Include password hashing and token refresh.
```

### Task with Acceptance Criteria
```markdown
- [ ] T003 Create REST API for todos
  CRUD endpoints for todo items.
  
  Acceptance Criteria:
  - GET /todos returns paginated list
  - POST /todos creates new item
  - PUT /todos/{id} updates item
  - DELETE /todos/{id} removes item
  - All endpoints require auth
```

### Sub-tasks (Grouped)
```markdown
## Authentication Module

- [ ] T010 Setup auth database models
- [ ] T011 Implement password hashing
- [ ] T012 Create JWT token service
- [ ] T013 Build login/register endpoints
- [ ] T014 Add auth middleware
```

---

## Parsing Rules (What the Parser Extracts)

The parser (`ticket_ingestion.py::parse_task_lines`) extracts:

| Field | Source | Example |
|-------|--------|---------|
| `id` | Regex `^(T\d+)` | `T001` |
| `title` | Text after ID | `Setup project structure` |
| `description` | Subsequent indented lines | `Add JWT-based auth...` |
| `checkbox_state` | Checkbox char | `unchecked` / `checked` / `in_progress` |
| `line_number` | Line in file | `42` |

### Checkbox State Mapping
| Markdown | `checkbox_state` | Meaning |
|----------|------------------|---------|
| `- [ ]` | `unchecked` | Not started |
| `- [x]` / `- [X]` | `checked` | Visually done |
| `- [~]` / `- [/]` | `in_progress` | Visually in progress |

**Remember:** `checkbox_state` is **display only**. It NEVER drives Kanban status.

---

## Task ID Conventions

### Numbering
- **Sequential:** T001, T002, T003...
- **Grouped by feature:** T100-T199 (auth), T200-T299 (API), etc.
- **Gap-tolerant:** Can skip numbers (T001, T003, T005)

### Uniqueness
- **Per project:** IDs unique within one `tasks.md`
- **Across projects:** Can repeat (T001 in project A, T001 in project B)
- **Resolution:** Backend uses `source_file_path` (`.../tasks.md#T001`) for uniqueness

---

## Anti-Patterns (What NOT to Do)

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| `- [ ] Setup project` | Missing task ID | Add `T001` |
| `- [ ] T1 Setup` | ID too short (need 3+ digits) | Use `T001` |
| `T001 Setup` | Missing checkbox | Add `- [ ]` |
| `- [ ] T001` | Missing title | Add descriptive title |
| `- [x] T001 Done` | Checked but status not synced | Write `current-task.json` |

---

## Ingestion Behavior

When `POST /ingest` runs:

1. **Parses** `tasks.md` → list of task dicts
2. **Creates/Updates** tickets in DB:
   - New ticket → status `todo`
   - Existing ticket → updates title/desc/hash/checkbox, **status unchanged**
3. **Returns** list of tickets created/refreshed

### Idempotency
- Running ingest multiple times = safe
- Only creates missing tickets
- Updates metadata on existing tickets
- **Never** modifies status

---

## Template for New Projects

```markdown
# Project: <Project Name>
# Spec: <link to spec document>

## Phase 1: Foundation

- [ ] T001 Initialize repository with <tech stack>
- [ ] T002 Configure CI/CD pipeline
- [ ] T003 Setup database and ORM
- [ ] T004 Create base project structure

## Phase 2: Core Features

- [ ] T010 Implement user authentication
  - [ ] T011 User model & migrations
  - [ ] T012 Password hashing (bcrypt)
  - [ ] T013 JWT token generation
  - [ ] T014 Login / Register endpoints
  - [ ] T015 Auth middleware & protected routes

- [ ] T020 Implement <core feature>
  - [ ] T021 <subtask>
  - [ ] T022 <subtask>

## Phase 3: Polish

- [ ] T100 Write API documentation
- [ ] T101 Add integration tests
- [ ] T102 Performance optimization
- [ ] T103 Deploy to staging
```

---

## Validation Checklist

Before committing `tasks.md`:

- [ ] Every task line starts with `- [ ]` (or `[x]`/`[~]`)
- [ ] Every task has `T###` ID (3+ digits)
- [ ] Every task has a descriptive title
- [ ] IDs are unique within this file
- [ ] Descriptions are indented (2 spaces)
- [ ] No duplicate IDs
- [ ] File encoded as UTF-8

---

## Parser Test Cases

```python
# These should all parse correctly:
"- [ ] T001 Simple task"
"- [x] T002 Completed task"  
"- [~] T003 In progress task"
"- [/] T004 Also in progress"
"- [ ] T100 High number ID"
"  Description line for T001"
"  Another description line"

# These will FAIL or produce wrong results:
"T001 No checkbox"           # No checkbox → ignored
"- [ ] Task without ID"      # No T### → auto-generated ID
"- [ ] t001 lowercase"       # Case sensitive → treated as different
"- [ ] T01 Two digits"       # Too short → may not match
```

---

**Parsed by:** `backend/app/services/ticket_ingestion.py::parse_task_lines()`  
**Ingested by:** `POST /ingest` → `ingest_all_tasks()`  
**Synced by:** `current-task.json` watcher (status only)