# Cursor Adapter - Universal Contract Injection

**Source:** `/prompts/universal-contract.md` (master protocol)
**Target:** `.cursorrules` (project root)

## Ticket Agent Protocol (MANDATORY)

Use `specs/{project_name}/.task_runtime/current-task.json` for every task. Resolve `project_name` from `.task_runtime/config.json`, the parent folder of `tasks.md`, or the Git remote. Never create a workspace-root `.task_runtime`.

At task start, atomically write the full task map with the active task `in_progress`. After implementation and tests pass, write the full map with the task `done` only after completing the verification below. The `tasks` object must contain every task ID from `tasks.md`.

### Metrics and Dashboard Verification (MANDATORY)

1. Ensure `ENABLE_AUDITOR=true` on the running backend.
2. The `done` write triggers StatusWatcher and the Auditor.
3. If needed, call `POST http://localhost:8000/api/v1/sync-current-task` once; never edit the database directly.
4. Verify `GET http://localhost:8000/api/v1/ticket-agent/metrics?project_name={project_name}` returns `conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, and `traceability` for the completed task.
5. Confirm the dashboard Metrics tab displays the score, verdict, and component metrics. If absent, keep the task `in_progress` and resolve the backend issue.

Never invent metrics or put metric values in `current-task.json`.

### JSON Shape

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
