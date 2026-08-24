# Backend Architecture - Spec-Kit

This directory contains the backend implementation of the Spec-Kit project. The backend is designed as an agentic pipeline that transforms raw technical documents into structured, enriched, and professionally formatted specifications.

## 🏗️ Architecture Overview

The backend follows a layered architecture to ensure modularity, provider independence, and structured data flow.

### 1. LLM Provider Layer (`app/core/`)
The system implements a **Strategy/Facade pattern** to handle multiple LLM providers (Ollama, Gemini, NVIDIA) through a single interface.

- **`llm_client.py`**: The central orchestrator. It dynamically loads the active provider based on the `LLM_PROVIDER` environment variable.
- **Provider Clients**: Specific implementations (e.g., `client_ollama.py`, `client_gemini.py`) that translate generic requests into provider-specific API calls.
- **Uniform Interface**: All services use `get_llm_client()` and `get_llm_model()`, making the rest of the application agnostic to which LLM is actually running.

### 2. Service Layer (`app/services/`)
The system uses a "Logic vs. Execution" separation: **Services** handle the intelligence (the "what"), while **Utility Tools** handle the technical execution (the "how").

- **Agent Services**:
    - `ParserService`: Performs initial structural analysis and categorization.
    - `SummaryService`: Generates executive summaries.
    - `GlossaryService`: Extracts and defines technical terms.
    - `DiagramService`: Generates Mermaid/PlantUML diagrams.
    - `DocWriterService`: Synthesizes all previous outputs into a coherent Markdown document.
    - `LayoutService`: Handles final formatting and PDF rendering.
- **Evaluation Services**: Parallel to each agent service, an evaluator (e.g., `ParsingEvaluatorService`) checks the quality of the output against templates or original data.

### 🛠️ Utility Tools Layer (`app/utils/`)
This layer provides the concrete implementation for the services. Each agent relies on a specialized set of tools to interact with the filesystem and external formats.

| Agent | Utility Tool | Technical Role |
| :--- | :--- | :--- |
| **Parsing** | `markdown_parser.py` | Decomposes raw Markdown into logical sections and calculates file hashes for change detection. |
| **Summary** | `summary_pruner.py` | Post-processes LLM summaries to remove redundancies and ensure conciseness. |
| **Glossary** | `glossary_tools.py` | Harvests technical terms and creates internal document anchors for cross-referencing. |
| **Diagram** | `diagram_tools.py` | Renders Mermaid/PlantUML code into visual PDF diagrams. |
| **Doc Writer**| `doc_writer_tools.py`| Formats the final synthesis and manages Markdown injection of summaries and diagrams. |
| **Layout** | `layout_tools.py` | Handles the professional PDF publication (margins, fonts, and page layout). |

#### Transverse Tools (Cross-Agent)
- **`path_builder.py`**: The central authority for the filesystem. It ensures all agents read/write to the correct versioned directories in `/outputs/`.
- **`responses.py`**: Standardizes API response formats for the FastAPI layer to ensure seamless frontend integration.


### 3. Pipeline Orchestration (`app/graph/`)
The agentic flow is managed using **LangGraph**, treating the pipeline as a state machine.

- **`workflow.py`**: Defines the graph topology.
- **`state.py`**: Defines the `GraphState`, a shared memory object that carries data (parsed JSON, summaries, metrics) between nodes.
- **`nodes.py`**: Implements the execution logic for each node in the graph, acting as the glue between the graph and the services.

---

## 🔄 The Agent Pipeline Flow

The transformation process follows a structured sequence:

1. **START** $\to$ **Parsing Agent**: Analyzes the input file and creates a structured JSON representation.
2. **Parallel Enrichment**: Three agents run concurrently using the parsed data:
    - **Summary Agent** $\to$ Executive summary.
    - **Glossary Agent** $\to$ Technical dictionary.
    - **Diagram Agent** $\to$ Visual architectural representations.
3. **Convergence** $\to$ **Doc Writer Agent**: Collects outputs from all previous stages to write the final technical specification.
4. **Finalization** $\to$ **Layout Agent**: Applies professional styling and renders the final PDF.
5. **END**

---

## 📂 Directory Structure

| Directory | Purpose |
| :--- | :--- |
| `app/api/` | FastAPI endpoints for triggering pipelines and monitoring. |
| `app/core/` | LLM client management, configuration, and common utils. |
| `app/graph/` | LangGraph workflow definitions, nodes, and state management. |
| `app/services/` | Core logic for each agent and their respective evaluators. |
| `app/schemas/` | Pydantic models for strict input/output validation. |
| `app/resources/` | JSON specification files defining agent constraints and templates. |
| `app/utils/` | Helper tools for PDF rendering, Markdown parsing, and path management. |

## 💾 State & Persistence

- **PostgreSQL**: Used to track every run of the pipeline. The `PipelineStage` model records the status, output, and evaluation metrics for each agent in real-time.
- **Disk Storage**: Intermediate JSON outputs and final PDFs are stored in a versioned directory structure for auditability and debugging.
