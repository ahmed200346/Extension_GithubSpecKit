# Universal Contract — Ticket Agent Protocol

**Version:** 1.0  
**Scope:** Mandatory for ALL AI assistants (Claude Code, GitHub Copilot, Codex, Cursor, etc.)  
**Location:** Project root `/prompts/universal-contract.md`

---

## 1. Purpose

This document defines the **Universal Contract** — the single, tool-agnostic protocol that every AI assistant MUST follow to report task progress to the Ticket Agent backend.

The backend watches `specs/{project_name}/.task_runtime/current-task.json`. Any AI that writes to this file correctly will automatically sync its Kanban board status in real-time, regardless of which IDE or CLI tool it runs in.

---

## 2. The Protocol (MANDATORY)

### 2.1 File Location
```
specs/{project_name}/.task_runtime/current-task.json
```
- Where `{project_name}` is the exact name of the project folder under `specs/` (e.g., `specs/001-course-management-system/.task_runtime/current-task.json`).
- The `.task_runtime/` directory MUST exist (create if missing).
- The file MUST be valid JSON, UTF-8 encoded.
- Write **atomically** (write to temp file, then rename) to avoid partial reads.

### 2.2 Write Timing (CRITICAL)
| Moment | Action |
|--------|--------|
| **BEFORE** starting any task | Write `status: "in_progress"` for that task |
| **AFTER** completing a task | Write `status: "done"` for that task |
| **ON EVERY STATUS CHANGE** | Write the **FULL `tasks` map** (all task IDs → current status) |

> **Why full map?** The backend may have been offline. The full map lets it recover the true state of every task from a single write.

### 2.3 JSON Schema

```json
{
  "task_id": "T004",
  "file": "src/routes.py",
  "status": "in_progress",
  "project_name": "my-project",
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

#### Field Definitions
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | YES | The task currently being worked on (e.g., `"T004"`). |
| `file` | string | YES | Primary file being edited (relative path). |
| `status` | enum | YES | `"in_progress"` or `"done"`. Never `"todo"` here. |
| `project_name` | string | YES | Exact project name as known to the backend (e.g., `"001-cli-todo-manager"`). |
| `updated_at` | ISO8601 | YES | UTC timestamp of this write. |
| `tasks` | object | YES | **Full map** of every task ID → status (`"todo"`, `"in_progress"`, `"done"`). |

#### Status Enum
- `"todo"` — Not started
- `"in_progress"` — Actively working
- `"done"` — Completed and verified

---

## 3. Task ID Format

- **Pattern:** `T` followed by 3+ digits (e.g., `T001`, `T012`, `T100`).
- **Source:** Extracted from `tasks.md` checkbox lines: `- [ ] T001 Implement auth`.
- **Consistency:** The same ID must appear in `tasks.md`, the `tasks` map, and `current-task.json`.

---

## 4. Project Name Resolution

The `project_name` must match the backend's `Project.name` column exactly.

**Resolution order (AI should use first match):**
1. Explicit config in `.task_runtime/config.json` (if exists): `{ "project_name": "..." }`
2. Parent directory name of the `tasks.md` file (e.g., `specs/001-cli-todo-manager/tasks.md` → `"001-cli-todo-manager"`)
3. Git remote origin repo name (fallback)

---

## 5. Backend Behavior (For Reference)

The backend watcher (`watcher.py`) detects file changes via `watchfiles` and:
1. Reads `current-task.json`
2. Finds matching tickets in PostgreSQL (3-strategy fallback)
3. Updates `Ticket.status` for:
   - The single `task_id`/`status` pair (legacy)
   - **Every entry in the `tasks` map** (recovery mechanism)
4. Creates `TicketEvent` audit trail (`author_type: "agent"`)

---

## 6. Compliance Checklist (AI Self-Verification)

Before/after each task, the AI MUST verify:
- [ ] `.task_runtime/` directory exists
- [ ] `current-task.json` written atomically
- [ ] `task_id` matches a ticket from `tasks.md`
- [ ] `project_name` matches backend project
- [ ] `tasks` map contains **ALL** task IDs from `tasks.md`
- [ ] `updated_at` is current UTC ISO8601
- [ ] JSON is valid (no trailing commas, proper escaping)

---

## 7. Non-Compliance Consequences

| Violation | Effect |
|-----------|--------|
| Missing `tasks` map | Board cannot recover state if backend was down |
| Wrong `project_name` | Ticket not found → status stuck in `todo` |
| Partial `tasks` map | Other tasks appear stale on Kanban |
| No write on `in_progress` | Board shows `todo` while work happens |
| Invalid JSON | Watcher logs error, no sync occurs |

---

## 8. Example Workflow

**User:** "Implement T004: Add user authentication"

**AI (before coding):**
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

**AI (after completing T004, before starting T005):**
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

## 9. Tool-Specific Adapters

This universal contract is adapted for each tool:

| Tool | Adapter File | Injection Target |
|------|--------------|------------------|
| Claude Code | `claude-adapter.md` | `CLAUDE.md` (project root) |
| GitHub Copilot | `copilot-adapter.md` | `.github/copilot-instructions.md` |
| Codex | `codex-adapter.md` | `AGENTS.md` or `.codex/instructions.md` |
| Cursor | `cursor-adapter.md` | `.cursorrules` or project settings |

**Each adapter MUST:**
- Include the full protocol above
- Add tool-specific syntax/examples
- Reference this master contract as the source of truth

---

**END OF UNIVERSAL CONTRACT**