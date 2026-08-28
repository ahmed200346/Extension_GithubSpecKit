# 🚀 AgentDocx - Spec Kit Orchestrator

**Version**: 0.0.6  
**Author**: Ahmed Aziz Ammar (5th Year AI Student)  
**License**: MIT

**VS Code Marketplace category**: `Integration` — l'extension relie Spec Kit, les CLI d'agents, le backend FastAPI, le frontend React et le Kanban Ticket Agent.

> [!NOTE]
> **Où se trouve cette extension ?** Branche `extension` (`BrancheExtenion/Extension_GithubSpecKit/agentdocx-speckit/`) — à part du pipeline `main` (`RepoSigma/Extension_GithubSpecKit/backend/`, `frontend/`, `specs/`). Voir `README.md` racine → `🌿 Branches du repo` pour cloner les deux ou les fusionner en `main` avant publication.

AgentDocx is a VS Code extension designed to bridge the gap between AI-generated software specifications and real-time project tracking. It empowers developers using the **Spec Kit** protocol to automatically sync their progress from markdown files to a live Kanban-style dashboard via the **Universal Ticket Agent**.

## 🌟 Key Features

- **⚡ Auto-Runtime Initialization**: Automatically creates per-project `.task_runtime` environments (`specs/{project}/.task_runtime/current-task.json`) for all projects in the `specs/` directory upon activation — isolated per project, no root-level conflicts.
- **🔍 Live Spec Watcher**: A Python-based background process that monitors specification files (`spec.md`, `plan.md`, `tasks.md`, etc.) and triggers the generation pipeline in real-time.
- **🎫 Universal Ticket Agent — Dual Watchers**: `StructureWatcher` (watches `specs/{project}/tasks.md`) + `StatusWatcher` (watches `specs/{project}/.task_runtime/current-task.json`) for autonomous `todo → in_progress → done` transitions. AI agents (Claude Code, Codex, Copilot, Cursor, Windsurf) write to `specs/{project}/.task_runtime/current-task.json` and the Kanban board syncs in real-time via `source:"watcher"` events.
- **🌐 FastAPI Backend**: A robust backend that manages the state of the specification pipeline and provides a REST API for integration. TicketManager is launched via `app.main:app` lifespan (`ticket_agent_lifespan`) with structured logging.
- **💻 React-Based Frontend**: A modern dashboard to visualize the project's progress, current tasks, and pipeline status with polling fallback for WebSocket.
- **🤖 AI Agent Synergy**: Specifically optimized to work with Claude Code (via `CLAUDE.md`), Codex (`AGENTS.md`), Copilot, Cursor and Windsurf through the Universal Contract (`specs/{project}/.task_runtime/current-task.json`).

## 🛠️ Technical Architecture

- **Extension**: TypeScript / VS Code API (`src/extension.ts` with `initTaskRuntimes()` per-project)
- **Backend**: Python / FastAPI / Uvicorn (`scripts/python/start_server.py` → `app.main:app` with `ticket_agent_lifespan`)
- **Ticket Agent**: `DualWatcherManager` (StructureWatcher + StatusWatcher) → `SyncService` → `Auditor` (threshold 75.0)
- **Database**: PostgreSQL `FinalDB` (production) / SQLite fallback — `Ticket`, `TicketEvent` and `TicketMetrics` with `source:"watcher"` tracking
- **Frontend**: React / JavaScript
- **Sync Engine**: Watchdog (Python) → FastAPI → React Frontend + Ticket Agent file watcher (`specs/{project}/.task_runtime/current-task.json` → DB → Kanban)

### 🎫 Ticket Agent Protocol

Every AI agent **MUST** write to `specs/{project}/.task_runtime/current-task.json` atomically (tmp + rename):
- **Before** a task → `"status":"in_progress"` + full `tasks` map
- **After** a task → `"status":"done"` + full `tasks` map
- See `CLAUDE.md`, `AGENTS.md`, `prompts/universal-contract.md` and `agentdocx-speckit/adapters/*` for the exact JSON schema. The backend `StatusWatcher` detects the file change and emits `status_change` events (`source:"watcher"`) for real-time Kanban transitions.

## 🚀 Installation & Usage

1. **Clone and Install**:
   Follow the standard VS Code extension installation process.
2. **Start the Infrastructure**:
   Use the extension commands to launch the components:
   - `AgentDocx: Start Server` (FastAPI)
   - `AgentDocx: Start Watcher` (Python Watcher)
   - `AgentDocx: Start Frontend` (React App)
3. **Work with Specs**:
   Create your specs in the `specs/` folder. The watcher will detect changes and synchronize them with your dashboard automatically.

## 📦 Development Setup

1. **Dependencies**:
   ```bash
   npm install
   ```
2. **Compile**:
   ```bash
   npm run compile
   ```
3. **Run**:
   Launch via `F5` in VS Code.

## 🐍 Prerequisites

- Python 3.10+
- Ollama installed and model `gemma4:31b-cloud` downloaded (`ollama pull gemma4:31b-cloud`)
- `ollama serve` running in the background.

## 📁 Project Structure

```text
agentdocx-speckit/
├── src/
│   └── extension.ts          # Extension entry point & Auto-init per-project .task_runtime
├── scripts/
│   ├── python/
│   │   ├── start_server.py   # FastAPI launcher (app.main:app + TicketManager lifespan + logging)
│   │   ├── spec_watcher.py   # Watchdog for specs/**/*.md
│   │   └── run_pipeline_cli.py
│   └── bash/
│       └── ...
├── adapters/                 # Universal Contract adapters (claude, codex, copilot, cursor, windsurf)
├── prompts/                  # Master protocol (universal-contract.md) + per-IDE adapters
├── frontend/                 # React Dashboard
├── package.json              # version 0.0.6
├── tsconfig.json
├── CHANGELOG.md
└── LICENSE.md

Per-project runtime (created by extension & AI agents):
specs/{project}/.task_runtime/current-task.json  # single source of truth for Ticket Agent
```

## 📈 Version History

For a detailed list of changes, please refer to the [CHANGELOG.md](./CHANGELOG.md).

---
*Developed as part of a 5th-year AI specialization project.*
