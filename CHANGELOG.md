# Change Log

Toutes les modifications notables apportées à l'extension **AgentDocx_SpecKit** seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [0.0.3] - 2026-08-21

### Ajouté
* **Frontend React intégré** : Lancement/arrêt automatique du frontend React (port 5000) via `npm start`
* **Canal de sortie dédié** : `AgentDocx Frontend` pour logs temps réel du frontend React
* **Détection compilation** : Notification automatique `Compiled successfully!` avec boutons **Ouvrir** (http://localhost:5000) et **Copier URL**
* **Commandes frontend** : `agentdocx-speckit.start_frontend` / `agentdocx-speckit.stop_frontend`
* **Support Windows** : `shell: true` pour spawn `npm.cmd` sur Windows
* **Auto-démarrage frontend** : Frontend lancé automatiquement avec serveur et watcher au chargement

### Modifié
* `extension.ts` : 3 canaux sortie (Server/Watcher/Frontend), spawnOptions frontend avec `shell: true` Windows
* `package.json` : Dépendance `cross-env` pour PORT=5000
* Auto-démarrage étendu : Serveur + Watcher + Frontend au chargement

### Corrigé
* Port 5000 occupé : Détection processus existant + logs CWD
* Logs frontend : Capture ligne par ligne stdout/stderr, détection `Compiled successfully!`
* Notification VS Code avec actions **Ouvrir** (navigateur) / **Copier URL**

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