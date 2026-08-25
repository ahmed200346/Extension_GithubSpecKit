# 🚀 Spec Kit — AgentDocx Ticket Manager

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.4-blue?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="fastapi" />
  <img src="https://img.shields.io/badge/PostgreSQL-StageTal-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="postgres" />
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
| **🧩 Extension VS Code** | [`agentdocx-speckit/README.md`](agentdocx-speckit/README.md) | Auto-init `.task_runtime`, Dual Watchers, `start_server.py`, `spec_watcher.py`, packaging `0.0.3` |
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

Le système s'appuie sur une base de données PostgreSQL pour garantir l'immuabilité des versions et la traçabilité complète de chaque modification.

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
        VARCHAR source_path
        VARCHAR title
        TEXT description
        VARCHAR status
        INTEGER position
        VARCHAR checkbox_state
        VARCHAR file_hash
        DATETIME created_at
        DATETIME updated_at
    }
    artifacts ||--o{ tickets : references
    projects ||--o{ tickets : references
    ticket_events {
        UUID id "PK"
        UUID ticket_id "FK"
        VARCHAR event_type
        VARCHAR author_type
        JSONB payload
        DATETIME created_at
    }
    tickets ||--o{ ticket_events : references
    ticket_comments {
        UUID id "PK"
        UUID ticket_id "FK"
        VARCHAR author_type
        TEXT body
        DATETIME created_at
    }
    tickets ||--o{ ticket_comments : references
```

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

1. Téléchargez `agentdocx-speckit-0.0.3.vsix`.
2. `Ctrl+Shift+P` $\rightarrow$ **Extensions: Install from VSIX...**

---

## 🌿 Branches du repo — où se trouve quoi ?

> **Depuis `0.0.4`, tout est dans `main` au même niveau** (plus besoin de 2 clones) :

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
- **PostgreSQL** : Lancé avec la base `speckit` (ou `StageTal` selon votre `.env`).
- **LLM Provider** : Ollama lancé (`ollama serve`) ou clés API configurées dans `.env` (Gemini, NVIDIA).
- **Node.js 18+** et **Python 3.10+**.

### 2. Configuration `.env` — le cœur du projet (DB inchangée)

> [!IMPORTANT]
> Copiez `backend/.env` à la racine **ou** créez un nouveau `.env` à la racine. **Ne modifiez jamais `DATABASE_URL`** si `StageTal` est déjà créée.

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

**Copiez le contrat universel vers la racine du projet cloné selon votre IDE :**

| Votre LLM / IDE | Fichier à copier | Commande (depuis la racine du clone) |
|---|---|---|
| **Claude Code (Ollama)** | `CLAUDE.md` | `cp prompts/claude-adapter.md CLAUDE.md` ou `cp agentdocx-speckit/adapters/claude-adapter.md CLAUDE.md` puis suivez les instructions d'injection dans le fichier |
| **Codex** | `AGENTS.md` | `cp prompts/universal-contract.md AGENTS.md` (ou utilisez `agentdocx-speckit/adapters/codex-adapter.md`) |
| **Cursor** | `.cursorrules` | `cp prompts/cursor-adapter.md .cursorrules` |
| **Windsurf** | `.windsurfrules` | `cp prompts/windsurf-adapter.md .windsurfrules` |
| **Copilot** | `.github/copilot-instructions.md` | `cp prompts/copilot-adapter.md .github/copilot-instructions.md` |

> **Source unique :** `prompts/universal-contract.md` est le contrat maître. Tous les adapters en sont dérivés. Le fichier copié dit au LLM d'écrire **uniquement** dans `specs/{project}/.task_runtime/current-task.json` (atomique, avec FULL `tasks` map) pour déclencher `todo → in_progress → done`.

> [!NOTE]
> **Fichiers actifs à la racine (recréés) :** `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md` — ce sont **ces fichiers à la racine** que les LLM lisent, pas ceux dans `prompts/` (qui n'est que la bibliothèque source à copier).

Vérifiez que le fichier copié contient bien `specs/{project_name}/.task_runtime/current-task.json` (pas `.task_runtime` à la racine).

### 4. Environnement virtuel Python — pour `demo/` vide (obligatoire)

> [!IMPORTANT]
> Dans votre dossier `demo/` vide après `git clone`, créez l'environnement avant d'installer les dépendances.

```powershell
# Depuis la racine du clone (demo/Extension_GithubSpecKit)
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

### 6. Lancement — 4 étapes, zéro terminal (sauf LLM)

| Étape | Action | Vérification |
|:---:|---|---|
| **1️⃣** | **Extension** : Installez `agentdocx-speckit-0.0.3.vsix` → `Ctrl+Shift+P` → `Developer: Reload Window` | `Output > AgentDocx Server` affiche `✔ [TicketManager] Dual watchers started` + `StatusWatcher Monitoring .../.task_runtime` |
| **2️⃣** | **Frontend** : `AgentDocx: Start Frontend` dans la palette (ou `cd frontend && npm start`) | `Output > AgentDocx Frontend` → `webpack compiled successfully` → `http://localhost:5000` |
| **3️⃣** | **Pipeline** : Modifiez un fichier dans `specs/{project}/` ou `AgentDocx: Trigger Pipeline` | `Output > AgentDocx Watcher` → `Pipeline exécuté avec succès` |
| **4️⃣** | **Kanban** : Dashboard → `Ingest Tasks` → lancez `Claude Code : /speckit-implement T009` | Kanban passe `todo → in_progress → done` en temps réel (`source:"watcher"` dans `Ticket Events`) |

> [!NOTE]
> Tout est piloté depuis l'extension — seul votre LLM (`ollama launch claude`, `cursor`, etc.) tourne en CLI, comme vous le faites déjà.
