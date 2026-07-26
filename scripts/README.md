# ⚙️ Automation Scripts

This directory contains the orchestration engine and utility scripts that drive the Spec Kit agentic pipeline. It bridges the gap between raw Markdown files in the `specs/` directory and the FastAPI-based agent orchestration backend.

## 🚀 Overview

The scripts in this folder automate the lifecycle of a specification: from the creation of a new workflow branch to the real-time detection of changes that trigger the AI pipeline.

---

## 👁️ Real-time File Watcher (`python/spec_watcher.py`)

The Watcher is a background service that monitors the `specs/` directory. Its primary goal is to ensure that any modification to an official architectural artifact immediately triggers the processing pipeline.

### 🛠️ How it Works
- **Event Detection**: Uses the `watchdog` library to listen for `on_created`, `on_modified`, and `on_moved` events. The `on_moved` event is critical for capturing "atomic saves" performed by modern IDEs and tools like Claude Code.
- **Artifact Filtering**: To avoid triggering the pipeline on every temporary file, it only reacts to files whose names start with types defined in `ALLOWED_ARTIFACT_TYPES`:
  - `spec`, `plan`, `tasks`, `task`, `constitution`, `requirements`, `contracts`.
  - **Excluded**: Internal working documents like `research.md`, `quickstart.md`, and `data-model.md` are automatically ignored to prevent redundant pipeline runs.
- **Robustness Mechanisms**:
  - **Stabilization**: The `wait_until_file_is_stable` function prevents triggering the pipeline while a file is still being written to disk (prevents partial reads).
  - **Database Guard**: The `is_file_already_in_db` check ensures that existing files aren't re-processed unnecessarily upon watcher restart.
  - **Sequential Processing**: Uses a `Queue` and a dedicated `queue_worker` thread to process files one-by-one, preventing server overload and race conditions.

---

## 💻 Pipeline CLI (`python/run_pipeline_cli.py`)

For cases where background monitoring is not desired or specific files need to be re-processed manually, the CLI tool provides a synchronous interface to the pipeline.

### 🛠️ Usage
```bash
python scripts/python/run_pipeline_cli.py --file specs/my-project/spec.md
```
The CLI handles:
1. **Server Availability**: Checks if the FastAPI server is running and idle.
2. **Synchronous Execution**: Waits for the LangGraph agents to complete the full processing cycle.
3. **Result Reporting**: Displays the execution time and the path to the generated final PDF.

---

## 🐚 Bash Utilities

The bash scripts provide convenient entry points for the Python automation logic.

### 🏁 `start-watcher.sh`
A wrapper script to launch the `spec_watcher.py` from the project root.
**Usage**: `./scripts/bash/start-watcher.sh`

### 🏗️ `create-doc-pipeline.sh`
This is the **initialization engine** for new features. It sets up the environment for a new architectural cycle:
1. **ID Generation**: Increments the `doc-pipeline-###` identifier.
2. **Git Integration**: Automatically creates and switches to a new feature branch (e.g., `doc-pipeline/001-feature-name`).
3. **Workspace Setup**: Creates a dedicated project folder in `specs/` and populates it with official templates (`template.md`, `tasks.md`).

---

## 🔄 Full Automation Workflow

The following diagram represents the end-to-end lifecycle of a specification within this project:

```text
[ Manual Start ] ➔ create-doc-pipeline.sh ➔ Creates Branch & templates in specs/
                                 │
                                 ▼
[ User Edit ] ➔ Writes Markdown file in specs/
                                 │
                                 ▼
[ Detection ] ➔ spec_watcher.py (detects event) ➔ Stabilization Check ➔ Type Filtering
                                 │
                                 ▼
[ Queuing ] ➔ Sequential Queue ➔ Worker picks up file ➔ is_file_already_in_db?
                                 │
                                 ▼
[ Execution ] ➔ API Call (/run) ➔ LangGraph Agents ➔ PDF Generation
                                 │
                                 ▼
[ Storage ] ➔ Final artifacts organized in /outputs/<project-folder>/
```
