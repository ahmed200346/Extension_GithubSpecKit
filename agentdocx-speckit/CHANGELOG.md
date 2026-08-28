# Change Log

Toutes les modifications notables apportées à l'extension **AgentDocx_SpecKit** seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [0.0.5] - 2026-08-28

### Corrigé
* **Script path** : correction du chemin `file:` dans `extension.yml` — `scripts/bash/create-doc-pipeline.sh` → `agentdocx-speckit/scripts/bash/create-doc-pipeline.sh` (le script est dans le sous-dossier `agentdocx-speckit/`, pas à la racine).
* **Required Tools** : ajout des versions minimales requises dans `extension.yml` — Python >=3.10, Node.js >=18, PostgreSQL >=12.

### Modifié
* `extension.yml` : version bump `0.0.4 → 0.0.5`, ajout de la section `requires.tools`.
* `package.json` : version bump `0.0.4 → 0.0.5`.

---

## [0.0.4] - 2026-08-26

### Ajouté
* **Catégorie Marketplace `Integration`** : le manifeste VS Code classe AgentDocx comme extension d'intégration entre Spec Kit, les CLI d'agents, FastAPI, React et le Ticket Agent.
* **TicketMetrics** : documentation et affichage du score de conformité, du verdict, de la couverture des exigences, de la qualité du code, de l'architecture et de la traçabilité.
* **Frontend intégré** : l'extension lance automatiquement React et centralise ses logs dans le canal `AgentDocx Frontend`, ce qui laisse un seul terminal à l'utilisateur pour son CLI d'agent.

### Modifié
* `package.json` : catégorie VS Code changée de `Other` vers `Integration` et version stabilisée à `0.0.4`.
* `README.md` et `vsc-extension-quickstart.md` : alignement de la version, de `FinalDB`, des commandes et du flux frontend intégré.

---

## [0.0.3] - 2026-08-25

### Ajouté
* **Ticket Manager — Dual Watchers** : `StructureWatcher` (surveille `specs/{project}/tasks.md`) + `StatusWatcher` (surveille `specs/{project}/.task_runtime/current-task.json`) via `ticket_agent_lifespan` dans `backend/app/main.py`. `StatusWatcher` génère des événements `source:"watcher"` pour transitions `todo → in_progress → done`.
* **Universal Ticket Agent Protocol** : Tous les adapters (`CLAUDE.md`, `AGENTS.md`, `prompts/universal-contract.md`, `prompts/claude|codex|copilot|cursor|windsurf-adapter.md`, `agentdocx-speckit/adapters/*`) pointent désormais vers `specs/{project}/.task_runtime/current-task.json` (isolation par projet, plus de dossier racine `.task_runtime`).
* **Auto-Init per-project** : `extension.ts` `initTaskRuntimes()` et `spec_watcher.py` créent `specs/{project}/.task_runtime/current-task.json` isolé par projet.
* **Auditor** : Seuil 75.0, `auto_audit_on_done` déclenché sur transition `→ done`.

### Modifié
* `backend/app/services/ticket_ingestion.py` : `_write_current_task()` n'écrit plus que vers le path project-specific + support `utf-8-sig` (BOM).
* `backend/app/api/v1/endpoints/pipeline.py` : `GET /pipeline/task-state/{project}` ne lit plus que le path project-specific.
* `backend/app/api/v1/endpoints/tickets.py` : `POST /ticket-agent/write-current-task` exige `project_name` et n'écrit plus vers la racine.
* `backend/app/agents/ticket_agent/watcher.py` : `StructureWatcher` surveille désormais `specs/{project}` directement (correction double `specs` → `specs/{project}/specs`).
* `agentdocx-speckit/scripts/python/start_server.py` : Ajout `logging.basicConfig` INFO + lancement via `app.main:app` avec `app_dir=backend` pour garantir le lifespan TicketManager.
* `agentdocx-speckit/package.json` : bump `0.0.2 → 0.0.3`.

### Corrigé
* Suppression du dossier racine `.task_runtime` qui causait des conflits entre projets et des erreurs `Unexpected UTF-8 BOM`.
* Chemins des exemples atomiques (bash `cat > ...` / `mv ...`) dans tous les adapters corrigés vers `specs/{project}/.task_runtime`.
* Helper Python `write_task_status()` dans `CLAUDE.md` / `claude-adapter.md` corrigé vers `Path(f"specs/{project}/.task_runtime")`.
* `WebSocket 403` documenté comme non bloquant (polling fallback 15s).

---

## [1.0.4] - 2026-08-24

### Ajouté
* **Auto-Init .task_runtime** : L'extension crée désormais automatiquement le dossier `.task_runtime` et le fichier `current-task.json` pour tous les projets détectés dans `specs/` dès l'activation, sans attendre la création de `tasks.md`.
* **Support Protocol Ticket Agent** : Alignement complet avec le protocole de synchronisation Kanban pour Claude Code.

### Modifié
* `extension.ts` : Refonte de la fonction `initTaskRuntimes` pour supprimer la condition restrictive sur `tasks.md`.
* `README.md` : Mise à jour complète pour refléter la version 1.0.4 et les nouvelles fonctionnalités.
* `LICENSE.md` : Ajout de la licence MIT au nom d'Ahmed Aziz Ammar.

### Corrigé
* Problème de création du dossier de runtime qui empêchait la synchronisation avec le tableau Kanban lors du premier lancement d'un projet.

---

## [0.0.2] - 2026-07-30

### Ajouté
* **Deux canaux de sortie distincts** : `AgentDocx Server` et `AgentDocx Watcher` pour une traçabilité optimale
* **Démarrage automatique** : Serveur FastAPI + Watcher Python lancés au chargement de l'extension
* **Watcher robuste** : Debounce 1s, stabilisation fichier, vérification BDD avant envoi, file d'attente séquentielle
* **Endpoints pipeline** : `/status`, `/check-file`, `/run`, `/health`, `/documents` pour frontend
* **Progression temps réel** : DocVersion créée au début du pipeline (statut "pending") pour affichage immédiat dans frontend
* **Diagram Agent corrigé** : Nettoyage Mermaid robuste (espaces dans nœuds décision, guillemets, flèches)
* **Upload vers StageTalan/specs** : Fichiers sauvegardés sous `StageTalan/specs/<project>/` (pas `backend/specs/`)
* **DiagramExporterTool** : Auto-quoting nœuds, correction flèches, header flowchart auto, nettoyage pré-rendu

### Modifié
* `extension.ts` : 2 canaux sortie, spawnOptions avec PYTHONPATH, auto-start serveur+watcher
* `pipeline.py` : DocVersion créée au début (pending), mise à jour à la fin, upload vers BASE_DIR/specs
* `diagram_tools.py` : Pré-nettoyage espaces délimiteurs, header flowchart auto, regex nœuds améliorée
* `spec_watcher.py` : Debounce 1s, wait_for_server au démarrage, is_file_already_in_db avec retry
* `db_service.py` : `create_doc_version_pending()`, `save_successful_run` met à jour DocVersion existante
* `pipeline.py` : `create_doc_version_pending` appelé avant pipeline, `doc_version_id` passé au state LangGraph

### Corrigé
* Erreur Mermaid `{ "Label" }` → `{"Label"}` (espaces dans nœuds décision)
* Erreur Mermaid `[ "Label" ]` → `["Label"]` et `( "Label" )` → `("Label")`
* Doublons artifacts (check-file créait artifact, puis upload en recréait un) → check-file lecture seule, hash immédiat à la création
* Port 8000 occupé au reload → `reload=False` dans start_server.py
* Check-file timeout 3s → retry serveur non prêt (watch_for_server au démarrage watcher)

## [0.0.1] - Version Initiale

### Ajouté
* Initialisation du projet d'extension VS Code pour AgentDocx SpecKit.
* Configuration de la chaîne de compilation avec `esbuild`, `typescript` et `eslint`.
* Enregistrement de la commande de base `agentdocx-speckit.helloWorld`.
