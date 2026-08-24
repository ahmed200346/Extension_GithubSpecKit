# 🚀 Spec Kit

**Spec Kit** est un pipeline multi-agents avancé conçu pour la génération, l'enrichissement et la validation automatisée de spécifications d'architecture logicielle. Il transforme des documents techniques bruts en livrables structurés, certifiés et professionnels.

---

## 📌 Architecture Générale du Projet

Le projet adopte une architecture modulaire où l'IA n'est pas seulement un "chat", mais un ensemble d'agents spécialisés orchestrés comme un flux de travail industriel.

### 📂 Arborescence & Rôles
- **`/backend`** : ⚙️ **Le Moteur**. Propulsé par **FastAPI** et **LangGraph**. Il contient la logique d'orchestration, les services d'agents et la gestion des providers LLM.
  - 📘 *Architecture Technique* : Consultez le [README du backend](backend/README.md) pour les détails sur le `llm_client` et les services.
- **`/frontend`** : 🖥️ **Le Poste de Contrôle**. Dashboard **React** pour le monitoring temps réel, la visualisation des KPIs et la gestion des documents.
- **`/specs`** : 📄 **La Source**. Dossier surveillé contenant les spécifications Markdown brutes et le fichier `tasks.md`.
- **`/outputs`** : 📦 **L'Usine**. Stockage centralisé des livrables (JSON, Markdown enrichis, PDF versionnés).

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

## 📋 Agent JIRA (Kanban Ticket Sync)

L'**Agent JIRA** assure une synchronisation bidirectionnelle et automatique entre l'état d'avancement technique du projet (via Copilot) et un tableau Kanban de suivi (To Do / In Progress / Done).

### 🔄 Flux de Synchronisation
#### 1. Ingestion des Tâches (`POST /api/v1/ingest`)
L'ingestion permet d'initialiser ou de rafraîchir la liste des tickets en base de données à partir du fichier de spécifications.
- **Processus** : Le backend analyse `specs/tasks.md` $\rightarrow$ crée les tickets (`T001`, `T002`, ...) avec le statut initial `todo`.

#### 2. Synchronisation de Statut en Temps Réel
Le passage d'un ticket à l'état "en cours" ou "terminé" est strictement piloté par l'activité de Copilot via le fichier `.task_runtime/current-task.json`.

### 🤖 Contrat Copilot (`.github/copilot-instructions.md`)
Pour garantir cette synchronisation, GitHub Copilot suit un protocole strict :
- **Avant chaque tâche** : Écrit `status: "in_progress"`.
- **Après chaque tâche** : Écrit `status: "done"`.
- **État Global** : Inclut un instantané complet de toutes les tâches pour éviter toute perte de synchronisation.

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

- **Logs Intégrés** : Deux canaux dans la vue Output (`AgentDocx Server` et `AgentDocx Watcher`).
- **Automatisation** : Démarrage automatique du serveur et du watcher au chargement.
- **Commandes Palette** : `triggerPipeline`, `startServer`, etc.

### 📦 Installation (via .vsix)
1. Téléchargez `agentdocx-speckit-0.0.2.vsix`.
2. `Ctrl+Shift+P` $\rightarrow$ **Extensions: Install from VSIX...**

---

## 🚀 Quick Start (Guide de Lancement)

### 1. Prérequis
- **PostgreSQL** : Lancé avec la base `speckit`.
- **LLM Provider** : Ollama lancé ou clés API configurées dans `.env`.

### 2. Configuration `.env` (Repo Source)
```dotenv
DATABASE_URL=postgresql://user:password@localhost:5432/speckit
TARGET_PROJECT_PATH=C:\chemin\vers\votre-projet-enfant
LLM_PROVIDER=ollama
OLLAMA_MODEL=gemma4:31b-cloud
```

### 3. Lancement
1. **Frontend** : `cd frontend && npm start`
2. **Extension** : Activez l'extension dans VS Code.
3. **Pipeline** : Modifiez un fichier dans `specs/` ou utilisez la commande `Trigger Pipeline`.
