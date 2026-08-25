# Mapping Rules — Spec Markdown to BDD Ticket

**Purpose:** Defines the exact logic for mapping specification documents (Markdown) to Kanban tickets in the database.

---

## Overview

The mapping happens in two distinct phases:

| Phase | Trigger | Function | Status Impact |
|-------|---------|----------|---------------|
| **Ingestion** | `POST /ingest` | Parse `tasks.md` → Create/Update `Ticket` rows | Creates as `todo`, never changes status |
| **Sync** | File watcher on `current-task.json` | Read AI progress → Update `Ticket.status` | Changes `todo`→`in_progress`→`done` |

---

## Ingestion Mapping (tasks.md → Ticket)

### Source: `tasks.md` Checkbox Lines
```markdown
- [ ] T001 Initialize repository
- [ ] T002 Configure database
- [x] T003 Setup CI/CD  ← checked but IGNORED for status
```

### Target: `Ticket` Model Fields
```python
class Ticket(Base):
    ticket_id: str           # "T001" (from markdown)
    title: str               # "Initialize repository" (text after ID)
    description: str         # Subsequent indented lines
    status: TicketStatus     # ALWAYS "todo" on ingest
    checkbox_state: str      # "unchecked"/"checked"/"in_progress" (display only)
    source_file_path: str    # "/full/path/tasks.md#T001" (unique key)
    source_file_hash: str    # SHA256 of tasks.md content
    line_number: int         # Line number in file
    project_id: UUID         # FK to Project
    artifact_id: UUID        # FK to Artifact (optional)
```

### Mapping Algorithm
```python
def parse_task_lines(content: str) -> List[Dict]:
    # 1. Find lines matching: - [xX~/] T### Title
    # 2. Extract: checkbox, task_id, title
    # 3. Collect subsequent indented lines as description
    # 4. Return list of dicts with: id, title, description, checkbox_state, line_number
```

### Unique Key: `source_file_path`
```
Format: "{absolute_path_to_tasks.md}#{task_id}"
Example: "/home/user/project/specs/001-cli-todo-manager/tasks.md#T001"
```
- Used for **upsert** (insert or update existing)
- Survives file moves if hash matches
- Project-scoped via `project_id`

### Hash-Based Change Detection
```python
file_hash = sha256(tasks.md content)
if existing_ticket.source_file_hash != file_hash:
    # Update title, description, checkbox_state, line_number
    # NEVER update status
```

---

## Sync Mapping (current-task.json → Ticket.status)

### Source: `current-task.json`
```json
{
  "task_id": "T004",
  "status": "in_progress",
  "tasks": {
    "T001": "done",
    "T002": "done", 
    "T003": "done",
    "T004": "in_progress",
    "T005": "todo"
  }
}
```

### Target: `Ticket.status` Update
```python
# For EACH entry in tasks map:
ticket = find_ticket(project, task_id)
if ticket:
    update_ticket_status(db, ticket.id, new_status, AuthorType.agent)
```

### Ticket Lookup Strategy (3-Strategy Fallback)
```python
def _find_ticket_for_task(db, project, project_name, task_id):
    like_pattern = f"%#{task_id}"
    
    # Strategy 1: Project-scoped exact match
    if project:
        ticket = db.query(Ticket).filter(
            Ticket.source_file_path.like(like_pattern),
            Ticket.project_id == project.id
        ).first()
        if ticket: return ticket
    
    # Strategy 2: Path-similarity (watched project root in path)
    watched_root = get_current_task_file_path().parent.parent
    for candidate in db.query(Ticket).filter(Ticket.source_file_path.like(like_pattern)):
        if str(watched_root) in candidate.source_file_path:
            return candidate
    
    # Strategy 3: Global fallback (first match anywhere)
    return db.query(Ticket).filter(Ticket.source_file_path.like(like_pattern)).first()
```

### Status Transition Logic
```python
def can_auto_transition(current: TicketStatus, target: TicketStatus) -> bool:
    order = {TicketStatus.todo: 0, TicketStatus.in_progress: 1, TicketStatus.done: 2}
    return order.get(target, 0) >= order.get(current, 0)

# In update_ticket_status():
if can_auto_transition(old, new):
    event_type = TicketEventType.status_change
else:
    event_type = TicketEventType.status_override  # Backward move
```

---

## Spec Document Mapping (Extended)

Beyond `tasks.md`, other spec files can generate tickets:

| Spec File | Artifact Type | Ticket Generation |
|-----------|---------------|-------------------|
| `requirements.md` | `requirements` | Future: extract user stories → tickets |
| `contracts.md` | `contracts` | Future: extract API endpoints → tickets |
| `data-model.md` | `data-model` | Future: extract entities → tickets |
| `tasks.md` | `task` | **Current: checkbox lines → tickets** |

### Future: Requirement Traceability
```
requirements.md (US-001) 
    │
    ├─► contracts.md (API endpoints)
    │       │
    │       └─► tasks.md (T001, T002, T003)
    │                   │
    │                   └─► Tickets (T001, T002, T003)
    │
    └─► data-model.md (entities)
```

### Mapping Rules for Future Enhancement

| Spec Element | Ticket Field | Rule |
|--------------|--------------|------|
| User Story `US-###` | `ticket_id` prefix | `US-001` → `T001-T005` |
| Acceptance Criteria | `description` | Bullet points → markdown |
| Priority Tag | `priority` field | `@high` → `priority: 1` |
| Estimate | `estimate_hours` | `@est(4h)` → `4` |
| Assignee | `assignee` | `@alice` → user lookup |

---

## Project Name Resolution

The `project_name` in `current-task.json` MUST match `Project.name` in DB.

### Resolution Order (AI should use first match)
1. `.task_runtime/config.json` → `"project_name"`
2. Parent directory of `tasks.md`: `specs/{project_name}/tasks.md`
3. Git remote origin repo name

### Backend Resolution (in `_sync_current_task_to_db`)
```python
project_name = data.get("project_name", "")
if project_name:
    project = db.query(Project).filter(Project.name == project_name).first()
else:
    # Search across all projects (fallback)
    project = None
```

---

## Artifact Linking

Tickets can link to `Artifact` (uploaded spec document):

```python
# During ingest_all_tasks():
artifact = db.query(Artifact).filter(
    Artifact.project_id == project.id,
    Artifact.source_path == str(task_file.resolve())
).first()

ticket = Ticket(
    project_id=project.id,
    artifact_id=artifact.id if artifact else None,  # Link if found
    ...
)
```

### Benefits
- Trace ticket → source document
- Enable "View Spec" in Kanban UI
- Support multi-version specs (v1, v2 tickets)

---

## Conflict Resolution

### Duplicate Task IDs Across Projects
**Problem:** Project A and B both have `T001`
**Solution:** `source_file_path` includes full path → unique per project

### Task ID Changed in tasks.md
**Problem:** `T001` renamed to `T005`
**Solution:** Hash mismatch → new ticket created, old ticket orphaned (manual cleanup)

### tasks.md Moved
**Problem:** `specs/old/tasks.md` → `specs/new/tasks.md`
**Solution:** Hash matches → ticket updated with new `source_file_path`

---

## Validation Rules

### Ingestion Validation
```python
# In parse_task_lines():
- Task ID must match ^T\d{3,}$  (T + 3+ digits)
- Title must not be empty after ID extraction
- Checkbox must be one of [ ], [x], [X], [~], [/]
```

### Sync Validation
```python
# In _sync_current_task_to_db():
- task_id must not be empty
- status must be in_progress or done (not todo)
- project_name should match existing project
- tasks map should contain all known task_ids
```

---

## Summary: Mapping Flow

```
┌─────────────────┐     POST /ingest      ┌──────────────────┐
│  tasks.md       │ ────────────────────► │  Ticket (DB)     │
│  - [ ] T001 ... │   parse_task_lines    │  status=todo     │
└─────────────────┘   ingest_all_tasks    │  checkbox_state  │
                                               │  source_file_path│
                                               └────────┬─────────┘
                                                        │
                              ┌─────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ current-task.json│
                    │ (AI writes)      │
                    └────────┬────────┘
                             │ watchfiles
                             ▼
                    ┌─────────────────┐     sync_service     ┌──────────────────┐
                    │  watcher.py     │ ──────────────────►  │  Ticket (DB)     │
                    │  detects change │   update_ticket_     │  status=IP/done  │
                    └─────────────────┘     status()         │  event logged    │
                                                          └──────────────────┘
```

---

**Implemented in:**
- `backend/app/services/ticket_ingestion.py` (ingestion)
- `backend/app/main.py` → `_find_ticket_for_task`, `_sync_current_task_to_db` (sync)
- `backend/app/agents/ticket_agent/` (new modular structure)