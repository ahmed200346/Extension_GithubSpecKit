# 🚀 Spec Kit

**Spec Kit** est un pipeline multi-agents avancé conçu pour la génération, l'enrichissement et la validation automatisée de spécifications d'architecture logicielle. Il transforme des documents techniques bruts en livrables structurés et certifiés.

---

## 📌 Structure & Présentation Générale

Le projet est organisé de manière modulaire pour séparer l'orchestration IA, l'interface de suivi et les mécanismes d'automatisation.

### 📂 Arborescence du Projet

- **`/backend`** : ⚙️ Pipeline d'enrichissement et d'évaluation. Propulsé par **FastAPI** et **LangGraph**, il orchestre la chaîne d'agents et gère la logique métier.
- **`/frontend`** : 🖥️ Dashboard **React** permettant le suivi en temps réel des exécutions, la visualisation des KPIs et le téléversement de nouveaux documents.
- **`/scripts`** : 🛠️ Watchers de fichiers et scripts d'automatisation qui font le pont entre le système de fichiers et le pipeline.
- **`/extensions`** : 🔌 Intégrations CLI SpecKit pour déclencher automatiquement le pipeline lors de la génération d'artefacts.
- **`/outputs`** : 📦 Dossier centralisé des livrables, organisé par projet :
  - `data/` : Données structurées JSON.
  - `markdowns/` : Fichiers enrichis.
  - `diagrams/` : Schémas générés.
  - `evaluations/` : Métriques de qualité des agents.
  - `pdf/` : Documents finaux versionnés.

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

## 🗄️ Traçabilité & Versioning BDD (PostgreSQL)

Le système s'appuie sur une base de données PostgreSQL pour garantir l'immuabilité des versions et la traçabilité complète de chaque modification.

### 📊 Modèle de Données
- **`projects`** : L'entité parente regroupant tous les artefacts et exécutions d'un projet spécifique.
- **`artifacts`** : Registre des fichiers sources surveillés dans `specs/`, incluant une empreinte **SHA-256** pour détecter précisément chaque modification.
- **`pipeline_runs`** : Journalisation exhaustive de chaque exécution, stockant les métriques **JSONB** détaillées pour chacun des 6 agents du pipeline.
- **`doc_versions`** : Registre immuable gérant le versioning dynamique des documents et le lien vers les fichiers PDF certifiés.

---

## 🔌 Extension VS Code SpecKit (Nouveau)

> **⚠️ En cours de développement** — Non publiée sur le Marketplace pour le moment.  
> **Branche dédiée** : [`extension`](https://github.com/ahmed200346/Extension_GithubSpecKit/tree/extension) pour le code complet, tests et documentation détaillée.

L'extension VS Code **AgentDocx SpecKit** remplace le dossier `scripts/` et offre une expérience intégrée :
- **Deux canaux de logs séparés** : `AgentDocx Server` (FastAPI) et `AgentDocx Watcher` (Python watchdog)
- **Démarrage automatique** au chargement de l'extension (F5)
- **Progression temps réel** visible dans le frontend (DocVersion créée dès le début, statut `pending` → `completed`)
- **Commandes palette** : `start_server`, `stopServer`, `startWatcher`, `stopWatcher`, `triggerPipeline`

> 📸 **Captures de l'extension** :  
> 1. **AgentDocx Watcher** — logs watchdog, détection fichiers, file d'attente  
>    ![AgentDocx Watcher](AgentDocxWatcher.png)  
> 2. **AgentDocx Server** — logs FastAPI, progression agents (Parsing → Summary → Glossary → Diagram → DocWriter → Layout), KPIs  
>    ![AgentDocx Server](AgentDocxServer.png)

---

## 🚀 Quick Start (Guide de Lancement)

Suivez ces étapes pour mettre en place l'environnement Spec Kit sur votre machine.

### ⚠️ Prérequis Base de Données
Avant de démarrer les services, assurez-vous impérativement que :
- **PostgreSQL** est lancé en arrière-plan.
- OU que **pgAdmin4** est ouvert avec une connexion active à la base de données du projet.

---

### 🛠️ Méthode 1 : Scripts Standalone (Version Actuelle — 4 Terminaux)

> **Approche classique** avec scripts Python standalone. Idéale pour développement sans l'extension.

#### Prérequis Base de Données
- PostgreSQL lancé (ou pgAdmin4 connecté)

#### Procédure de Lancement

**Étape 0 : Environnement Virtuel Python & Dépendances**
```bash
# Créer l'environnement virtuel
python -m venv env

# Activer l'environnement
# Sur Windows : env\Scripts\activate
# Sur Linux/Mac : source env/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

**Étape 1 : Démarrer le Backend FastAPI** (Terminal 1)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Étape 2 : Démarrer l'interface Frontend React** (Terminal 2)
```bash
cd frontend
npm install
npm start
```
> 💡 Si erreurs (dépendances, Node.js, `cross-env`, ports) → voir `configFrontEnd.pdf` à la racine.

**Étape 3 : Lancer le Watcher Temps Réel** (Terminal 3)
```bash
python scripts/python/spec_watcher.py
```

**Étape 4 : Exécuter Spec Kit via Claude Code** (Terminal 4)
```bash
ollama launch claude
```
*Utilisez les commandes Spec Kit (ex: `/speckit-specify`, `/doc-pipeline`) pour générer vos spécifications.*

---

### 🛠️ Méthode 2 : Extension VS Code (En Développement — Branche `extension`)

> **Remplace** le dossier `scripts/` par une extension VS Code intégrée.  
> **Branche** : [`extension`](https://github.com/ahmed200346/Extension_GithubSpecKit/tree/extension) — contient le code complet, tests et doc détaillée.

#### Architecture
- **Dossier `agentdocx-speckit/`** remplace `scripts/` (extension VS Code complète)
- **2 Terminaux pour le Frontend** : 
  1. `cd frontend && npm start` 
  2. `cd frontend && npm run dev` (si applicable)
- **Fenêtre Extension (F5)** : Ouvre une fenêtre **Extension Development Host** avec :
  - Canal **AgentDocx Watcher** — logs watchdog, détection fichiers, file d'attente
  - Canal **AgentDocx Server** — logs FastAPI, progression agents, KPIs
- **Terminal Claude Code** : pour commandes Speckit (`/speckit-specify`, `/doc-pipeline`)

#### Prérequis Supplémentaires
- **Ollama** installé + modèle `gemma4:31b-cloud` (`ollama pull gemma4:31b-cloud`)
- **Ollama serve** en cours d'exécution
- **Python 3.10+**, dépendances `scripts/python/requirements.txt` si test hors extension

#### ⚙️ Configuration VS Code Recommandée (pour l'extension)
Créez un fichier `.vscode/settings.json` à la racine du projet `agentdocx-speckit/` pour que l'extension Python reconnaisse le module `backend` utilisé par `spec_watcher.py` :

```json
{
  "python.analysis.extraPaths": [
    "./backend"
  ],
  "python.defaultInterpreterPath": "${workspaceFolder}/env/Scripts/python.exe"
}
```

> **Note** : Le chemin `./backend` permet à l'analyseur Python (Pylance) de résoudre les imports comme `from app.api.v1.endpoints import pipeline` utilisés dans `spec_watcher.py` qui lance le serveur via `start_server.py`.

#### Procédure de Lancement

**Étape 0 : Environnement Python (optionnel pour tests hors extension)**
```bash
python -m venv env
# Windows: env\Scripts\activate
# Linux/Mac: source env/bin/activate
pip install -r scripts/python/requirements.txt
```

**Étape 1 : Frontend React** (Terminal 1)
```bash
cd frontend
npm install
npm start
```

**Étape 2 : Ouvrir l'Extension Dev Host** (Terminal 2 — racine `agentdocx-speckit/`)
```bash
cd agentdocx-speckit
npm install
npm run compile
# Puis F5 dans VS Code pour ouvrir l'Extension Development Host
```
> L'extension démarre **automatiquement** serveur + watcher au chargement (voir canaux `AgentDocx Server` / `AgentDocx Watcher`).

**Étape 3 : Claude Code** (Terminal 3)
```bash
ollama launch claude
```
*Commandes disponibles : `/speckit-specify`, `/doc-pipeline`, `/speckit-plan`, etc.*

---

## 🔄 Résumé : Quelle méthode choisir ?

| Critère | Méthode 1 (Scripts) | Méthode 2 (Extension) |
|---------|---------------------|----------------------|
| **Statut** | Production | Développement (branche `extension`) |
| **Terminaux** | 4 | 3 (Frontend×2 + Claude) + Fenêtre Extension |
| **Logs** | Unifiés dans terminaux | Séparés : `AgentDocx Watcher` / `AgentDocx Server` |
| **Progression v2+** | Visible seulement à la fin | Temps réel (DocVersion `pending` → `completed`) |
| **Publication** | N/A | Pas encore sur Marketplace |

> Pour les détails complets sur l'extension : voir branche [`extension`](https://github.com/ahmed200346/Extension_GithubSpecKit/tree/extension) et documentation dans `agentdocx-speckit/README.md`.

---

### 📚 Ressources Complémentaires
- `configFrontEnd.pdf` — Dépannage Frontend
- `scripts/README.md` — Documentation scripts Python
- `agentdocx-speckit/README.md` — Doc extension (branche `extension`)
- `configFrontEnd.pdf` — Configuration Frontend détaillée

---

*Dernière mise à jour : 2026-07-30 — Spec Kit v0.0.2 (Extension en développement)*