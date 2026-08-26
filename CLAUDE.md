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

### Claude Code Execution Rule (MANDATORY)

When `/speckit-implement` is invoked, this protocol is part of the command execution and MUST be performed by Claude Code itself. Do not delegate status-file writes to the backend, frontend, extension, or Ticket Agent. The Ticket Agent only observes `current-task.json`; it never infers implementation progress from the chat, `tasks.md`, Git changes, or logs. Claude Code writes the status; the Ticket Agent backend calculates and persists conformity metrics.

After reading `tasks.md` and before editing any source file, determine the requested task IDs from the command arguments. For `/speckit-implement Implement T001,T002 and T003`, the requested IDs are `T001`, `T002`, and `T003`. Validate that every requested ID exists in `tasks.md`, then immediately write `specs/{project_name}/.task_runtime/current-task.json` with:

- `task_id` set to the first task currently being implemented;
- `file` set to the primary file for that task, or the first primary file when several files are involved;
- `status` set to `in_progress`;
- `project_name` resolved from `.task_runtime/config.json` first, then the parent directory of `tasks.md`;
- `tasks` containing every task ID in `tasks.md`, with requested tasks marked `in_progress` and all other tasks preserving their current status (use `todo` when no prior status exists).

This first status write MUST happen before any implementation edit, test edit, formatting change, dependency installation, or hook execution. For multiple requested tasks, mark all requested tasks `in_progress` in the same initial write. Never write `status: "todo"` in the top-level object, and never leave `task_id` empty.

After each requested task is implemented and its validation succeeds, atomically rewrite the same file with that task marked `done`. This `done` transition is mandatory: the backend StatusWatcher uses it to trigger the Auditor, which calculates the conformity score plus requirement coverage, code quality, architecture, and traceability metrics. Keep the full `tasks` map on every write. Before starting the next task, set its `task_id`, `file`, and top-level `status` to `in_progress`; after the final requested task passes validation and its metrics have been verified, set the top-level status to `done` and mark all completed requested tasks `done`.

Use a temporary file in the same `.task_runtime` directory followed by an atomic replace. On Windows, use a short Python or PowerShell script if needed. Verify that the final file is valid JSON and that its path is project-specific. If a status write fails, stop implementation and report the write error; do not continue while the Kanban state is stale.

### Metrics and Dashboard Verification (MANDATORY)

When a requested task is completed, Claude Code MUST complete this sequence before declaring it done:

1. Ensure the backend Ticket Agent is running with the Auditor enabled (`ENABLE_AUDITOR=true`). Do not calculate conformity scores in `CLAUDE.md` or invent metric values in `current-task.json`; the backend is the source of truth.
2. Write the full `current-task.json` with the completed task set to `"done"`. The write must include the complete `tasks` map and the correct `project_name` so StatusWatcher can find the ticket.
3. Allow the watcher to synchronize the status and trigger the audit. If the watcher does not react, call `POST http://localhost:8000/api/v1/sync-current-task` once; do not bypass the watcher by editing the database directly.
4. Verify the calculated result with `GET http://localhost:8000/api/v1/ticket-agent/metrics?project_name={project_name}`. The response must contain `overall_progress_pct`, `tickets_with_audit`, `avg_conformity_score`, and the completed task in `tickets_metrics` with `conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, and `traceability`.
5. Verify the ticket detail in the dashboard by opening the completed ticket's Metrics tab. It must display the conformity score, verdict, and available component scores. If metrics are missing, keep the task `in_progress`, inspect backend logs and the Auditor configuration, fix the cause, and repeat verification.

The dashboard reads metrics from the backend; Claude Code must never mark a task complete based only on a successful code test while the audit response is still missing.

---

## The Protocol

### File to Write
```
specs/{project_name}/.task_runtime/current-task.json
```
(Where `{project_name}` is the exact project folder name under `specs/`, e.g., `specs/001-course-management-system/.task_runtime/current-task.json`)
**NEVER** create `.task_runtime/` at the project root — only under `specs/{project}/`.

> [!IMPORTANT]
> **Until `tasks.md` exists:** After `/speckit-specify` and `/speckit-plan`, keep `current-task.json` **empty** (`tasks:{}`) — do NOT treat `spec.md`/`plan.md` as tasks. Only after `/speckit-tasks` generates `tasks.md` should you write the FULL `tasks` map with every `T00N` initially `todo`.

### When to Write — TIMING CRITICAL
1. **IMMEDIATELY BEFORE you start coding (first action)** → write `status: "in_progress"` with `tasks: { ..., "T00N": "in_progress", ... }`
2. **AFTER** completing a task and verifying its backend audit metrics and dashboard display → write `status: "done"`
3. **ALWAYS** include the FULL `tasks` map (all task IDs → status)

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
- [ ] Auditor is enabled in the backend (`ENABLE_AUDITOR=true`)
- [ ] `GET /ticket-agent/metrics?project_name=...` returns metrics for the completed task
- [ ] Dashboard Metrics tab displays the conformity score and component metrics

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