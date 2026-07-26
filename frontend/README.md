# 🖥️ Spec Kit Frontend

L'interface utilisateur de Spec Kit est un dashboard de monitoring et de pilotage conçu pour offrir une visibilité complète et en temps réel sur l'exécution du pipeline multi-agents d'enrichissement de spécifications.

## 📌 Présentation du Frontend

Le frontend est une application Web moderne construite avec l'écosystème suivant :
- **Framework** : React.js
- **UI Kit** : [Material UI (MUI)](https://mui.com/)
- **Data Visualisation** : [@mui/x-data-grid](https://mui.com/x-react-data-grid/)
- **Design** : Basé sur un thème de type *Admin Dashboard* pour une navigation efficace et une densité d'information optimisée.

L'interface sert de tour de contrôle permettant de suivre la progression des documents, d'analyser la qualité des sorties via des KPIs et de téléverser de nouvelles spécifications pour traitement.

---

## 🧩 Architecture des Composants (`src/scenes/`)

L'application est structurée autour de "scènes" qui représentent les différentes vues fonctionnelles du dashboard.

### 📑 Page "DOCUMENTS" (`src/scenes/documents/index.jsx`)
C'est le cœur du monitoring. Elle permet de visualiser l'état de santé et l'avancement de chaque document traité.

- **DataGrid Dynamique** : Liste tous les documents et leurs exécutions de pipeline correspondantes (`PipelineRun`).
- **Polling Temps Réel** : L'interface rafraîchit automatiquement les données toutes les 3 secondes (`POLL_INTERVAL = 3000`) pour mettre à jour les statuts :
  - `parsing` $\rightarrow$ `writing` $\rightarrow$ `completed` $\rightarrow$ `failed`.
- **Analyse de Qualité (`KpiPopup`)** : Une modale interactive qui décompose les évaluations JSONB générées par les 6 agents du pipeline :
  - `parsing_eval`, `summary_eval`, `glossary_eval`, `diagram_eval`, `writer_eval`, `layout_eval`.
- **Accès aux Livrables** : Un bouton **"Viewer"** permet d'ouvrir et de visualiser instantanément le fichier PDF final généré via l'API REST.

### ➕ Page "ADD DOCUMENT" (`src/scenes/add_document/index_form.jsx`)
Interface dédiée à l'injection de nouvelles données dans le pipeline.

- **Formulaire Interactif** : Saisie du nom du projet pour l'organisation des outputs.
- **Upload Intelligent** : Zone de **Drag & Drop** acceptant exclusivement les fichiers au format Markdown (`.md`).
- **Flux d'Envoi** : Transmission directe du fichier et des métadonnées du projet vers l'endpoint de téléversement du backend.

---

## ⚙️ Intégration API Backend

Le frontend communique avec le serveur FastAPI via des requêtes REST.

- **Adresse de base** : `http://localhost:8000/api/v1/docs`
- **Endpoints Consommés** :
  - `GET /documents` : Récupération de la liste exhaustive des documents et de l'état d'avancement des pipelines.
  - `POST /upload` : Envoi multipart (form-data) du fichier Markdown et du nom du projet.
  - `GET /pdf/{docVersionId}` : Flux de récupération et d'affichage du PDF final certifié.

---

## 🚀 Installation & Lancement Quick Start

### 🛠️ Étapes de mise en route

1. **Accéder au répertoire** :
   ```bash
   cd frontend
   ```

2. **Installation des dépendances** :
   ```bash
   npm install
   ```
   *Note : Si vous rencontrez des conflits de versions de dépendances, utilisez la commande suivante :*
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Lancement de l'application** :
   ```bash
   npm start
   ```

### ⚠️ Dépannage & Support
L'installation du frontend peut parfois présenter des instabilités selon l'environnement (OS, version de Node). Si vous rencontrez l'une des erreurs suivantes :
- Conflit de port (`PORT=5000` déjà utilisé).
- Erreur `cross-env` sous Windows.
- Incompatibilité avec Node.js v24.
- Erreurs liées à la librairie `ajv`.

👉 Veuillez consulter impérativement le guide de configuration pas-à-pas **`../configFrontEnd.pdf`** situé à la racine du projet pour résoudre ces problèmes.
