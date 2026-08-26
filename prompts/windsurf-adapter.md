# Windsurf Adapter - Universal Contract Injection

**Source:** `/prompts/universal-contract.md` (master protocol)
**Target:** `.windsurfrules` (project root)

## Ticket Agent Protocol (MANDATORY)

For every task, write the project-specific file `specs/{project_name}/.task_runtime/current-task.json`. Resolve the project name from `.task_runtime/config.json`, the parent folder of `tasks.md`, or the Git remote. Do not create `.task_runtime` at the workspace root.

Write the full task map with the active task `in_progress` before coding. After implementation and tests pass, write the full map with the task `done` only after the metrics and dashboard checks below. Use a temporary file followed by an atomic replace. Include every task ID from `tasks.md`.

### Metrics and Dashboard Verification (MANDATORY)

1. Ensure the backend runs with `ENABLE_AUDITOR=true`.
2. The `done` status triggers StatusWatcher and the Auditor.
3. If the watcher does not react, call `POST http://localhost:8000/api/v1/sync-current-task` once. Never edit the database directly.
4. Verify `GET http://localhost:8000/api/v1/ticket-agent/metrics?project_name={project_name}` returns `conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, and `traceability` for the completed task, plus project progress metrics.
5. Confirm the dashboard Metrics tab displays the score, verdict, and component metrics. If missing, keep the task `in_progress` and fix the auditor/backend issue.

Never invent metrics or write them into `current-task.json`.

### JSON Shape

```json
{
  "task_id": "T001",
  "file": "src/main.py",
  "status": "in_progress",
  "project_name": "my-project",
  "updated_at": "2026-08-12T10:30:00.000Z",
  "tasks": {"T001": "in_progress", "T002": "todo"}
}
```
