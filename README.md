# AgentDocx SpecKit

**AgentDocx SpecKit** est une extension VS Code conçue pour le suivi et le déclenchement du pipeline de documentation **Spec Kit**.

## 🚀 Fonctionnalités

* **Serveur FastAPI** : Démarrage/arrêt du serveur FastAPI (port 8000) depuis VS Code
* **Watcher Python** : Surveillance en temps réel du dossier `specs/` avec détection de changements
* **Pipeline Spéc Kit** : Déclenchement et suivi du pipeline de documentation (LangGraph agents)
* **Sortie en temps réel** : Deux canaux de sortie dédiés (`AgentDocx Server` et `AgentDocx Watcher`)
* **Intégration fluide** : Commandes accessibles depuis la palette de commandes (`Ctrl+Shift+P` / `Cmd+Shift+P`)
* **Démarrage automatique** : Serveur + Watcher lancés automatiquement au chargement de l'extension

## 🛠️ Commandes disponibles

| Commande | Intitulé | Description |
| :--- | :--- | :--- |
| `agentdocx-speckit.start_server` | `AgentDocx SpecKit: Démarrer le Serveur FastAPI` | Lance le serveur FastAPI (port 8000) |
| `agentdocx-speckit.stopServer` | `AgentDocx SpecKit: Arrêter le Serveur FastAPI` | Arrête le serveur FastAPI |
| `agentdocx-speckit.startWatcher` | `AgentDocx SpecKit: Démarrer le Watcher Python` | Lance le watcher de fichiers `specs/` |
| `agentdocx-speckit.stopWatcher` | `AgentDocx SpecKit: Arrêter le Watcher Python` | Arrête le watcher |
| `agentdocx-speckit.triggerPipeline` | `AgentDocx SpecKit: Déclencher la régénération` | Déclenche le pipeline via `/health` |

## 📦 Installation, Développement & Publication

### 🛠️ Mode Développement (Lancement rapide)
1. Clonez le dépôt dans votre répertoire local.
2. Installez les dépendances :
   ```bash
   npm install
   ```
3. Compilez l'extension :
   ```bash
   npm run compile
   ```
4. Lancez l'extension en mode développement (`F5` dans VS Code).

### 🏗️ Construction & Packaging (Génération du .vsix)
Pour générer le fichier `.vsix` distribuable, vous devez utiliser l'outil `vsce` :

1. Installer l'outil de packaging VS Code (une seule fois) :
   ```bash
   npm install -g @vscode/vsce
   ```
2. Générer le fichier `.vsix` :
   ```bash
   vsce package
   # → Génère le fichier .vsix à la racine du projet
   ```

### 🚀 Publication sur le Marketplace
Pour publier l'extension sur le VS Code Marketplace (nécessite un Personal Access Token Azure DevOps) :

```bash
vsce publish -p <VOTRE_PAT>
# ou
vsce publish  # mode interactif
```
> 📖 Pour créer un PAT : https://dev.azure.com/ → User Settings → Personal Access Tokens → New Token  
> Scopes : **Marketplace > Manage (Publish, Manage)**


## 🐍 Prérequis Python

* Python 3.10+
* Ollama installé et modèle `gemma4:31b-cloud` téléchargé (`ollama pull gemma4:31b-cloud`)
* `ollama serve` en cours d'exécution

## 📁 Structure du projet

```
agentdocx-speckit/
├── src/
│   ├── extension.ts          # Point d'entrée de l'extension
│   └── test/
│       └── extension.test.ts # Tests d'intégration
├── scripts/
│   ├── python/
│   │   ├── start_server.py   # Lancement serveur FastAPI + uvicorn
│   │   ├── spec_watcher.py   # Watchdog watcher pour specs/
│   │   ├── run_pipeline_cli.py # CLI manuel pour pipeline
│   │   └── spec_watcher.py   # Watcher avec debounce + retry
│   └── bash/
│       ├── start-watcher.sh
│       └── create-doc-pipeline.sh
├── src/test/extension.test.ts
├── dist/                     # Build output (esbuild)
├── package.json
├── tsconfig.json
├── esbuild.js
├── CHANGELOG.md
└── README.md
```

## 🔄 Workflow complet

```text
[ F5 / Ctrl+Shift+P > start_server ] 
    │
    ▼
[ Serveur FastAPI :8000 démarré ]
[ Watcher specs/ démarré ]
    │
    ▼
[ Édition spec.md / requirements.md dans specs/ ]
    │
    ▼
[ Watcher détecte changement → Stabilisation → File d'attente ]
    │
    ▼
[ Pipeline LangGraph : Parsing → Summary → Glossary → Diagram → DocWriter → Layout ]
    │
    ▼
[ PDF généré dans outputs/<project>/ ]
```

## 📚 Documentation

* [Scripts Python](./scripts/README.md) - Documentation détaillée des scripts Python
* [CHANGELOG](./CHANGELOG.md) - Historique des versions
* [API Endpoints](./docs/api.md) - Documentation de l'API FastAPI (si disponible)

## 🤝 Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amazing-feature`)
3. Committez (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

## 📄 Licence

MIT License - voir [LICENSE](LICENSE) pour plus de détails.