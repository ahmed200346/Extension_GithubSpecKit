# 📋 Protocol Universel Spec Kit - Instruction Skill

## Statut : Skill officiel pour Claude Code & tous les frameworks

Ce fichier définit le protocole universel que TOUT CLI (Copilot, Aider, Claude Code, Cursor, Codex, Windurfr) doit suivre pour synchroniser l'état des tâches avec Spec Kit.

Il est conçu pour être lu en tant que **Skill** par Claude Code, et utilisé directement par les autres frameworks.

---

## 🎯 Fichier cible : .task_runtime/current-task.json

Tous les CLIs doivent écrire vers ce chemin (l'extension crée le dossier automatiquement) :

```
.task_runtime/current-task.json
```

**Création automatique par l'extension AgentDocx :**
- Au premier lancement, `src/extension.ts` créé `.task_runtime/` racine
- Par projet : `specs/{project_name}/.task_runtime/`
- Fichier `config.json` inclus si absent

---

## 📄 Format JSON requis (EXACT)

Tous les CLIs doivent produire un JSON valide avec ces 5 champs :

| Champ | Requis | Description |
|-------|--------|-------------|
| `task_id` | **OBLIGATOIRE** | ID ticket depuis `tasks.md` (ex: `T001`, `T004`) |
| `file` | **OBLIGATOIRE** | Chemin du fichier principal en cours de modification (relatif ou absolu) |
| `status` | **OBLIGATOIRE** | `"in_progress"` (début) ou `"done"` (fin) |
| `project_name` | **OBLIGATOIRE** | Nom du projet (correspondre au dossier `specs/{nom}`) |
| `updated_at` | **OBLIGATOIRE** | Date UTC ISO8601 (`2026-08-14T10:30:00.000Z`) |
| `tasks` | **OBLIGATOIRE** | **TABLEAU COMPLET** : Tous les IDs tasks → statut ({`T001`: `in_progress`, `T002`: `todo`}) |

### Exemple complet :

```json
{
  "task_id": "T004",
  "file": "src/auth/routes.py",
  "status": "in_progress",
  "project_name": "001-cli-todo-manager",
  "updated_at": "2026-08-14T10:30:00.000Z",
  "tasks": {
    "T001": "done",
    "T002": "done",
    "T003": "done",
    "T004": "in_progress",
    "T005": "todo"
  }
}
```

⚠️ **Règle d'or :** Le champ `tasks` doit contenir la valeur réelle de TOUTES les tasks de `tasks.md`. C'est ce qui permet au backend de "rattraper" le retard si le serveur n'était pas démarré pendant que le CLI travaillait sur plusieurs tâches d'affilée.

---

## 🤖 Comment chaque framework "Skill" lit ce fichier

### Claude Code (en tant que Skill)

1. **Placement :** Déposez `INSTRUCTIONS/instruction.md` dans `.claude/skills/` de votre projet
2. **Déclenchement :** Claude Code lit ce fichier au démarrage comme compétence officielle
3. **Action avant tâche :** Avant de commencer `T004`, Claude écrit `.task_runtime/current-task.json` avec `status: "in_progress"` + `tasks: {...}`
4. **Action après tâche :** Après completion, met à jour `status: "done"` + `tasks: {...}` mis à jour
5. **Fichier de compétence (.claude/skills/universal-task-skill.md) :**

```markdown
# Skill : Protocol Universel Spec Kit

Lue `INSTRUCTIONS/instruction.md` du repo racial.

**Avant chaque tâche :**
1. Copier `task_id` et `tasks` depuis `specs/tasks.md`
2. Écrire `.task_runtime/current-task.json` :
```json
{
  "task_id": "T004",
  "file": "src/auth/routes.py",
  "status": "in_progress",
  "project_name": "001-cli-todo-manager",
  "updated_at": now().toISOString(),
  "tasks": { "T001": "done", "T002": "done", "T003": "done", "T004": "in_progress", "T005": "todo" }
}
```

**Après chaque tâche :**
1. Mettre `status: "done"`
2. Mettre à jour `tasks[T004]` = `"done"`
3. Laisser les autres inchangés

**Pourquoi ce skill ?**
- Compatible avec tous les frameworks
- Le backend AgentDocx détectera le changement et synchronisera la BDD
- Format JSON stable, pas de rupture de contrat

**Dépendance :** Nécessite l'extension VS Code AgentDocx SpecKit démarrée.
```

### GitHub Copilot

1. Copier le contenu de `INSTRUCTIONS/instruction.md` dans `.github/copilot-instructions.md` (ou laisser l'extension le générer automatiquement)
2. Copilot lit ces instructions et écrit `current-task.json` selon le format ci-dessus
3. L'extension `src/extension.ts` génère auto `.github/copilot-instructions.md` au premier lancement

### Aider

1. Créer un hook Python dans `.aider/task_hook.py` :
```python
#!/usr/bin/env python3
import json, os
from pathlib import Path
from datetime import datetime

def on_task_start(task_id, file_path, all_tasks):
    project_name = os.getenv("PROJECT_NAME", Path.cwd().name)
    # Toujours sous specs/{project}/.task_runtime — jamais à la racine
    runtime = Path(f"specs/{project_name}/.task_runtime")
    runtime.mkdir(parents=True, exist_ok=True)
    data = {
        "task_id": task_id,
        "file": file_path,
        "status": "in_progress",
        "project_name": project_name,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "tasks": all_tasks
    }
    (runtime / "current-task.json").write_text(json.dumps(data, indent=2))

def on_task_end(task_id, file_path, all_tasks):
    project_name = os.getenv("PROJECT_NAME", Path.cwd().name)
    runtime = Path(f"specs/{project_name}/.task_runtime")
    runtime.mkdir(parents=True, exist_ok=True)
    data = {
        "task_id": task_id,
        "file": file_path,
        "status": "done",
        "project_name": project_name,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "tasks": all_tasks
    }
    (runtime / "current-task.json").write_text(json.dumps(data, indent=2))
```

### Cursor

1. Créer une règle MDC `.cursor/rules/task-sync.mdc` :
```markdown
---
alwaysApply: true
---
# Task Sync Rule

Quand vous commencez une tâche depuis `specs/tasks.md` :
1. Lisez `INSTRUCTIONS/instruction.md` pour le format JSON
2. Écrivez `.task_runtime/current-task.json` avec `status: "in_progress"` et `tasks: {...}`

Quand vous finissez :
1. Mettez à jour `status: "done"`
2. Mettez à jour `tasks[CURRENT_TASK]` = `"done"`
```

### Codex / OpenAI

1. Utilisez un script bash/python qui lit `INSTRUCTIONS/instruction.md` pour le format
2. Le script écrit `.task_runtime/current-task.json` avant/après chaque tâche

---

## 📁 Emplacement dans le repo (branche `extension`)

```
agentdocx-speckit/
├── INSTRUCTIONS/          ← **Nouveau** ← Copiez ce dossier vers vos projets
│   └── instruction.md     ← **Protocol universel** (compétence Claude Code)
│
├── adapters/              ← **Reste ici** ← Documentation framework par framework
│   ├── copilot-adapter.md
│   ├── claude-adapter.md
│   ├── codex-adapter.md
│   ├── cursor-adapter.md
│   ├── universal-contract.md
│   └── windsurf-adapter.md
│
├── src/                   ← Code extension VS Code
├── backend/               ← Serveur FastAPI
├── frontend/              ← Dashboard React
└── ...
```

---

## 👨‍💻 Pour les développeurs (Workflow)

### Étape 1 : Cloner la branche extension
```bash
git clone -b extension https://github.com/ahmed200346/Extension_GithubSpecKit.git
```

### Étape 2 : Copier le dossier INSTRUCTIONS vers votre projet
```bash
# Option A : Copie directe
cp -R ./agentdocx-speckit/INSTRUCTIONS/ ./mon-projet/

# Option B : Via l'extension
# L'extension détecte et affiche un message au premier lancement :
# "[INFO] Protocol universel INSTRUCTIONS détecté - copiez ce dossier vers votre projet"
```

### Étape 3 : Activer selon votre CLI

| CLI | Action |
|-----|--------|
| **Claude Code** | Le skill se charge automatiquement depuis `.claude/skills/` |
| **Copilot** | L'extension génère `.github/copilot-instructions.md` |
| **Aider** | Utilisez le hook Python ci-dessus |
| **Cursor** | Utilisez la règle MDC ci-dessus |
| **Codex** | Adaptez un script pour lire le format JSON |

### Étape 3 : Commencer à coder

1. Votre CLI lit `specs/tasks.md` et sélectionne la tâche T004
2. Le CLI écrit `.task_runtime/current-task.json` selon le format ci-dessus
3. L'extension AgentDocx Server affiche le log
4. Le watcher backend détecte le changement → synchronise la BDD → frontend Kanban se met à jour

---

## 🛠️ Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| `current-task.json` introuvable | CLI n'écrit pas vers ce chemin | Vérifiez que votre CLI suit le format JSON ci-dessus |
| Projet_name mismatch | `project_name` ne correspond pas au dossier `specs/{nom}` | Vérifiez que `project_name` = nom du dossier `specs/` |
| Tâches ne se synchronisent pas | Le champ `tasks` est incomplet | Incluez TOUTES les tasks de `tasks.md` dans l'objet `tasks` |
| L'extension ne détecte pas | L'extension n'est pas démarrée | Lancez `agentdocx-speckit:start_server` et `agentdocx-speckit:startWatcher` |

---

## 📜 Historique

| Version | Date | Changement |
|---------|------|------------|
| `1.0.0` | 2026-08-14 | Version initiale : Protocol universel pour tous frameworks |

---

## 📞 Support

Pour questions sur l'implémentation de ce skill dans votre framework préféré :
- **Claude Code :** Voir `.claude/skills/` documentation
- **Copilot :** Voir `.github/copilot-instructions.md` génération
- **Aider :** Voir `--task-start-hook` documentation
- **Cursor :** Voir `.cursor/rules/` documentation
- **Codex :** Adapter script bash/python

---

**Ce fichier sert de référence unique** : quel que soit votre CLI, lisez d'abord `INSTRUCTIONS/instruction.md` pour le format JSON obligatoire et les instructions par framework.