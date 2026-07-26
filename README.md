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

## 🚀 Quick Start (Guide de Lancement)

Suivez ces étapes pour mettre en place l'environnement Spec Kit sur votre machine.

### ⚠️ Prérequis Base de Données
Avant de démarrer les services, assurez-vous impérativement que :
- **PostgreSQL** est lancé en arrière-plan.
- OU que **pgAdmin4** est ouvert avec une connexion active à la base de données du projet.

### 🛠️ Procédure de Lancement

**Étape 0 : Environnement Virtuel Python & Dépendances**
À la racine du projet, créez votre environnement virtuel Python, activez-le puis installez les dépendances du fichier `requirements.txt` :
```bash
# Créer l'environnement virtuel
python -m venv env

# Activer l'environnement
# Sur Windows : env\Scripts\activate
# Sur Linux/Mac : source env/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

**Étape 1 : Démarrer le Backend FastAPI**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Étape 2 : Démarrer l'interface Frontend React**
```bash
cd frontend
npm install
npm start
```
> 💡 **Note de Dépannage** : Si vous rencontrez des erreurs lors de l'installation ou du lancement du frontend (conflits de dépendances, Node.js, `cross-env` ou ports), veuillez vous référer au guide de configuration détaillé : **`configFrontEnd.pdf`** situé à la racine du projet.

**Étape 3 : Lancer le Watcher Temps Réel**
```bash
python scripts/python/spec_watcher.py
```

**Étape 4 : Exécuter Spec Kit via Claude Code**
```bash
ollama launch claude
```
*Vous pouvez maintenant utiliser les commandes Spec Kit (ex: `/speckit-specify`, `/doc-pipeline`) pour générer vos spécifications.*
