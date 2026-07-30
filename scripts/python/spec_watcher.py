import sys
import time
import requests
import os
from pathlib import Path
from queue import Queue
from threading import Thread, Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ============================================
# CONFIGURATION CONSOLE & ENCODAGE (Windows)
# ============================================
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# ============================================
# CONFIGURATION DE BASE & DÉTECTION SPECS
# ============================================
CURRENT_FILE = Path(__file__).resolve()

# Hiérarchie des dossiers :
# parents[0] = python/
# parents[1] = scripts/
# parents[2] = agentdocx-speckit/
# parents[3] = StageTalan/
STAGE_TALAN_DIR = CURRENT_FILE.parents[3] if len(CURRENT_FILE.parents) > 3 else CURRENT_FILE.parents[2]
AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# 🎯 PRIORITÉ 1 : Variable d'environnement SPECKIT_WORKSPACE (définie par l'extension VS Code)
SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
SPECKIT_SPECS_DIR = os.environ.get("SPECKIT_SPECS_DIR")
SPECKIT_BACKEND_DIR = os.environ.get("SPECKIT_BACKEND_DIR")
SPECKIT_SCRIPTS_DIR = os.environ.get("SPECKIT_SCRIPTS_DIR")

if SPECKIT_WORKSPACE:
    BASE_DIR = Path(SPECKIT_WORKSPACE)
    print(f"[WATCHER] Utilisation du workspace depuis l'extension : {BASE_DIR}")
else:
    # Fallback : détection automatique (mode standalone)
    print(f"[WATCHER] Mode standalone - détection automatique du workspace")
    if (STAGE_TALAN_DIR / "specs").exists():
        BASE_DIR = STAGE_TALAN_DIR
    elif (AGENTDOCX_DIR / "specs").exists():
        BASE_DIR = AGENTDOCX_DIR
    else:
        BASE_DIR = STAGE_TALAN_DIR

if SPECKIT_SPECS_DIR:
    WATCH_DIR = Path(SPECKIT_SPECS_DIR)
else:
    WATCH_DIR = BASE_DIR / "specs"

# Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# API Endpoints
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


# ============================================
# UTILITAIRES POSIX
# ============================================
def sanitize_path_string(path_str: str) -> str:
    """
    Nettoyage preventif de TOUS les caracteres de controle ASCII (0x00-0x1F)
    et remplacement des backslashes Windows par des slashes POSIX.
    """
    clean_str = str(path_str)
    clean_str = clean_str.replace("\\", "/")
    for i in range(0, 32):
        clean_str = clean_str.replace(chr(i), "")
    return clean_str


def to_posix_str(path_obj) -> str:
    """
    Convertit n'importe quel chemin (Path ou str) en format POSIX strict,
    SANS caracteres de controle.
    """
    if path_obj is None:
        return ""
    return sanitize_path_string(Path(path_obj).as_posix())


# ============================================
# LOGIQUE DE STABILISATION ET D'ENVOI
# ============================================
def wait_until_file_is_stable(
    file_path: Path, 
    wait_seconds: float = 2.0, 
    check_interval: float = 0.5,
    max_timeout: float = 20.0
) -> bool:
    """⏳ Attend que l'outil d'écriture (ex: Claude Code / IDE) termine la modification du fichier."""
    if not file_path.exists():
        return False

    last_size = -1
    stable_time = 0.0
    total_time = 0.0

    print(f"⏳ [WATCHER] Attente de stabilisation pour : {file_path.name}", flush=True)

    while stable_time < wait_seconds and total_time < max_timeout:
        try:
            if not file_path.exists():
                return False
            
            current_size = file_path.stat().st_size
            with open(file_path, "r", encoding="utf-8") as f:
                _ = f.read(50)
        except (OSError, PermissionError):
            current_size = -1

        if current_size > 0 and current_size == last_size:
            stable_time += check_interval
        else:
            last_size = current_size
            stable_time = 0.0

        time.sleep(check_interval)
        total_time += check_interval

    if stable_time >= wait_seconds:
        print(f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}", flush=True)
        return True
    else:
        print(f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}", flush=True)
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
    """🗂️ Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
    try:
        file_path_posix = to_posix_str(file_path.resolve())
        response = requests.get(
            API_CHECK_URL,
            params={"file_path": file_path_posix},
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get("exists_in_db", False)
    except Exception as e:
        print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}", flush=True)
    
    return False


def trigger_pipeline(file_path: Path):
    """Envoie le fichier Markdown et le nom de projet a l'endpoint FastAPI /upload."""
    abs_path = file_path.resolve()
    
    try:
        rel_path = abs_path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        rel_path = abs_path.name

    # 🎯 Extraction du nom du projet sous 'specs/'
    project_name = "Default Project"
    try:
        relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
        if len(relative_parts) > 1:
            project_name = relative_parts[0]
    except ValueError:
        pass

    print(f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})", flush=True)

    try:
        with open(abs_path, "rb") as f:
            files = {"file": (abs_path.name, f, "text/markdown")}
            data = {"projectName": project_name}
            response = requests.post(API_RUN_URL, files=files, data=data, timeout=None)

        if response.status_code in (200, 201):
            print(f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n", flush=True)
        elif response.status_code == 429:
            print(f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}", flush=True)
            file_queue.put(abs_path)
        else:
            print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n", flush=True)
    except Exception as e:
        print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n", flush=True)


def queue_worker():
    """👷 Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
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


# ============================================
# LOGIQUE DE STABILISATION ET D'ENVOI
# ============================================
from collections import defaultdict
import time

_last_event_time = defaultdict(float)
_DEBOUNCE_SECONDS = 1.0

def handle_file_event(file_path: Path):
    """📥 Vérifie la stabilité puis ajoute le fichier à la file d'attente (avec debounce)."""
    abs_path = file_path.resolve()
    now = time.time()
    
    # Debounce : ignorer si même fichier traité récemment
    if now - _last_event_time[abs_path] < _DEBOUNCE_SECONDS:
        return
    _last_event_time[abs_path] = now
    
    with pending_lock:
        if abs_path in pending_files:
            return
        pending_files.add(abs_path)

    if wait_until_file_is_stable(abs_path, wait_seconds=2.0):
        print(f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}", flush=True)
        file_queue.put(abs_path)
    else:
        with pending_lock:
            pending_files.discard(abs_path)


# ============================================
# WATCHER PRINCIPAL
# ============================================
class SpecWatcherHandler(FileSystemEventHandler):
    """🔍 Gestionnaire d'événements du système de fichiers."""
    
    def process_path(self, file_path: Path):
        abs_path = file_path.resolve()

        # 1️⃣ Ignorer les dossiers système ou réservés
        if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
            return

        # 2️⃣ Ignorer les templates
        if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
            return

        # 3️⃣ Traiter uniquement les fichiers .md des types autorisés
        if abs_path.suffix.lower() == ".md":
            clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
            if clean_stem not in ALLOWED_ARTIFACT_TYPES:
                return

            print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}", flush=True)
            Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

    def on_modified(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path))

    def on_created(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.process_path(Path(event.dest_path))


def wait_for_server(max_wait: int = 60) -> bool:
    """Attend que le serveur FastAPI soit prêt (endpoint /health répond 200)."""
    print(f"⏳ [WATCHER] Attente du serveur FastAPI (max {max_wait}s)...", flush=True)
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(API_STATUS_URL, timeout=2)
            if response.status_code == 200:
                print("✅ [WATCHER] Serveur FastAPI prêt", flush=True)
                return True
        except Exception:
            pass
        time.sleep(1)
    print("⚠️ [WATCHER] Timeout : serveur non disponible", flush=True)
    return False


def initial_scan():
    """🔍 Scanne tous les fichiers .md au démarrage du Watcher."""
    # Attendre que le serveur soit prêt
    if not wait_for_server():
        print("❌ [WATCHER] Serveur inaccessible, scan initial annulé", flush=True)
        return
    
    print(f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...", flush=True)
    
    for file_path in WATCH_DIR.glob("**/*.md"):
        abs_path = file_path.resolve()

        if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
            continue

        if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
            continue

        clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
        if clean_stem not in ALLOWED_ARTIFACT_TYPES:
            continue

        if is_file_already_in_db(abs_path):
            print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}", flush=True)
        else:
            print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}", flush=True)
            Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()


# ============================================
# POINT D'ENTRÉE
# ============================================
if __name__ == "__main__":
    print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}", flush=True)
    print(f"🎯 [WATCHER] Types d'artefacts autorisés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n", flush=True)

    # Worker thread
    Thread(target=queue_worker, daemon=True).start()

    # Scan initial
    initial_scan()

    # Démarrage Watchdog
    event_handler = SpecWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)
    observer.start()

    try:
        print("🟢 [WATCHER] En attente d'événements...\n", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
        observer.stop()
    observer.join()
# import sys
# import os
# import time
# import requests
# from pathlib import Path
# from queue import Queue
# from threading import Thread, Lock
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# # 1. FORCER L'AFFICHAGE IMMÉDIAT ET L'ENCODAGE UTF-8 (Pour VS Code / Terminal)
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# # 2. DÉTECTION DU DOSSIER SPECS (Racine StageTalan vs agentdocx-speckit)
# CURRENT_FILE = Path(__file__).resolve()

# # parents[0] = .../scripts/python
# # parents[1] = .../scripts
# # parents[2] = .../agentdocx-speckit
# # parents[3] = .../StageTalan
# STAGE_TALAN_DIR = CURRENT_FILE.parents[3] if len(CURRENT_FILE.parents) > 3 else CURRENT_FILE.parents[2]
# AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# # Vérification prioritaire du dossier StageTalan/specs
# if (STAGE_TALAN_DIR / "specs").exists():
#     BASE_DIR = STAGE_TALAN_DIR
# elif (AGENTDOCX_DIR / "specs").exists():
#     BASE_DIR = AGENTDOCX_DIR
# else:
#     BASE_DIR = STAGE_TALAN_DIR

# WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : création du dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# # 3. ENDPOINTS API FASTAPI
# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Filtres
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}
# ALLOWED_ARTIFACT_TYPES = {"spec", "plan", "tasks", "task", "constitution", "requirements", "contracts"}

# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()


# def wait_until_file_is_stable(
#     file_path: Path, 
#     wait_seconds: float = 2.0, 
#     check_interval: float = 0.5,
#     max_timeout: float = 20.0
# ) -> bool:
#     if not file_path.exists():
#         return False

#     last_size = -1
#     stable_time = 0.0
#     total_time = 0.0

#     print(f"⏳ [WATCHER] Attente de stabilisation pour : {file_path.name}", flush=True)

#     while stable_time < wait_seconds and total_time < max_timeout:
#         try:
#             if not file_path.exists():
#                 return False
            
#             current_size = file_path.stat().st_size
#             with open(file_path, "r", encoding="utf-8") as f:
#                 _ = f.read(50)
#         except (OSError, PermissionError):
#             current_size = -1

#         if current_size > 0 and current_size == last_size:
#             stable_time += check_interval
#         else:
#             last_size = current_size
#             stable_time = 0.0

#         time.sleep(check_interval)
#         total_time += check_interval

#     if stable_time >= wait_seconds:
#         print(f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}", flush=True)
#         return True
#     else:
#         print(f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}", flush=True)
#         return False


# def is_server_busy() -> bool:
#     try:
#         res = requests.get(API_STATUS_URL, timeout=3)
#         if res.status_code == 200:
#             return res.json().get("is_running", False)
#     except Exception:
#         pass
#     return False


# def is_file_already_in_db(file_path: Path) -> bool:
#     try:
#         response = requests.get(
#             API_CHECK_URL,
#             params={"file_path": str(file_path.resolve())},
#             timeout=3
#         )
#         if response.status_code == 200:
#             return response.json().get("exists_in_db", False)
#     except Exception as e:
#         print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}", flush=True)
    
#     return False


# def trigger_pipeline(file_path: Path):
#     abs_path = file_path.resolve()
#     rel_path = abs_path.relative_to(BASE_DIR) if abs_path.is_relative_to(BASE_DIR) else abs_path.name

#     project_name = "Default Project"
#     try:
#         relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#         if len(relative_parts) > 1:
#             project_name = relative_parts[0]
#     except ValueError:
#         pass

#     print(f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})", flush=True)

#     try:
#         with open(abs_path, "rb") as f:
#             files = {"file": (abs_path.name, f, "text/markdown")}
#             data = {"projectName": project_name}
#             response = requests.post(API_RUN_URL, files=files, data=data, timeout=None)

#         if response.status_code in (200, 201):
#             print(f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n", flush=True)
#         elif response.status_code == 429:
#             print(f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}", flush=True)
#             file_queue.put(file_path)
#         else:
#             print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n", flush=True)
#     except Exception as e:
#         print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n", flush=True)


# def queue_worker():
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
#     abs_path = file_path.resolve()

#     with pending_lock:
#         if abs_path in pending_files:
#             return
#         pending_files.add(abs_path)

#     if wait_until_file_is_stable(abs_path, wait_seconds=2.0):
#         print(f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}", flush=True)
#         file_queue.put(abs_path)
#     else:
#         with pending_lock:
#             pending_files.discard(abs_path)


# class SpecWatcherHandler(FileSystemEventHandler):
#     def process_path(self, file_path: Path):
#         abs_path = file_path.resolve()

#         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
#             return

#         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#             return

#         if abs_path.suffix.lower() == ".md":
#             clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
#             if clean_stem not in ALLOWED_ARTIFACT_TYPES:
#                 return

#             print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}", flush=True)
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

#     def on_modified(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_created(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_moved(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.dest_path))


# def initial_scan():
#     print(f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...", flush=True)
    
#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
#             continue

#         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#             continue

#         clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
#         if clean_stem not in ALLOWED_ARTIFACT_TYPES:
#             continue

#         if is_file_already_in_db(abs_path):
#             print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}", flush=True)
#         else:
#             print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}", flush=True)
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()


# if __name__ == "__main__":
#     print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}", flush=True)
#     print(f"🎯 [WATCHER] Types d'artefacts écoutés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n", flush=True)

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
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
#         observer.stop()
#     observer.join()
# import sys
# import os
# import time
# import requests
# from pathlib import Path
# from queue import Queue
# from threading import Thread, Lock
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# # 1. FORCER L'AFFICHAGE EN TEMPS RÉEL ET L'ENCODAGE UTF-8 (Pour VS Code)
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# # 2. LOCALISATION DU DOSSIER StageTalan/specs
# CURRENT_FILE = Path(__file__).resolve()

# # Parents :
# # parents[0] = .../scripts/python
# # parents[1] = .../scripts
# # parents[2] = .../agentdocx-speckit
# # parents[3] = .../StageTalan
# STAGE_TALAN_DIR = CURRENT_FILE.parents[3] if len(CURRENT_FILE.parents) > 3 else CURRENT_FILE.parents[2]
# AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# # Détection automatique de StageTalan/specs (avec fallback sur agentdocx-speckit/specs)
# if (STAGE_TALAN_DIR / "specs").exists():
#     BASE_DIR = STAGE_TALAN_DIR
# elif (AGENTDOCX_DIR / "specs").exists():
#     BASE_DIR = AGENTDOCX_DIR
# else:
#     BASE_DIR = STAGE_TALAN_DIR

# WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# # 3. ENDPOINTS API FASTAPI
# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Fichiers et dossiers à ignorer strictement
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# # 🎯 Types d'artefacts autorisés à déclencher le pipeline
# ALLOWED_ARTIFACT_TYPES = {"spec", "plan", "tasks", "task", "constitution", "requirements", "contracts"}

# # File d'attente & verrous pour la synchronisation des événements
# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()


# def wait_until_file_is_stable(
#     file_path: Path, 
#     wait_seconds: float = 2.0, 
#     check_interval: float = 0.5,
#     max_timeout: float = 20.0
# ) -> bool:
#     """Attend que l'outil d'écriture (ex: Claude Code / IDE) termine la modification du fichier."""
#     if not file_path.exists():
#         return False

#     last_size = -1
#     stable_time = 0.0
#     total_time = 0.0

#     print(f"⏳ [WATCHER] Attente de stabilisation pour : {file_path.name}", flush=True)

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
#         print(f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}", flush=True)
#         return True
#     else:
#         print(f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}", flush=True)
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
#         print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}", flush=True)
    
#     return False


# def trigger_pipeline(file_path: Path):
#     """Envoie le fichier Markdown et le projet à l'endpoint FastAPI /upload."""
#     abs_path = file_path.resolve()
#     rel_path = file_path.relative_to(BASE_DIR) if file_path.is_relative_to(BASE_DIR) else file_path.name

#     # Extraire le nom du dossier projet sous 'specs/'
#     project_name = "Default Project"
#     try:
#         relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#         if len(relative_parts) > 1:
#             project_name = relative_parts[0]
#     except ValueError:
#         pass

#     print(f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})", flush=True)

#     try:
#         # Envoi en multipart/form-data conforme à /api/v1/pipeline/upload
#         with open(abs_path, "rb") as f:
#             files = {"file": (abs_path.name, f, "text/markdown")}
#             data = {"projectName": project_name}
#             response = requests.post(API_RUN_URL, files=files, data=data, timeout=None)

#         if response.status_code in (200, 201):
#             print(f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n", flush=True)
#         elif response.status_code == 429:
#             print(f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}", flush=True)
#             file_queue.put(file_path)
#         else:
#             print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n", flush=True)
#     except Exception as e:
#         print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n", flush=True)


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
#         print(f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}", flush=True)
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

#         # 3. Traiter uniquement les fichiers .md faisant partie des types autorisés
#         if abs_path.suffix.lower() == ".md":
#             clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
#             if clean_stem not in ALLOWED_ARTIFACT_TYPES:
#                 return

#             print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}", flush=True)
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
#     """Scanne tous les fichiers .md sous specs/ au démarrage du Watcher."""
#     print(f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...", flush=True)
    
#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS):
#             continue

#         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#             continue

#         clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
#         if clean_stem not in ALLOWED_ARTIFACT_TYPES:
#             continue

#         if is_file_already_in_db(abs_path):
#             print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}", flush=True)
#         else:
#             print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}", flush=True)
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()


# if __name__ == "__main__":
#     print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}", flush=True)
#     print(f"🎯 [WATCHER] Types d'artefacts écoutés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n", flush=True)

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
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
#         observer.stop()
#     observer.join()
