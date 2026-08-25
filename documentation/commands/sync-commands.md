# Sync Commands — CLI Reference for Ticket Agent

**Purpose:** Complete reference for all CLI commands to control, debug, and force synchronization of the Ticket Agent.

---

## Backend API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently no auth required (development). Add `Authorization: Bearer <token>` when enabled.

---

## Ticket Sync Commands

### Force Full Sync from current-task.json
```bash
# Triggers the same logic as the file watcher
curl -X POST http://localhost:8000/api/v1/sync-current-task
```

**Response:**
```json
{
  "file_path": "/project/.task_runtime/current-task.json",
  "file_exists": true,
  "task_id": "T004",
  "project_name": "001-cli-todo-manager",
  "target_status": "done",
  "ticket_found": true,
  "ticket_id": "uuid...",
  "action": "in_progress -> done",
  "bulk_sync": [
    {"task_id": "T001", "status": "done", "action": "no_change"},
    {"task_id": "T004", "status": "done", "action": "in_progress -> done"}
  ]
}
```

### Manual Ticket Status Update (Drag-and-Drop Equivalent)
```bash
# Move ticket to in_progress
curl -X PATCH http://localhost:8000/api/v1/tickets/<TICKET_UUID>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Move ticket to done
curl -X PATCH http://localhost:8000/api/v1/tickets/<TICKET_UUID>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Move ticket back to todo
curl -X PATCH http://localhost:8000/api/v1/tickets/<TICKET_UUID>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "todo"}'
```

### Ingest Tasks from tasks.md (Creates/Updates Tickets, NEVER Changes Status)
```bash
# With explicit tasks directory
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"tasks_dir": "/path/to/specs/001-cli-todo-manager"}'

# With project name (resolves from DB artifacts)
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"project_name": "001-cli-todo-manager"}'
```

### Commit-Based Status Refinement
```bash
# Infer status from commit message
curl -X POST http://localhost:8000/api/v1/commit-refine \
  -H "Content-Type: application/json" \
  -d '{"commit_message": "feat: finish T004 authentication", "project_name": "001-cli-todo-manager"}'
```

**Recognized Keywords:**
| Keywords | Status |
|----------|--------|
| finish, complete, done, close | done |
| start, begin, implement, wip | in_progress |

---

## Query Commands

### List All Tickets
```bash
# All tickets
curl "http://localhost:8000/api/v1/tickets"

# Filter by project
curl "http://localhost:8000/api/v1/tickets?project_name=001-cli-todo-manager"

# Filter by status
curl "http://localhost:8000/api/v1/tickets?status=in_progress"

# Combined
curl "http://localhost:8000/api/v1/tickets?project_name=001-cli-todo-manager&status=done"
```

### Get Single Ticket
```bash
curl "http://localhost:8000/api/v1/tickets/<TICKET_UUID>"
```

### Get Project Progress
```bash
curl "http://localhost:8000/api/v1/progress?project_name=001-cli-todo-manager"
```

**Response:**
```json
{
  "total": 10,
  "done": 4,
  "in_progress": 1,
  "todo": 5,
  "progress_pct": 40.0
}
```

### Get Ticket Events (Audit Trail)
```bash
curl "http://localhost:8000/api/v1/tickets/<TICKET_UUID>/events"
```

### Get Ticket Comments
```bash
curl "http://localhost:8000/api/v1/tickets/<TICKET_UUID>/comments"
```

### Add Comment to Ticket
```bash
curl -X POST http://localhost:8000/api/v1/tickets/<TICKET_UUID>/comments \
  -H "Content-Type: application/json" \
  -d '{"body": "Working on this now", "author_type": "human"}'
```

---

## Debug Commands

### Debug Current Task Sync (Detailed Diagnostics)
```bash
curl "http://localhost:8000/debug-current-task"
```

Returns full diagnostic including:
- File path resolution
- Project lookup details
- All ticket source paths in project
- Match strategy used
- Exact error if any

### Health Check
```bash
curl "http://localhost:8000/health"
```

### Pipeline Status (Document Generation)
```bash
curl "http://localhost:8000/api/v1/docs/status"
```

### Pipeline Progress
```bash
curl "http://localhost:8000/api/v1/docs/progress"
```

---

## Frontend Kanban Integration

The React frontend uses these endpoints:
- `fetchTickets` → `GET /tickets?project_name=...`
- `fetchProgress` → `GET /progress?project_name=...`
- `ingestTasks` → `POST /ingest`
- `updateTicketStatus` → `PATCH /tickets/{id}/status`

---

## Automation Scripts

### Watch & Auto-Sync (Development)
```bash
#!/bin/bash
# watch-sync.sh - Poll sync endpoint every 2s
while true; do
  curl -s -X POST http://localhost:8000/api/v1/sync-current-task > /dev/null
  sleep 2
done
```

### Pre-Commit Hook (Auto-update on commit)
```bash
#!/bin/bash
# .git/hooks/pre-commit
# Extract task IDs from commit message and refine
MSG=$(git log -1 --pretty=%B)
if echo "$MSG" | grep -qE 'T[0-9]{3,}'; then
  curl -s -X POST http://localhost:8000/api/v1/commit-refine \
    -H "Content-Type: application/json" \
    -d "{\"commit_message\": \"$MSG\", \"project_name\": \"$(basename $(pwd))\"}" > /dev/null
fi
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/ticket-sync.yml
name: Ticket Sync
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync tickets from commit
        run: |
          curl -X POST ${{ secrets.TICKET_API }}/api/v1/commit-refine \
            -H "Content-Type: application/json" \
            -d "{\"commit_message\": \"${{ github.event.head_commit.message }}\", \"project_name\": \"${{ github.event.repository.name }}\"}"
```

---

## Troubleshooting

### Sync Not Working?
1. Check `.task_runtime/current-task.json` exists and is valid JSON
2. Run `/debug-current-task` to see exact error
3. Verify `project_name` matches backend exactly
4. Check backend logs: `docker logs <backend_container>`

### Ticket Not Found?
1. Run `POST /ingest` first to create tickets from `tasks.md`
2. Check `source_file_path` format: `/full/path/to/tasks.md#T004`
3. Verify project exists in DB: `GET /tickets?project_name=...`

### Status Stuck?
1. Force sync: `POST /sync-current-task`
2. Manual update: `PATCH /tickets/{id}/status`
3. Check watcher running: `GET /health` → watcher should be active

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_PROJECT_PATH` | (auto) | Override project root for current-task.json |
| `DATABASE_URL` | postgresql://postgres:0000@localhost:5432/StageTal | PostgreSQL connection |
| `WATCH_DEBOUNCE_MS` | 500 | Debounce file watcher |

---

**Related:** `/prompts/universal-contract.md` (protocol), `/commands/lifecycle-guide.md` (status rules)