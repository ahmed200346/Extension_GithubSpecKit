# Claude Code Adapter — Universal Contract Injection

**Source:** `/prompts/universal-contract.md` (master protocol)  
**Target:** `CLAUDE.md` (project root)  
**Purpose:** Make Claude Code follow the Universal Contract automatically

---

## Injection Instructions

Copy the **entire content below** into your project's `CLAUDE.md` file at the root of the repository.

---

## CLAUDE.md Content (Copy Everything Below This Line)

---

# Ticket Agent Protocol (MANDATORY for Claude Code)

## Overview
You are working with a **Universal Ticket Agent** that syncs your task progress to a live Kanban board in real-time. This works by you writing to a JSON file that a backend watcher monitors.

**You MUST follow this protocol for EVERY task you work on.**

---

Claude Code writes the status file; the Ticket Agent backend calculates and persists conformity metrics. The dashboard reads those metrics from the backend.

## The Protocol

### File to Write
```
specs/{project_name}/.task_runtime/current-task.json
```
(Where `{project_name}` is the exact project folder name under `specs/`, e.g., `specs/001-course-management-system/.task_runtime/current-task.json`)

### When to Write
1. **BEFORE** starting any task → write `status: "in_progress"`
2. **AFTER** completing a task and verifying its backend audit metrics and dashboard display → write `status: "done"`
3. **ALWAYS** include the FULL `tasks` map (all task IDs → status)

### Metrics and Dashboard Verification (MANDATORY)

When a task is completed, Claude Code MUST:

1. Ensure the backend Ticket Agent is running with `ENABLE_AUDITOR=true`.
2. Write the full `current-task.json` with the task set to `"done"`; this transition triggers the StatusWatcher and Auditor.
3. If the watcher does not react, call `POST http://localhost:8000/api/v1/sync-current-task` once. Never edit the database directly.
4. Verify `GET http://localhost:8000/api/v1/ticket-agent/metrics?project_name={project_name}`. The completed task must have `conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, and `traceability`; the project response must include `overall_progress_pct`, `tickets_with_audit`, and `avg_conformity_score`.
5. Open the completed ticket's Metrics tab in the dashboard and confirm the score, verdict, and component metrics are displayed. If missing, leave the task `in_progress`, fix the backend/auditor cause, and repeat verification.

Do not invent metric values in `current-task.json`, and do not mark a task done based only on passing code tests while the audit response is missing.

### JSON Format (EXACT)
```json
{
  "task_id": "T004",
  "file": "src/routes.py",
  "status": "in_progress",
  "project_name": "001-cli-todo-manager",
  "updated_at": "2026-08-12T10:30:00.000Z",
  "tasks": {
    "T001": "done",
    "T002": "done",
    "T003": "done",
    "T004": "in_progress",
    "T005": "todo"
  }
}
```

### Field Rules
| Field | Required | Rules |
|-------|----------|-------|
| `task_id` | YES | Exact task ID from `tasks.md` (e.g., `T004`) |
| `file` | YES | Relative path of primary file you're editing |
| `status` | YES | `"in_progress"` (starting) or `"done"` (finishing) |
| `project_name` | YES | Exact project name from backend (e.g., `001-cli-todo-manager`) |
| `updated_at` | YES | Current UTC time in ISO8601: `new Date().toISOString()` |
| `tasks` | YES | **ALL** task IDs from `tasks.md` with current status |

### Status Values
- `"todo"` — Not started
- `"in_progress"` — Currently working
- `"done"` — Completed

---

## How to Find Your Project Name

Check in order:
1. `.task_runtime/config.json` → `"project_name"` field (if exists)
2. Parent folder of `tasks.md` (e.g., `specs/001-cli-todo-manager/tasks.md` → `"001-cli-todo-manager"`)
3. Git repo name: `git config --get remote.origin.url | sed 's/.*\/\([^/]*\)\.git/\1/'`

---

## Example Workflow

### User says: "Implement T004: Add user authentication"

**Step 1 — BEFORE coding (write to current-task.json):**
```json
{
  "task_id": "T004",
  "file": "src/auth/routes.py",
  "status": "in_progress",
  "project_name": "001-cli-todo-manager",
  "updated_at": "2026-08-12T10:30:00.000Z",
  "tasks": {
    "T001": "done",
    "T002": "done",
    "T003": "done",
    "T004": "in_progress",
    "T005": "todo"
  }
}
```

**Step 2 — Do the work** (write code, run tests, etc.)

**Step 3 — AFTER completing (write to current-task.json):**
```json
{
  "task_id": "T004",
  "file": "src/auth/routes.py",
  "status": "done",
  "project_name": "001-cli-todo-manager",
  "updated_at": "2026-08-12T10:45:00.000Z",
  "tasks": {
    "T001": "done",
    "T002": "done",
    "T003": "done",
    "T004": "done",
    "T005": "todo"
  }
}
```

---

## Implementation Helper (Python)

You can use this helper function in your code:

```python
import json
from datetime import datetime
from pathlib import Path

def write_task_status(task_id: str, file: str, status: str, project_name: str, all_tasks: dict):
    """Write current-task.json atomically."""
    runtime_dir = Path(f"specs/{project_name}/.task_runtime")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "task_id": task_id,
        "file": file,
        "status": status,
        "project_name": project_name,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "tasks": all_tasks
    }
    
    # Atomic write
    temp_file = runtime_dir / "current-task.json.tmp"
    temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp_file.replace(runtime_dir / "current-task.json")
```

---

## Compliance Checklist (Verify Every Time)

- [ ] `.task_runtime/` directory exists
- [ ] `current-task.json` written atomically (temp + rename)
- [ ] `task_id` matches a ticket from `tasks.md`
- [ ] `project_name` matches backend project exactly
- [ ] `tasks` map contains **ALL** task IDs from `tasks.md`
- [ ] `updated_at` is current UTC ISO8601
- [ ] JSON is valid (test with `jq . current-task.json`)

---

## Why This Matters

| If You Skip | Consequence |
|-------------|-------------|
| No write on start | Board shows `todo` while you're working |
| No write on done | Board stays `in_progress` forever |
| Partial `tasks` map | Other tasks look stale on Kanban |
| Wrong `project_name` | Ticket not found → no sync at all |
| Invalid JSON | Watcher errors, no sync |

---

## Manual Sync Trigger (If Needed)

If the watcher misses a change:
```bash
curl -X POST http://localhost:8000/api/v1/sync-current-task
```

---

**This protocol is defined in `/prompts/universal-contract.md` — this adapter is a formatted injection for Claude Code.**

---

## End of Injection