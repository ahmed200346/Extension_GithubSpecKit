# 🚀 AgentDocx SpecKit — Extension QuickStart `0.0.4`

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.4-blue?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/VS_Code-1.125+-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="vscode" />
  <img src="https://img.shields.io/badge/Ticket_Agent-Dual_Watchers-blue?style=for-the-badge" alt="ticket" />
</p>

> [!NOTE]
> **Où se trouve ce dossier ?** Branche `extension` (`BrancheExtenion/Extension_GithubSpecKit/agentdocx-speckit/`) — complément de la branche `main` (`RepoSigma` → `backend/`, `frontend/`, `specs/`). Voir `README.md` racine → `🌿 Branches du repo`.

---

## 📦 What's in the folder — `0.0.4` Ticket Manager

* `package.json` — manifeste `agentdocx-speckit` `0.0.4` : 6 commandes (`Start Server`, `Start Watcher`, `Start Frontend`, `Trigger Pipeline`, ...)
* `src/extension.ts` — `activate()` + `initTaskRuntimes()` : crée `specs/{project}/.task_runtime/current-task.json` **vide** (`tasks:{}`) jusqu'à `tasks.md`, puis `29 todo`
* `scripts/python/` — `start_server.py` (`app.main:app` + `ticket_agent_lifespan` + auto `Base.metadata.create_all` pour `FinalDB`), `spec_watcher.py` (watchdog `specs/**/*.md` sans créer à la racine)
* `adapters/` — contrats `universal-contract.md` + 5 adapters (`claude`, `codex`, `copilot`, `cursor`, `windsurf`) tous en `specs/{project}/.task_runtime`
* `dist/extension.js` — bundle `esbuild` (généré par `npm run compile`)

---

## 🛠️ Setup

* `npm install` (recommandé : `amodio.tsl-problem-matcher`, `ms-vscode.extension-test-runner`)
* `npm run compile` → vérifie `src/extension.ts` + `spec_watcher.py` + `start_server.py` (0 errors, ~60 warnings `naming-convention` ignorables)

---

## ▶️ Get up and running

* `F5` → nouvelle fenêtre avec l'extension chargée → `Output` : `AgentDocx Server` (`[TicketManager] Dual watchers started` + `[Lifespan] Tables vérifiées`), `AgentDocx Watcher`, `AgentDocx Frontend`
* `Ctrl+Shift+P` → `AgentDocx: Start Server` / `Start Watcher` / `Start Frontend` (auto au `onStartupFinished`)
* Breakpoints dans `src/extension.ts` → Debug Console

---

## 🔄 Make changes — Ticket Manager

* Modifie `src/extension.ts` → `npm run compile` → `Ctrl+R` (Reload Window) → vérifie `specs/{project}/.task_runtime` reste vide jusqu'à `tasks.md`
* Modifie `scripts/python/spec_watcher.py` → pas de `mkdir` à la racine (garde-fou `BaseWatcher.run`)

---

## 🧪 Run tests

* `npm run watch` + Extension Test Runner → `src/test/extension.test.ts` (`**.test.ts`)

---

## 📚 Go further

* `npm run package` → `agentdocx-speckit-0.0.4.vsix` → `Extensions: Install from VSIX...`
* Pour publier : branche `extension` → merge dans `main` (voir `README.md` racine → `🌿 Branches`), puis `vsce publish`
