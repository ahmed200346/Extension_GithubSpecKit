# Windsurf Adapter — Universal Contract Injection

**Source:** `/prompts/universal-contract.md` (master protocol)  
**Target:** `.windsurfrules` (project root)  
**Purpose:** Make Windsurf (Codeium) follow the Universal Contract automatically

---

## Injection Instructions

Copy the **entire content below** into your project's `.windsurfrules` file at the root of the repository.

---

## .windsurfrules Content (Copy Everything Below This Line)

---

# Ticket Agent Protocol (MANDATORY for Windsurf AI)

You are integrated with a **Universal Ticket Agent** system. To ensure the project Kanban board remains synchronized in real-time, you MUST report your progress via the specified JSON interface.

**This protocol is MANDATORY for every single task assigned to you.**

---

## 🛠 Protocol Specifications

### 1. State File
The single source of truth for your current activity is:
`specs/{project_name}/.task_runtime/current-task.json` (where `{project_name}` is the exact project folder name under `specs/`)
**NEVER** create `.task_runtime/` at the project root — only under `specs/{project}/`.

> [!IMPORTANT] Until `tasks.md` exists, keep `current-task.json` empty (`tasks:{}`) — do NOT treat `spec.md`/`plan.md` as tasks.

### 2. Mandatory Update Cycle
| Event | Required Action | Status Value |
|-------|-------------------|---------------|
| **Task Initiation** | Write to JSON immediately | `"in_progress"` |
| **Task Completion** | Write to JSON immediately | `"done"` |
| **State Sync** | Always provide the **FULL `tasks` map** | All IDs $\rightarrow$ status |

### 3. JSON Data Structure
```json
{
  "task_id": "T001",
  "file": "src/main.py",
  "status": "in_progress",
  "project_name": "my-project",
  "updated_at": "2026-08-12T10:30:00.000Z",
  "tasks": {
    "T001": "in_progress",
    "T002": "todo"
  }
}
```

### 4. Field Rules
- `task_id`: Exactly as defined in `tasks.md`.
- `file`: Relative path of the primary file you are editing.
- `status`: Either `"in_progress"` (when starting) or `"done"` (when finishing).
- `project_name`: Must match the backend project name exactly.
- `updated_at`: Current timestamp in ISO8601 UTC.
- `tasks`: A complete mapping of ALL task IDs from `tasks.md` to their current state (`"todo"`, `"in_progress"`, `"done"`).

---

## 🔄 Operational Workflow

**Example:** "T005 Implement User Logout"

- **Step A (Start)** $\rightarrow$ Write `current-task.json` $\rightarrow$ `status: "in_progress"`.
- **Step B (Work)** $\rightarrow$ Implement the logic, run tests, verify.
- **Step C (Finish)** $\rightarrow$ Write `current-task.json` $\rightarrow$ `status: "done"`.

---

## ✅ Self-Verification Checklist
You MUST verify these points before submitting your work:
- [ ] Is the `.task_runtime/` folder present?
- [ ] Was `current-task.json` updated at the start AND end of the task?
- [ ] Does the `tasks` map contain every ID from `tasks.md`?
- [ ] Is the `project_name` correct?
- [ ] Is the JSON format perfectly valid?

---

**This protocol is an implementation of the `/prompts/universal-contract.md`. Adherence is required for Kanban synchronization.**

---

## End of Injection