# Welcome to AgentDocx SpecKit Extension

## What's in the folder

* This folder contains all of the files necessary for your extension.
* `package.json` - this is the manifest file in which you declare your extension and command.
* `src/extension.ts` - this is the main file where you will provide the implementation of your command.
* `scripts/python/` - Scripts Python pour le serveur FastAPI et le watcher

## Architecture

L'extension gère **3 processus** au démarrage automatique :
1. **Serveur FastAPI** (port 8000) - Pipeline LangGraph pour génération docs
2. **Watcher Python** - Surveillance `specs/` avec watchdog
3. **Frontend React** (port 5000) - Dashboard React pour visualisation

## Canaux de sortie (Output Channels)

* **AgentDocx Server** - Logs FastAPI / Pipeline
* **AgentDocx Watcher** - Logs Watchdog / File queue
* **AgentDocx Frontend** - Logs React / Webpack / Compilation

## Commandes disponibles

| Commande | Description |
|---|---|
| `agentdocx-speckit.start_server` | Démarre FastAPI (8000) |
| `agentdocx-speckit.stopServer` | Arrête FastAPI |
| `agentdocx-speckit.startWatcher` | Démarre Watcher specs/ |
| `agentdocx-speckit.stopWatcher` | Arrête Watcher |
| `agentdocx-speckit.start_frontend` | Démarre React (5000) |
| `agentdocx-speckit.stop_frontend` | Arrête React |
| `agentdocx-speckit.triggerPipeline` | Déclenche pipeline via /health |

## Setup & Development

```bash
# Installer dépendances
npm install

# Compiler
npm run compile

# Lancer en dev (F5 dans VS Code)
```

## Prérequis

* **Python 3.10+** + `ollama serve` + `gemma4:31b-cloud`
* **Node.js** + `npm install` dans `workspace/frontend/`
* Workspace doit contenir dossiers `backend/`, `frontend/`, `specs/`

## Canaux de sortie

Ouvrir : **View > Output** → Dropdown pour basculer :
- `AgentDocx Server`
- `AgentDocx Watcher`
* `AgentDocx Frontend` ← **NOUVEAU** : logs React, détection `Compiled successfully!`

## Debugging

* `F5` : Nouvelle fenêtre avec extension chargée
* Breakpoints dans `src/extension.ts`
* Logs dans Output channels (pas Debug Console)

## Notifications Frontend

Quand le frontend compile (`Compiled successfully!`), notification VS Code :
- **Ouvrir** → http://localhost:5000
- **Copier URL** → Presse-papiers

## Packaging

```bash
npm install -g @vscode/vsce
npm run compile
vsce package
# → agentdocx-speckit-0.0.3.vsix
```

## Go further

* [Bundling](https://code.visualstudio.com/api/working-with-extensions/bundling-extension)
* [Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
* [CI/CD](https://code.visualstudio.com/api/working-with-extensions/continuous-integration)