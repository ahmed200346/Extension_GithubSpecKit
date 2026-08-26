# GitHub Copilot Adapter - Universal Contract Injection

**Source:** `/prompts/universal-contract.md` (master protocol)
**Target:** `.github/copilot-instructions.md` (project root)

## Ticket Agent Protocol (MANDATORY)

For every task, use `specs/{project_name}/.task_runtime/current-task.json`. Resolve `project_name` from `.task_runtime/config.json`, then the parent folder of `tasks.md`, then the Git remote name. Never create `.task_runtime` at the workspace root.

Before coding, atomically write the full task map with the active task set to `in_progress`. After implementation and tests pass, set the task to `done` only after the metrics verification below. Every write must include every task ID from `tasks.md`.

### Metrics and Dashboard Verification (MANDATORY)

1. Ensure the backend Ticket Agent runs with `ENABLE_AUDITOR=true`.
2. Write the full `current-task.json` with the completed task set to `"done"`; this triggers StatusWatcher and the backend Auditor.
3. If the watcher does not react, call `POST http://localhost:8000/api/v1/sync-current-task` once. Never edit the database directly.
4. Verify `GET http://localhost:8000/api/v1/ticket-agent/metrics?project_name={project_name}`. The completed task must include `conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, and `traceability`; the project response must include `overall_progress_pct`, `tickets_with_audit`, and `avg_conformity_score`.
5. Confirm the dashboard ticket Metrics tab displays the score, verdict, and component metrics. If missing, keep the task `in_progress` and fix the auditor/backend issue.

Do not calculate or invent metric values in `current-task.json`.

### Required JSON Shape

```json
{
  "task_id": "T004",
  "file": "src/routes.py",
  "status": "in_progress",
  "project_name": "my-project",
  "updated_at": "2026-08-12T10:30:00.000Z",
  "tasks": {"T001": "done", "T004": "in_progress"}
}
```

Write to `current-task.json.tmp`, then atomically replace `current-task.json`. The JSON must be valid UTF-8.
