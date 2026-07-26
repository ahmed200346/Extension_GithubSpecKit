import time
import requests
from pathlib import Path
from queue import Queue
from threading import Thread, Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[2]
WATCH_DIR = BASE_DIR / "specs"

# Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
WATCH_DIR.mkdir(parents=True, exist_ok=True)

API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# Fichiers et dossiers à ignorer strictement
IGNORED_FILES = {"template.md", "spec-template.md"}
IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# 🎯 Types d'artefacts autorisés à déclencher le pipeline
ALLOWED_ARTIFACT_TYPES = {"spec", "plan", "tasks", "task", "constitution", "requirements", "contracts"}

# 🎯 File d'attente & verrous pour la synchronisation des événements
file_queue = Queue()
pending_files = set()
pending_lock = Lock()


def wait_until_file_is_stable(
    file_path: Path, 
    wait_seconds: float = 2.0, 
    check_interval: float = 0.5,
    max_timeout: float = 20.0
) -> bool:
    """
    Attend que l'outil d'écriture (ex: Claude Code / IDE) termine la modification du fichier.
    """
    if not file_path.exists():
        return False

    last_size = -1
    stable_time = 0.0
    total_time = 0.0

    print(f"⏳ [WATCHER] Attente de stabilisation pour : {file_path.name}")

    while stable_time < wait_seconds and total_time < max_timeout:
        try:
            if not file_path.exists():
                return False
            
            current_size = file_path.stat().st_size
            
            # Essai de lecture pour vérifier que le fichier n'est pas verrouillé
            with open(file_path, "r", encoding="utf-8") as f:
                _ = f.read(50)
        except (OSError, PermissionError):
            current_size = -1

        if current_size > 0 and current_size == last_size:
            stable_time += check_interval
        else:
            last_size = current_size
            stable_time = 0.0  # Réinitialise si le fichier est en cours d'écriture

        time.sleep(check_interval)
        total_time += check_interval

    if stable_time >= wait_seconds:
        print(f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}")
        return True
    else:
        print(f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}")
        return False


def is_server_busy() -> bool:
    """Vérifie auprès de FastAPI si le pipeline est actuellement en cours d'exécution."""
    try:
        res = requests.get(API_STATUS_URL, timeout=3)
        if res.status_code == 200:
            return res.json().get("is_running", False)
    except Exception:
        pass
    return False


def is_file_already_in_db(file_path: Path) -> bool:
    """Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
    try:
        response = requests.get(
            API_CHECK_URL,
            params={"file_path": str(file_path.resolve())},
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get("exists_in_db", False)
    except Exception as e:
        print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}")
    
    return False


def trigger_pipeline(file_path: Path):
    """Envoie le fichier Markdown et le projet à l'endpoint FastAPI /upload."""
    abs_path = file_path.resolve()
    rel_path = file_path.relative_to(BASE_DIR) if file_path.is_relative_to(BASE_DIR) else file_path.name

    # Extraire le nom du dossier projet sous 'specs/'
    project_name = "Default Project"
    try:
        relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
        if len(relative_parts) > 1:
            project_name = relative_parts[0]
    except ValueError:
        pass

    print(f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})")

    try:
        # Envoi en multipart/form-data conforme à /api/v1/pipeline/upload
        with open(abs_path, "rb") as f:
            files = {"file": (abs_path.name, f, "text/markdown")}
            data = {"projectName": project_name}
            response = requests.post(API_RUN_URL, files=files, data=data, timeout=None)

        if response.status_code in (200, 201):
            print(f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n")
        elif response.status_code == 429:
            print(f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}")
            file_queue.put(file_path)
        else:
            print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n")
    except Exception as e:
        print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n")

def queue_worker():
    """Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
    while True:
        file_path = file_queue.get()
        try:
            while is_server_busy():
                time.sleep(2)

            trigger_pipeline(file_path)

        finally:
            with pending_lock:
                pending_files.discard(file_path)
            file_queue.task_done()


def handle_file_event(file_path: Path):
    """Vérifie la stabilité puis ajoute le fichier à la file d'attente de manière thread-safe."""
    abs_path = file_path.resolve()

    with pending_lock:
        if abs_path in pending_files:
            return
        pending_files.add(abs_path)

    if wait_until_file_is_stable(abs_path, wait_seconds=2.0):
        print(f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}")
        file_queue.put(abs_path)
    else:
        with pending_lock:
            pending_files.discard(abs_path)


class SpecWatcherHandler(FileSystemEventHandler):
    def process_path(self, file_path: Path):
        """Filtre et traite les modifications, créations et déplacements de fichiers."""
        abs_path = file_path.resolve()

        # 1. Ignorer les dossiers système ou réservés
        if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
            return

        # 2. Ignorer les templates de spécification
        if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
            return

        # 3. Traiter uniquement les fichiers .md faisant partie des types autorisés
        if abs_path.suffix.lower() == ".md":
            # Extraire la racine du nom (ex: "plan(1)" -> "plan", "spec_v1.0" -> "spec")
            clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
            if clean_stem not in ALLOWED_ARTIFACT_TYPES:
                return

            print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}")
            Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

    def on_modified(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path))

    def on_created(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path))

    def on_moved(self, event):
        """Capture les écritures atomiques (fichiers temporaires remplacés par Claude Code)."""
        if not event.is_directory:
            self.process_path(Path(event.dest_path))


def initial_scan():
    """
    Scanne tous les fichiers .md sous specs/ au démarrage du Watcher
    et ne charge que ceux qui NE sont PAS encore enregistrés dans la BDD.
    """
    print("\n🔍 [WATCHER] Scan initial du dossier specs/...")
    
    for file_path in WATCH_DIR.glob("**/*.md"):
        abs_path = file_path.resolve()

        if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
            continue

        if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
            continue

        # Filtrage par type d'artefact autorisé
        clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
        if clean_stem not in ALLOWED_ARTIFACT_TYPES:
            continue

        if is_file_already_in_db(abs_path):
            print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}")
        else:
            print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}")
            Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()


if __name__ == "__main__":
    print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}")
    print(f"🎯 [WATCHER] Types d'artefacts écoutés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n")

    Thread(target=queue_worker, daemon=True).start()

    initial_scan()

    event_handler = SpecWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 [WATCHER] Arrêt de la surveillance.")
        observer.stop()
    observer.join()

# import time
# import requests
# from pathlib import Path
# from queue import Queue
# from threading import Thread, Lock
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# # --- CONFIGURATION ---
# BASE_DIR = Path(__file__).resolve().parents[2]
# WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/run"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Fichiers et dossiers à ignorer strictement
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# # 🎯 File d'attente & verrous pour la synchronisation des événements
# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()


# def wait_until_file_is_stable(
#     file_path: Path, 
#     wait_seconds: float = 2.0, 
#     check_interval: float = 0.5,
#     max_timeout: float = 20.0
# ) -> bool:
#     """
#     Attend que l'outil d'écriture (ex: Claude Code / IDE) termine la modification du fichier.
#     """
#     if not file_path.exists():
#         return False

#     last_size = -1
#     stable_time = 0.0
#     total_time = 0.0

#     print(f"⏳ [WATCHER] Attente de stabilisation pour : {file_path.name}")

#     while stable_time < wait_seconds and total_time < max_timeout:
#         try:
#             if not file_path.exists():
#                 return False
            
#             current_size = file_path.stat().st_size
            
#             # Essai de lecture pour vérifier que le fichier n'est pas verrouillé
#             with open(file_path, "r", encoding="utf-8") as f:
#                 _ = f.read(50)
#         except (OSError, PermissionError):
#             current_size = -1

#         if current_size > 0 and current_size == last_size:
#             stable_time += check_interval
#         else:
#             last_size = current_size
#             stable_time = 0.0  # Réinitialise si le fichier est en cours d'écriture

#         time.sleep(check_interval)
#         total_time += check_interval

#     if stable_time >= wait_seconds:
#         print(f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}")
#         return True
#     else:
#         print(f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}")
#         return False


# def is_server_busy() -> bool:
#     """Vérifie auprès de FastAPI si le pipeline est actuellement en cours d'exécution."""
#     try:
#         res = requests.get(API_STATUS_URL, timeout=3)
#         if res.status_code == 200:
#             return res.json().get("is_running", False)
#     except Exception:
#         pass
#     return False


# def is_file_already_in_db(file_path: Path) -> bool:
#     """Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
#     try:
#         response = requests.get(
#             API_CHECK_URL,
#             params={"file_path": str(file_path.resolve())},
#             timeout=3
#         )
#         if response.status_code == 200:
#             return response.json().get("exists_in_db", False)
#     except Exception as e:
#         print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}")
    
#     return False


# def trigger_pipeline(file_path: Path):
#     """Envoie le chemin absolu du fichier Markdown à l'API FastAPI."""
#     abs_path = str(file_path.resolve())
#     rel_path = file_path.relative_to(BASE_DIR) if file_path.is_relative_to(BASE_DIR) else file_path.name

#     print(f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path}")
#     payload = {"file_path": abs_path}
    
#     try:
#         response = requests.post(API_RUN_URL, json=payload, timeout=None)
#         if response.status_code == 200:
#             print(f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n")
#         elif response.status_code == 429:
#             print(f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}")
#             file_queue.put(file_path)
#         else:
#             print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n")
#     except Exception as e:
#         print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n")


# def queue_worker():
#     """Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
#     while True:
#         file_path = file_queue.get()
#         try:
#             while is_server_busy():
#                 time.sleep(2)

#             trigger_pipeline(file_path)

#         finally:
#             with pending_lock:
#                 pending_files.discard(file_path)
#             file_queue.task_done()


# def handle_file_event(file_path: Path):
#     """Vérifie la stabilité puis ajoute le fichier à la file d'attente de manière thread-safe."""
#     abs_path = file_path.resolve()

#     with pending_lock:
#         if abs_path in pending_files:
#             return
#         pending_files.add(abs_path)

#     if wait_until_file_is_stable(abs_path, wait_seconds=2.0):
#         print(f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}")
#         file_queue.put(abs_path)
#     else:
#         with pending_lock:
#             pending_files.discard(abs_path)


# class SpecWatcherHandler(FileSystemEventHandler):
#     def process_path(self, file_path: Path):
#         """Filtre et traite les modifications, créations et déplacements de fichiers."""
#         abs_path = file_path.resolve()

#         # 1. Ignorer les dossiers système ou réservés
#         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
#             return

#         # 2. Ignorer les templates de spécification
#         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#             return

#         # 3. Traiter uniquement les fichiers .md
#         if abs_path.suffix.lower() == ".md":
#             print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}")
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

#     def on_modified(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_created(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_moved(self, event):
#         """Capture les écritures atomiques (fichiers temporaires remplacés par Claude Code)."""
#         if not event.is_directory:
#             self.process_path(Path(event.dest_path))


# def initial_scan():
#     """
#     Scanne tous les fichiers .md sous specs/ au démarrage du Watcher
#     et ne charge que ceux qui NE sont PAS encore enregistrés dans la BDD.
#     """
#     print("\n🔍 [WATCHER] Scan initial du dossier specs/...")
    
#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
#             continue

#         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#             continue

#         if is_file_already_in_db(abs_path):
#             print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}")
#         else:
#             print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}")
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()


# if __name__ == "__main__":
#     print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}")
#     print("🎯 [WATCHER] Types de fichiers écoutés : Tous les *.md (spec.md, requirements.md, etc.)\n")

#     Thread(target=queue_worker, daemon=True).start()

#     initial_scan()

#     event_handler = SpecWatcherHandler()
#     observer = Observer()
#     observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)
#     observer.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.")
#         observer.stop()
#     observer.join()
