# Spec Kit Extensions

This directory contains the extensions and workflow definitions that bridge the **Spec Kit** framework with the **Agentic Enrichment Pipeline**. It allows for both seamless automation of standard business artifacts and the execution of advanced, multi-agent documentation workflows.

## 1. Overview

The extensions layer serves as the glue between the developer's workflow in Claude Code and the high-fidelity generation capabilities of the project's backend. It fulfills two primary roles:

- **Automatic Pipeline Orchestration**: Automatically triggers the enrichment pipeline when official Spec Kit artifacts are generated via the `speckit` CLI.
- **Advanced Documentation Generation**: Provides the custom `/doc-pipeline` command to transform a structured specification into a professional, technical document with an accompanying certified PDF.

---

## 2. Core Workflows & Features

### Standard Spec Kit Artifacts Automation
The extension integrates with the system's file monitoring logic to ensure that business-critical documents are always processed by the AI pipeline.
- **Trigger**: When the `speckit` CLI generates or modifies any of the 6 core artifacts (`spec`, `plan`, `tasks`, `contracts`, `requirements`, `constitution`), the **Watcher** (`scripts/spec_watcher.py`) detects the change.
- **Action**: The watcher notifies the FastAPI backend to initiate the enrichment process, ensuring that official project documents are consistently analyzed and validated.

### Smart Filtering Mechanism
To optimize resource usage and prevent "noise" in the pipeline, the extension employs a smart filtering system. It explicitly ignores Spec Kit's internal working documents such as:
- `research.md`
- `data-model.md`
- `quickstart.md`
- Any temporary draft files.
Only final-form artifacts are submitted to the multi-agent chain.

### Custom `/doc-pipeline` Extension Command
The `/doc-pipeline` command is a specialized entry point for generating high-end technical documentation. Instead of relying on simple file triggers, it allows the user to:
1. Initialize a structured specification using the project's internal templates.
2. Explicitly submit the document to the multi-agent pipeline for deep analysis and certification.

---

## 3. Multi-Agent Execution Pipeline (`/doc-pipeline`)

When a document is submitted via the `/doc-pipeline` workflow, it is processed through a four-phase chain orchestrated by the FastAPI backend:

### Phase 1: Preparation & Specification
The pipeline initializes the input specification file. This ensures the document adheres to the required structural markers needed for agents to accurately identify sections.

### Phase 2: Parallel Analysis
Four specialized agents analyze the document concurrently to maximize efficiency:
- **Summary Agent**: Extracts key business concepts and assesses maturity alignment.
- **Glossary Agent**: Identifies technical terms and acronyms, ensuring consistent terminology and eliminating tautologies.
- **Diagram Agent**: Validates architectural requirements and generates professional diagrams (SVG/PDF).
- **Parsing Agent**: Performs a structural check for schema adherence and relational integrity between sections.

### Phase 3: Convergence & Writing
The **DocWriter Agent** acts as the synthesizer. It fuses the outputs from the parallel analysis (summary, glossary, and diagrams) into a comprehensive, enriched Markdown document, ensuring a fluid narrative and correct embedding of technical assets.

### Phase 4: Layout & PDF Certification
The final stage is handled by the **Layout Agent**, which:
1. Compiles the Markdown into a high-fidelity HTML/CSS layout.
2. Performs a "page-budget" check to ensure optimal readability.
3. Produces the **Certified PDF** (`doc-pipeline-###.pdf`) and a detailed JSON metrics report (`_eval.json`).

---

## 4. Directory & Workflow Structure

```text
extensions/
├── enabled.conf                # List of currently active workflows (e.g., doc-pipeline)
└── workflows/                  # Definitions for custom Claude Code extensions
    └── doc-pipeline/           # The enriched documentation workflow
        ├── template.md         # The structural template for input specifications
        └── tasks-template.md   # The detailed pipeline task list for tracking agent progress
```

---

## 5. Backend Integration

The extension communicates with the backend via a REST API provided by the **FastAPI** server:

- **Base URL**: `http://127.0.0.1:8000` (Default)
- **Execution Endpoint**: `POST /api/v1/pipeline/run`
- **Process Flow**: 
  1. Extension sends the file path and workflow ID to the backend.
  2. Backend spawns the agent chain.
  3. Extension/User can poll for status updates and agent logs.
  4. Final deliverables (PDF and `_eval.json`) are deposited in the `outputs/` directory.

---

## 6. Commands, Configuration & Usage

### Using the Command
In the Claude Code environment, you can invoke the pipeline using:
` /doc-pipeline `

### Configuration
- **Activation**: To enable or disable specific workflows, update the `extensions/enabled.conf` file.
- **Integration**: The extension is designed to work in tandem with `scripts/spec_watcher.py`. Ensure the backend server is running (`uvicorn app.main:app`) before executing CLI commands or using the extension.
