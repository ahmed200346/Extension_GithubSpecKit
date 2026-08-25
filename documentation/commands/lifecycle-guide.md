# Lifecycle Guide — Ticket Status Transitions

**Purpose:** Defines the exact rules for when and how ticket statuses change. This is the single source of truth for both AI agents and human operators.

---

## Status Enum

```python
class TicketStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
```

---

## Transition Rules (STRICT)

### Allowed Transitions
```
todo ──────────────► in_progress ──────────────► done
  ▲                      │                         │
  │                      │                         │
  └──────────────────────┴─────────────────────────┘
        (override only - human or auditor)
```

| From → To | Allowed | Trigger | Author Type |
|-----------|---------|---------|-------------|
| `todo` → `in_progress` | ✅ YES | AI writes `current-task.json` with `in_progress` | `agent` |
| `in_progress` → `done` | ✅ YES | AI writes `current-task.json` with `done` | `agent` |
| `done` → `in_progress` | ⚠️ OVERRIDE | Human drag-back / auditor rejects | `human` / `agent` |
| `in_progress` → `todo` | ⚠️ OVERRIDE | Human reset / task cancelled | `human` |
| `done` → `todo` | ⚠️ OVERRIDE | Human reset / major rework | `human` |
| Any → Same | ✅ NO-OP | Idempotent write | - |

---

## Transition Triggers

### 1. AI-Driven (Automatic via current-task.json)
**File:** `.task_runtime/current-task.json`  
**Watcher:** `watcher.py` → `sync_service.py`

| AI Action | JSON Write | Result |
|-----------|------------|--------|
| Start task | `"status": "in_progress"` | `todo` → `in_progress` |
| Complete task | `"status": "done"` | `in_progress` → `done` |
| Bulk update | Full `tasks` map | All transitions applied |

**Rules:**
- AI MUST write full `tasks` map on EVERY change
- Backend applies ALL entries in map (recovery mechanism)
- Only `in_progress` and `done` written by AI; `todo` managed by ingestion

### 2. Human-Driven (Manual via API/UI)
**Endpoints:** `PATCH /tickets/{id}/status`, Kanban drag-drop

| Action | API Call | Result |
|--------|----------|--------|
| Start work | `{"status": "in_progress"}` | `todo` → `in_progress` |
| Mark done | `{"status": "done"}` | `in_progress` → `done` |
| Reopen | `{"status": "in_progress"}` | `done` → `in_progress` (OVERRIDE) |
| Reset | `{"status": "todo"}` | Any → `todo` (OVERRIDE) |

**Rules:**
- Backward transitions logged as `status_override` events
- Requires human confirmation in UI
- Auditor can trigger override if conformity < threshold

### 3. Ingestion (Creates Tickets, NEVER Changes Status)
**Endpoint:** `POST /ingest`

| Scenario | Status Set |
|----------|------------|
| New ticket | `todo` (always) |
| Existing ticket | **Unchanged** (only title/desc/hash updated) |
| Checkbox `[x]` in tasks.md | **Ignored** for status (display only) |

**Critical Rule:** Ingestion is **read-only** for status. Only the watcher/API can change status.

### 4. Commit-Based (Inferred from Git)
**Endpoint:** `POST /commit-refine`

| Commit Keywords | Inferred Status |
|-----------------|-----------------|
| finish, complete, done, close, resolve | `done` |
| start, begin, implement, wip, working on | `in_progress` |

**Rules:**
- Only applies if ticket exists in project
- Creates `status_change` event (not override)
- Supplementary to (not replacement for) current-task.json

---

## Event Types (Audit Trail)

```python
class TicketEventType(str, Enum):
    status_change = "status_change"      # Normal forward transition
    status_override = "status_override"  # Backward/reset transition
    comment_added = "comment_added"
```

### Event Metadata
```json
{
  "from": "todo",
  "to": "in_progress",
  "source": "api_patch"  // or "file_watcher", "commit_refine", "initial_ingestion"
}
```

---

## Status Display vs. Status Logic

### Checkbox State (Display Only)
| Markdown | `checkbox_state` | Drives Status? |
|----------|------------------|----------------|
| `- [ ]` | `unchecked` | ❌ NO |
| `- [~]` / `- [/]` | `in_progress` | ❌ NO |
| `- [x]` | `checked` | ❌ NO |

**The checkbox in `tasks.md` is purely for human readability. It NEVER drives the Kanban status.**

### Kanban Column Mapping
| Board Column | Ticket Status | Source |
|--------------|---------------|--------|
| To Do | `todo` | Ingestion / Reset |
| In Progress | `in_progress` | AI write / Human / Commit |
| Done | `done` | AI write / Human / Commit |

---

## Edge Cases & Resolutions

### Case 1: Backend Offline During Work
**Scenario:** AI works on T004 while backend down. Writes `in_progress` then `done`.
**Resolution:** When backend restarts, watcher reads `current-task.json` with full `tasks` map → applies all statuses correctly.

### Case 2: AI Forgets to Write `in_progress`
**Scenario:** AI writes only `done` for T004.
**Resolution:** Watcher applies `done` directly. Ticket jumps `todo` → `done`. Logged as `status_change`.

### Case 3: Conflicting Writes
**Scenario:** AI writes `in_progress`, human drags to `done` in UI.
**Resolution:** Last write wins. Both create events. Watcher re-syncs on next file change.

### Case 4: Duplicate Task IDs Across Projects
**Scenario:** Two projects have `T001`.
**Resolution:** 3-strategy ticket lookup:
1. Project-scoped match (project_id + source_file_path)
2. Path-similarity (watched project path in source_file_path)
3. Global fallback (first match)

### Case 5: Task Deleted from tasks.md
**Scenario:** T005 removed from tasks.md, but ticket exists in DB.
**Resolution:** Ticket remains in DB with last known status. Ingestion won't delete. Manual cleanup needed.

---

## Conformity Gates (Future Enhancement)

When Auditor is enabled:

| Conformity Score | Auto-Action |
|------------------|-------------|
| ≥ 90 | Allow `done` |
| 75-89 | Allow `done` with warning |
| 60-74 | Block `done`, keep `in_progress` |
| < 60 | Revert to `todo`, require rework |

**Implementation:** `auditor.py` runs on `in_progress` → `done` transition. If score < threshold, creates `status_override` event back to `in_progress`.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    STATUS TRANSITIONS                        │
├──────────────┬──────────────┬───────────────────────────────┤
│ TRIGGER      │ TRANSITION   │ EVENT TYPE                    │
├──────────────┼──────────────┼───────────────────────────────┤
│ AI start     │ todo → IP    │ status_change (agent)         │
│ AI complete  │ IP → done    │ status_change (agent)         │
│ Human drag   │ any → any    │ status_change or _override    │
│ Commit msg   │ todo/IP→done │ status_change (agent)         │
│ Ingestion    │ (create)     │ status_change (agent, todo)   │
│ Auditor fail │ done → IP    │ status_override (agent)       │
└──────────────┴──────────────┴───────────────────────────────┘

IP = in_progress
```

---

**Enforced by:** `backend/app/services/ticket_ingestion.py` (`update_ticket_status`, `can_auto_transition`)  
**Monitored by:** `backend/app/agents/ticket_agent/watcher.py` + `sync_service.py`  
**Audited by:** `backend/app/agents/ticket_agent/auditor.py` (future)