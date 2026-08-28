# 🚀 Spec Kit — AgentDocx Ticket Manager

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.7-blue?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="fastapi" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="postgres" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="license" />
</p>

<p align="center">
  <b>Pipeline multi-agents</b> • <b>Ticket Agent temps réel</b> • <b>Kanban autonome</b><br/>
  <i>Transforme des specs Markdown brutes en livrables certifiés avec traçabilité complète</i>
</p>

---

<details>
<summary>📑 Table des matières</summary>

- [Architecture Générale](#-architecture-générale-du-projet)
- [Cœur Agentique](#-le-cœur-agentique--pipeline--ressources-de-guidage)
- [Frontend](#️-interface-frontend)
- [Agent Ticket](#-agent-ticket--universal-ticket-agent-kanban-sync-temps-réel)
- [Traçabilité BDD](#️-traçabilité--versioning-bdd-postgresql)
- [Extension VS Code](#-extension-vs-code-speckit-nouveau)
- [Quick Start](#-quick-start-guide-de-lancement--pour-un-clone-vierge)

</details>

---

## 📌 Architecture Générale du Projet

Le projet adopte une architecture modulaire où l'IA n'est pas seulement un "chat", mais un ensemble d'agents spécialisés orchestrés comme un flux de travail industriel.

### 📂 Arborescence & Rôles
- **`/backend`** : ⚙️ **Le Moteur**. Propulsé par **FastAPI** et **LangGraph**. Il contient la logique d'orchestration, les services d'agents, la gestion des providers LLM et le **Ticket Agent** (`app/agents/ticket_agent/`).
  - 📘 *Architecture Technique* : Consultez le [README du backend](backend/README.md) pour les détails sur le `llm_client`, les services et l'architecture du Ticket Agent.
- **`/frontend`** : 🖥️ **Le Poste de Contrôle**. Dashboard **React** pour le monitoring temps réel, la visualisation des KPIs, la gestion des documents et le **Kanban Ticket Board** (polling `task-state` + WebSocket).
- **`/specs`** : 📄 **La Source**. Dossier surveillé contenant les spécifications Markdown brutes, le fichier `tasks.md` et **`.task_runtime/current-task.json` par projet** (`specs/{project}/.task_runtime/` — source unique pour le Ticket Agent).
- **`/outputs`** : 📦 **L'Usine**. Stockage centralisé des livrables (JSON, Markdown enrichis, PDF versionnés).
- **`/prompts`** : 📝 **Le Contrat — Source d'initialisation**. `universal-contract.md` (maître) + 5 adapters (`claude` → `CLAUDE.md`, `codex` → `AGENTS.md`, `copilot` → `.github/copilot-instructions.md`, `cursor` → `.cursorrules`, `windsurf` → `.windsurfrules`). **Indispensable même s'il n'est pas exécuté** : c'est en copiant ces fichiers à la racine que le LLM devient Ticket Agent (`specs/{project}/.task_runtime`).
- **`/documentation`** : 📚 **Guides de référence**. `commands/` (`lifecycle-guide.md`, `sync-commands.md`) pour le cycle de vie `/speckit-*` et `jira/` (`mapping-rules.md`, `ticket-templates.md`) pour les règles de mapping. N'affecte pas le runtime, mais explique comment initialiser et étendre les règles LLM.
- **`/agentdocx-speckit`** : 🧩 **L'Extension**. VS Code extension (`src/extension.ts`, `scripts/python/start_server.py`) qui auto-crée les `.task_runtime` par projet et lance le Ticket Manager.

---

## 📚 Documentation Détaillée par Module

> [!NOTE]
> Ce README racine donne une vue d'ensemble. Pour approfondir chaque partie, consultez :

| Module | README détaillé | Contenu |
|---|---|---|
| **🧩 Extension VS Code** | [`agentdocx-speckit/README.md`](agentdocx-speckit/README.md) | Auto-init `.task_runtime`, Dual Watchers, `start_server.py`, `spec_watcher.py`, packaging `0.0.7` |
| **🖥️ Frontend Dashboard** | [`frontend/README.md`](frontend/README.md) | React/MUI, Kanban Board, `kanbanSlice`, Drag & Drop, polling + WebSocket |
| **⚙️ Backend Moteur** | [`backend/README.md`](backend/README.md) | LLM providers (ollama/gemini/nvidia), LangGraph, Ticket Agent (`manager`, `watcher`, `sync_service`, `auditor`), API & BDD |

---

## 🧠 Le Cœur Agentique : Pipeline & Ressources de Guidage

L'originalité de Spec Kit réside dans son approche **"Guidée par Spécification"**. Chaque agent du pipeline ne se contente pas d'un prompt, mais est piloté par des **fichiers de ressources JSON** qui définissent des contraintes strictes, des structures attendues et des critères de qualité.

### 🛠️ Cartographie des Agents et leurs Ressources

| Agent | Ressource JSON (`backend/app/resources/`) | Rôle du fichier de guidage |
| :--- | :--- | :--- |
| **Parsing Agent** | `sdd_templates.json` | Définit les gabarits de structure selon le type de document (Constitution, Plan, Spec, Task). |
| **Summary Agent** | `summary_spec.json` | Spécifie la structure et les points clés requis pour l'executive summary. |
| **Glossary Agent** | `glossary_spec.json` | Définit les règles d'extraction des termes techniques et le format du dictionnaire. |
| **Diagram Agent** | `diagram_spec.json` | Guide la génération des schémas Mermaid/PlantUML (types de diagrammes, niveau de détail). |
| **Doc Writer Agent**| `doc_writer_spec.json`| Règle la synthèse finale : comment fusionner summary, glossary et diagrams dans le Markdown. |
| **Layout Agent** | `layout_spec.json` | Définit les contraintes de mise en page et les paramètres de rendu PDF final. |

### 🔄 Flux de Transformation
1. **Analyse (`Parsing`)** $\to$ Transforme le texte brut en JSON structuré via `sdd_templates.json`.
2. **Enrichissement Parallèle** $\to$ Trois agents utilisent les ressources `summary_spec`, `glossary_spec` et `diagram_spec` pour ajouter de la valeur.
3. **Synthèse (`DocWriter`)** $\to$ Fusionne tout selon `doc_writer_spec.json`.
4. **Publication (`Layout`)** $\to$ Produit le PDF final selon `layout_spec.json`.

---

## 🖥️ Interface Frontend

Le Frontend est une application React moderne utilisant **Material-UI** et **DataGrid** pour offrir une expérience de monitoring fluide et intuitive.

### 🔍 Fonctionnalités Clés
- **Suivi Temps Réel** : Visualisation instantanée de l'état d'avancement des agents.
- **Analyse de Performance** : Affichage des KPIs de qualité pour chaque étape du pipeline.
- **Gestion Documentaire** : Interface d'upload simplifiée pour initier de nouveaux processus.

### 📸 Aperçus
| 📑 Page Documents | ➕ Ajouter un Document |
| :---: | :---: |
| ![Documents Page](documents.png) | ![Add Document Page](form.png) |
| *Suivi des exécutions, status et viewer PDF* | *Formulaire d'upload et zone Drag & Drop (.md)* |

> 📖 Pour une documentation technique complète sur le frontend, consultez le fichier [`frontend/README.md`](frontend/README.md).

---

## 📋 Agent Ticket — Universal Ticket Agent (Kanban Sync Temps Réel)

L'**Agent Ticket** assure une synchronisation autonome et temps réel entre l'avancement technique (via n'importe quel LLM : Claude Code, Codex, Copilot, Cursor, Windsurf) et le tableau Kanban (To Do / In Progress / Done). Il remplace l'ancien Agent JIRA et fonctionne par **fichier unique par projet**.

### 📊 Métriques d'une tâche implémentée

Après le passage d'une tâche à `done`, le Ticket Agent déclenche l'Auditor backend. Le dashboard affiche ensuite dans l'onglet **Metrics** le score de conformité global, le verdict et quatre indicateurs détaillés : couverture des exigences, qualité du code, respect de l'architecture et traçabilité. Il affiche également la date du dernier audit et, lorsqu'elles sont disponibles, les métriques produites par l'agent.

![Métriques d'une tâche implémentée](ticket_metricx.png)

Exemple visible sur la capture : score de conformité `84.8`, verdict `COMPLIANT`, couverture des exigences `100 %`, qualité du code `74 %`, architecture `90 %` et traçabilité `55 %`. Ces valeurs sont calculées par le backend à partir des critères de la tâche et des éléments d'implémentation ; elles ne sont pas écrites manuellement par le LLM dans `current-task.json`.

### 🎯 Source Unique : `specs/{project}/.task_runtime/current-task.json`

Chaque projet sous `specs/` possède son propre `.task_runtime` isolé :
```
specs/001-course-management-system/.task_runtime/current-task.json
specs/002-autre-projet/.task_runtime/current-task.json
```
Aucun dossier racine `.task_runtime` — isolation totale, pas de conflit entre projets.

Format JSON (atomique, tmp + rename) :
```json
{
  "task_id": "T009",
  "file": "backend_course/main.py",
  "status": "in_progress",
  "project_name": "001-course-management-system",
  "updated_at": "2026-08-25T10:00:00.000Z",
  "tasks": { "T001": "done", "T002": "done", ..., "T009": "in_progress", "T010": "todo" }
}
```

### 🔄 Flux de Synchronisation Détaillé

#### 1. Ingestion des Tâches (`POST /api/v1/ingest`)
- **Processus** : Le backend analyse `specs/{project}/tasks.md` → crée les tickets (`T001`, `T002`, ...) avec statut initial `todo` + événement `source:"initial_ingestion"`.

![Dashboard Ingestion](DashboardVide.png)
*Utilisation du bouton "Ingest Tasks" pour synchroniser les tâches de `tasks.md` vers le Kanban.*

#### 2. Transition Autonome via `current-task.json` (Dual Watchers)
Le Ticket Manager (`backend/app/agents/ticket_agent/manager.py`) orchestre deux watchers :

| Watcher | Surveille | Déclenche |
|---|---|---|
| **StructureWatcher** | `specs/{project}/tasks.md` | Signal "ready for ingestion" (nouvelle tâche détectée) |
| **StatusWatcher** | `specs/{project}/.task_runtime/current-task.json` | `SyncService.sync_current_task()` → `TicketEvent` `source:"watcher"` → `todo → in_progress → done` |

![Dashboard Synchronisation](DashboardRempli.png)
*Visualisation du tableau Kanban synchronisé en temps réel avec l'activité de l'Agent Ticket.*

**Cycle nominal (ex: T009) :**
```
LLM écrit current-task.json {task_id:"T009", status:"in_progress", tasks:{...}} 
  → StatusWatcher détecte → DB: T009 todo→in_progress (source:"watcher")
LLM écrit current-task.json {task_id:"T009", status:"done"}
  → StatusWatcher détecte → DB: T009 in_progress→done (source:"watcher") → Auditor (si activé, seuil 75)
```

#### 3. Auditor (Optionnel)
Si `ENABLE_AUDITOR=True`, chaque passage `→ done` déclenche `Auditor.auto_audit_on_done()` (conformité < 75 → revert `done → in_progress` + événement `audit`).

### 🤖 Contrat Universal (`prompts/universal-contract.md`)

Pour fonctionner comme Agent Ticket, le LLM **DOIT** suivre le protocole (voir `prompts/universal-contract.md` — source unique, et ses adapters) :
- **Avant chaque tâche** : Écrire `specs/{project}/.task_runtime/current-task.json` avec `status: "in_progress"` + **FULL `tasks` map**.
- **Après chaque tâche** : Écrire le même fichier avec `status: "done"` + FULL `tasks` map.
- **Écriture atomique** : `current-task.json.tmp` → `rename` pour éviter les lectures partielles.

Adapters fournis pour chaque IDE :
| IDE | Fichier à copier dans votre projet cloné | Source |
|---|---|---|
| **Claude Code** | `CLAUDE.md` | `prompts/claude-adapter.md` |
| **Codex** | `AGENTS.md` | `prompts/universal-contract.md` → `AGENTS.md` |
| **Cursor** | `.cursorrules` | `prompts/cursor-adapter.md` |
| **Windsurf** | `.windsurfrules` | `prompts/windsurf-adapter.md` |
| **Copilot** | `.github/copilot-instructions.md` | `prompts/copilot-adapter.md` |

> **QuickStart pour un nouveau clone :** Copiez le fichier adapter correspondant à votre LLM depuis `prompts/` ou `agentdocx-speckit/adapters/` vers la racine du projet cloné (voir section Quick Start ci-dessous). Sans ce fichier, le LLM ne sait pas qu'il doit mettre à jour `current-task.json` et le Kanban restera bloqué.

---

## 🗄️ Traçabilité & Versioning BDD (PostgreSQL) 

Le système s'appuie sur **PostgreSQL `DATABASE`** (création autonome via `Base.metadata.create_all` au lancement) pour l'immuabilité des versions et la traçabilité complète.

**Nouveautés `0.0.7` :**
- **`ticket_metrics`** : table dédiée `1 ticket → 0..1 metrics` (`conformity_score`, `verdict`, `requirement_coverage`, `code_quality`, `architecture`, `traceability`, `last_audit_at`, `audit_metadata JSONB`) — remplace le scan `ticket_events.event_metadata` pour `GET /tickets/{id}/metrics` (fini le `N/A`)
- **Cascades** : `Project -- cascade --> Ticket -- cascade --> TicketEvent/TicketComment/TicketMetrics` et `Project -- cascade --> TicketMetrics` → `DELETE FROM projects` supprime tout (plus de tickets orphelins après `rm -rf specs/`)
- **Isolation** : `specs/{project}/.task_runtime/current-task.json` reste la seule source disque, `tickets`/`ticket_metrics` en sont le miroir DB

### 📊 Modèle de Données 
```mermaid
erDiagram
    projects {
        UUID id "PK"
        VARCHAR name
        VARCHAR repo_url
        DATETIME created_at
    }
    artifacts {
        UUID id "PK"
        UUID project_id "FK"
        VARCHAR current_file_hash
        VARCHAR source_path
        VARCHAR artifact_type
        DATETIME created_at
    }
    projects ||--o{ artifacts : references
    doc_versions {
        UUID id "PK"
        UUID artifact_id "FK"
        INTEGER version_no
        VARCHAR version_label
        VARCHAR pdf_path
        VARCHAR source_file_hash
        DATETIME generated_at
        JSONB sections_summary
        VARCHAR commit_hash
        VARCHAR generated_by
        UUID pipeline_run_id "FK"
        FLOAT global_kpi_score
    }
    artifacts ||--o{ doc_versions : references
    pipeline_runs ||--o{ doc_versions : references
    pipeline_runs {
        UUID id "PK"
        UUID artifact_id "FK"
        VARCHAR current_stage
        JSONB structured_json
        TEXT summary_output
        JSONB diagram_output
        JSONB glossary_output
        TEXT written_doc
        TEXT layout_output
        JSONB parsing_eval
        JSONB summary_eval
        JSONB glossary_eval
        JSONB diagram_eval
        JSONB writer_eval
        JSONB layout_eval
        FLOAT global_kpi_score
        TEXT error_message
        DATETIME started_at
        DATETIME completed_at
    }
    artifacts ||--o{ pipeline_runs : references
    tickets {
        UUID id "PK"
        UUID project_id "FK"
        UUID artifact_id "FK"
        VARCHAR ticket_id
        TEXT title
        TEXT description
        VARCHAR status
        VARCHAR source_file_path
        VARCHAR source_file_hash
        VARCHAR checkbox_state
        INTEGER line_number
        DATETIME created_at
        DATETIME updated_at
    }
    projects ||--o{ tickets : references
    artifacts ||--o{ tickets : references
    ticket_events {
        UUID id "PK"
        UUID ticket_id "FK"
        VARCHAR event_type
        VARCHAR author_name
        VARCHAR author_type
        VARCHAR old_status
        VARCHAR new_status
        TEXT comment
        JSONB event_metadata
        DATETIME created_at
    }
    tickets ||--o{ ticket_events : references
    ticket_comments {
        UUID id "PK"
        UUID ticket_id "FK"
        VARCHAR author_name
        VARCHAR author_type
        TEXT content
        DATETIME created_at
    }
    tickets ||--o{ ticket_comments : references
    ticket_metrics {
        UUID id "PK"
        UUID ticket_id "FK"
        UUID project_id "FK"
        FLOAT conformity_score
        VARCHAR verdict
        FLOAT requirement_coverage
        FLOAT code_quality
        FLOAT architecture
        FLOAT traceability
        DATETIME last_audit_at
        JSONB audit_metadata
        DATETIME created_at
        DATETIME updated_at
    }
    tickets ||--o{ ticket_metrics : references
    projects ||--o{ ticket_metrics : references
```

### 📋 Explication des Tables

#### Tables documentaires (V1 — pipeline agentique)

| Table | Rôle | Champs clés |
|---|---|---|
| **`projects`** | Entité racine — chaque projet suivi | `id` (UUID PK), `name`, `repo_url`, `created_at` |
| **`artifacts`** | Fichiers SDD surveillés (spec.md, plan.md, tasks.md…) | `project_id` FK, `current_file_hash` (SHA-256), `source_path`, `artifact_type` (spec/plan/task/constitution…) |
| **`doc_versions`** | Versions compilées d'un artefact (PDF immutable) | `artifact_id` FK, `version_no` (incrémental), `pdf_path`, `source_file_hash`, `global_kpi_score`, `pipeline_run_id` FK |
| **`pipeline_runs`** | Traçabilité d'un run complet du graphe LangGraph | `artifact_id` FK, `current_stage` (parsing/parallel_enrichment/writing/layout/rendering/completed/failed), sorties brutes de chaque agent (`structured_json`, `summary_output`, `diagram_output`, `glossary_output`, `written_doc`, `layout_output`), évaluations JSON (`parsing_eval`…`layout_eval`), `global_kpi_score`, `error_message`, `started_at`, `completed_at` |

#### Tables de tickets (V2 — Agent Ticket unifié)

| Table | Rôle | Champs clés |
|---|---|---|
| **`tickets`** | Tâches issues de `tasks.md`, synchronisées avec le Kanban | `project_id` FK cascade, `ticket_id` (T001, T002…), `status` (todo/in_progress/done), `source_file_path` (tasks.md#T004), `checkbox_state`, `line_number` |
| **`ticket_events`** | Historique des transitions de statut | `ticket_id` FK, `event_type`, `old_status`, `new_status`, `event_metadata` JSONB — source : `initial_ingestion` / `watcher` / `audit` |
| **`ticket_comments`** | Commentaires sur un ticket | `ticket_id` FK, `author_name`, `author_type` (human/agent), `content` |
| **`ticket_metrics`** | Métriques de conformité (Auditor backend) | `ticket_id` FK unique cascade, `project_id` FK cascade, `conformity_score`, `verdict` (COMPLIANT / NON-COMPLIANT), `requirement_coverage`, `code_quality`, `architecture`, `traceability`, `last_audit_at`, `audit_metadata` JSONB |

#### Cascades et propriétés

```
Project ──cascade──> Ticket ──cascade──> TicketEvent
                                  ──cascade──> TicketComment
                                  ──cascade──> TicketMetrics
Project ──cascade──> TicketMetrics
```

- **`DELETE FROM projects`** supprime toute la hiérarchie : artifacts, doc_versions, pipeline_runs, tickets, ticket_events, ticket_comments, ticket_metrics
- **`ticket_metrics`** est la table dédiée aux métriques : `1 ticket → 0..1 metrics` — remplace le scan `ticket_events.event_metadata` pour `GET /tickets/{id}/metrics` (fini le `N/A`)
- **`specs/{project}/.task_runtime/current-task.json`** reste la seule source disque ; `tickets` / `ticket_metrics` en sont le miroir DB

---

## 🔌 Extension VS Code SpecKit (Nouveau)

L'extension VS Code **AgentDocx SpecKit** offre une expérience intégrée dans une seule fenêtre VS Code, remplaçant les scripts manuels.

- **Logs Intégrés** : Trois canaux dans la vue Output (`AgentDocx Server`, `AgentDocx Watcher`, `AgentDocx Frontend`).
  - **AgentDocx Watcher** — logs watchdog, détection fichiers, file d'attente
    ![AgentDocx Watcher](AgentDocxWatcher.png)
  - **AgentDocx Server** — logs FastAPI, progression agents (Parsing → Summary → Glossary → Diagram → DocWriter → Layout), KPIs + Ticket Manager (`[TicketManager]`, `[StatusWatcher]`, `[SyncService]`)
    ![AgentDocx Server](AgentDocxServer.png)
  - **AgentDocx Frontend** — logs React, compilation `webpack compiled successfully`, URL `http://localhost:5000`
    ![AgentDocx Frontend](AgentDocxFrontend.png)
- **Automatisation** : Démarrage automatique du serveur, du watcher et du frontend au chargement de l'extension (via `src/extension.ts`).
- **Commandes Palette** : `AgentDocx: Start Server`, `AgentDocx: Start Watcher`, `AgentDocx: Start Frontend`, `AgentDocx: Trigger Pipeline`, etc.

### 📦 Installation (via .vsix)
> 📸 **Installation via .vsix** :
> ![Installation VSIX](ExtensionVSCode.png)
> *(Capture : icône Extensions → "..." → "Install from VSIX..." → sélectionner le fichier .vsix)*

1. Téléchargez `agentdocx-speckit-0.0.7.vsix`.
2. `Ctrl+Shift+P` $\rightarrow$ **Extensions: Install from VSIX...**

---

## 🌿 Branches du repo — où se trouve quoi ?

> **Depuis `0.0.7`, tout est dans `main` au même niveau** (plus besoin de 2 clones) :

| Emplacement dans `main` | Contenu | README détaillé |
|---|---|---|
| `backend/` | Pipeline FastAPI + Ticket Agent | [`backend/README.md`](backend/README.md) |
| `frontend/` | Dashboard React + Kanban | [`frontend/README.md`](frontend/README.md) |
| `agentdocx-speckit/` | Extension VS Code (`src/extension.ts`, `scripts/python/`) | [`agentdocx-speckit/README.md`](agentdocx-speckit/README.md) |
| `specs/` | Projets `001-...`, `002-...` (`tasks.md` + `.task_runtime/`) | — |
| `prompts/` | Contrats universels (`universal-contract.md` + adapters) | — |

> **Branche `extension` = miroir de dev** pour l'extension seule (`BrancheExtenion/`). Pour publier, on l'a **mergée dans `main`** — un seul `git clone` suffit désormais.

**Clone unique (recommandé) :**
```bash
git clone https://github.com/ahmed200346/Extension_GithubSpecKit.git
cd Extension_GithubSpecKit
# Vérifie : ls backend/ frontend/ agentdocx-speckit/ specs/
```

---

## 🚀 Quick Start (Guide de Lancement — pour un clone vierge)

### 1. Prérequis
- **PostgreSQL** : Lancé avec une base vide (nom au choix, défini dans `.env` → `DATABASE_URL`).
- **LLM Provider** : Ollama lancé (`ollama serve`) ou clés API configurées dans `.env` (Gemini, NVIDIA).
- **Node.js 18+** et **Python 3.10+**.

### 2. Configuration `.env` — le cœur du projet (DB inchangée)

> [!IMPORTANT]
> Copiez `.env.example` à la racine en `.env` **ou** créez un nouveau `.env` à la racine. **Ne modifiez pas `DATABASE_URL`** après la première création de la base.

<table>
<tr>
<td>

**📦 Depuis `.env.example` → copiez puis remplissez vos clés**

```bash
cp .env.example .env
# puis éditez .env : GEMINI_API_KEY, NVIDIA_API_KEY
```

```dotenv
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄️  DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖  LLM PROVIDER — choix unique (facade: llm_client.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ollama  → local via `ollama serve`
#  gemini  → Google API
#  nvidia  → NVIDIA NIM
LLM_PROVIDER=gemini

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎫  TICKET AGENT — auto-découverte recommandée
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET_PROJECT_PATH=
ENABLE_AUDITOR=True
AUDITOR_THRESHOLD=75.0
LLM_REQUEST_TIMEOUT=600

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📄  STOCKAGE & LOGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PDF_STORAGE_DIR=./storage/pdfs
LOG_LEVEL=INFO
```

</td>
</tr>
</table>

<details>
<summary>🦙 <b>Si <code>LLM_PROVIDER=ollama</code> → cliquez pour voir la config</b></summary>

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud   # ou via `ollama pull gemma4:31b-cloud`
```
> Lancer au préalable : `ollama serve` puis `ollama pull gemma4:31b-cloud`

</details>

<details>
<summary>✨ <b>Si <code>LLM_PROVIDER=gemini</code> → cliquez pour voir la config</b></summary>

```dotenv
GEMINI_API_KEY=VOTRE_CLE_GEMINI
GEMINI_MODEL=gemini-3.1-flash-lite
```

</details>

<details>
<summary>🟢 <b>Si <code>LLM_PROVIDER=nvidia</code> → cliquez pour voir la config</b></summary>

```dotenv
NVIDIA_API_KEY=VOTRE_CLE_NVIDIA
NVIDIA_MODEL=meta/llama-3.3-70b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

</details>

> [!TIP]
> **Laissez `TARGET_PROJECT_PATH=` vide** — le `TicketManager` résout dynamiquement :
> `1)` `TARGET_PROJECT_PATH` si défini → `2)` scan `**/.task_runtime/current-task.json` le plus récent → `3)` scan `specs/*/tasks.md` → `4)` fallback `BASE_DIR`.
> Ne le remplissez que pour forcer un projet, ex: `TARGET_PROJECT_PATH=C:\...\specs\001-course-management-system`

### 3. Activer le Ticket Agent pour votre LLM (OBLIGATOIRE)

Sans cette étape, le LLM ne sait pas qu'il doit mettre à jour le Kanban et les tickets resteront bloqués en `todo`.

**Copiez le contrat universel depuis `prompts/` (ou `agentdocx-speckit/adapters/`) — ne versionnez pas `.claude/` / `.github/` :**

| Votre CLI | Méthode la plus simple (recommandée) | Alternative | Copie depuis `prompts/` |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md` à la racine (lu comme skill) | `.claude/skills/universal-task-skill.md` | `cp prompts/claude-adapter.md CLAUDE.md` ou `mkdir -p .claude/skills && cp prompts/claude-adapter.md .claude/skills/universal-task-skill.md` |
| **Copilot** | `AGENTS.md` à la racine (lu comme skill, le plus simple) | `.github/skills/copilot-skill.md` ou `.github/copilot-skill.md` | `cp prompts/copilot-adapter.md AGENTS.md` ou `mkdir -p .github && cp prompts/copilot-adapter.md .github/copilot-instructions.md` |
| **Codex** | `AGENTS.md` | `.codex/skills/` | `cp prompts/universal-contract.md AGENTS.md` |
| **Cursor** | `.cursor/skills/universal-task-skill/SKILL.md` (ou `.cursor/rules/task-sync.mdc`, `.cursorrules` legacy) | `.cursor/rules/task-sync.mdc` | `mkdir -p .cursor/skills/universal-task-skill && cp prompts/cursor-adapter.md .cursor/skills/universal-task-skill/SKILL.md` |
| **Windsurf** | `.windsurf/skills/universal-task-skill/SKILL.md` (ou `.windsurfrules`) | `.windsurf/rules/task-sync.md` | `mkdir -p .windsurf/skills/universal-task-skill && cp prompts/windsurf-adapter.md .windsurf/skills/universal-task-skill/SKILL.md` |

> **Source unique :** `prompts/universal-contract.md` est le contrat maître. Tous les adapters en sont dérivés. Le fichier copié dit au LLM d'écrire **uniquement** dans `specs/{project}/.task_runtime/current-task.json` (atomique, avec FULL `tasks` map) pour déclencher `todo → in_progress → done`.

> [!NOTE]
> **Fichiers actifs à la racine :** `CLAUDE.md` (Claude, lu comme skill) et `AGENTS.md` (Copilot/Codex, lu comme skill) suffisent — pas besoin de `.claude/skills` ou `.github/copilot-instructions.md` séparés si vous utilisez la méthode simple. `prompts/` reste la bibliothèque source à copier.

Vérifiez que le fichier copié contient bien `specs/{project_name}/.task_runtime/current-task.json` (pas `.task_runtime` à la racine).

### 4. Environnement virtuel Python — pour votre dossier de test vide (obligatoire)

> [!IMPORTANT]
> Dans votre dossier de test vide après `git clone` (ex: `my-workspace/`), créez l'environnement avant d'installer les dépendances.

```powershell
# Depuis la racine du clone (my-workspace/Extension_GithubSpecKit)
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell — sur Mac/Linux: source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt          # ou pip install -r backend/requirements.txt si présent
```

### 5. Initialiser SpecKit — crée `.specify/` (obligatoire si absent)

```bash
specify init .
# Alternative : npx @github/spec-kit init .
# Vérifie : ls .specify/  et  ls .specify/memory/constitution.md
```
> Sans `specify init .`, les commandes `/speckit-specify` / `/speckit-plan` n'ont pas de mémoire.

### 6. Dépendances Node.js — Frontend + Extension (depuis votre dossier de test)

> [!WARNING]
> `tsc` / `cross-env` ne sont **pas** Python — ce sont des dépendances Node.js. Le `venv` Python ne les installe pas.

**Frontend (obligatoire pour `AgentDocx: Start Frontend`) :**
```powershell
# Depuis my-workspace/Extension_GithubSpecKit/frontend
cd frontend
npm install --legacy-peer-deps   # nécessaire à cause du conflit @nivo 0.79 vs 0.80
# Vérifie : npm run compile ne doit plus dire 'tsc not recognized'
cd ..
```

**Extension (seulement si vous recompilez l'extension) :**
```powershell
# Depuis my-workspace/Extension_GithubSpecKit/agentdocx-speckit
cd agentdocx-speckit
npm install              # installe tsc, esbuild, eslint (une seule fois)
npm run compile          # vérifie types + lint + bundle
# ou package complet :
npx @vscode/vsce package # génère agentdocx-speckit-0.0.7.vsix
cd ..
```

### 7. Lancement — 4 étapes, zéro terminal (sauf LLM)

| Étape | Action | Vérification |
|:---:|---|---|
| **1️⃣** | **Extension** : Installez `agentdocx-speckit-0.0.7.vsix` → `Ctrl+Shift+P` → `Developer: Reload Window` | `Output > AgentDocx Server` affiche `✔ [TicketManager] Dual watchers started` + `StatusWatcher Monitoring .../.task_runtime` |
| **2️⃣** | **Frontend** : `AgentDocx: Start Frontend` dans la palette (ou `cd frontend && npm start`) | `Output > AgentDocx Frontend` → `webpack compiled successfully` → `http://localhost:5000` |
| **3️⃣** | **Pipeline** : Modifiez un fichier dans `specs/{project}/` ou `AgentDocx: Trigger Pipeline` | `Output > AgentDocx Watcher` → `Pipeline exécuté avec succès` |
| **4️⃣** | **Kanban** : Dashboard → `Ingest Tasks` → lancez `Claude Code : /speckit-implement T009` | Kanban passe `todo → in_progress → done` en temps réel (`source:"watcher"` dans `Ticket Events`) |

> [!NOTE]
> Tout est piloté depuis l'extension — seul votre LLM (`ollama launch claude`, `cursor`, etc.) tourne en CLI, comme vous le faites déjà.
