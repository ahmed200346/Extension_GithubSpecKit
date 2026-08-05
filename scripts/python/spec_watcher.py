import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from queue import Queue
from threading import Lock, Thread

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ============================================
# CONFIGURATION CONSOLE & ENCODAGE (Windows)
# ============================================
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")

# ============================================
# CONFIGURATION DE BASE & DÉTECTION SPECS
# ============================================
CURRENT_FILE = Path(__file__).resolve()

STAGE_TALAN_DIR = (
    CURRENT_FILE.parents[3]
    if len(CURRENT_FILE.parents) > 3
    else CURRENT_FILE.parents[2]
)
AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# PRIORITÉ 1 : Variable d'environnement SPECKIT_WORKSPACE
SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
SPECKIT_SPECS_DIR = os.environ.get("SPECKIT_SPECS_DIR")
SPECKIT_BACKEND_DIR = os.environ.get("SPECKIT_BACKEND_DIR")
SPECKIT_SCRIPTS_DIR = os.environ.get("SPECKIT_SCRIPTS_DIR")

if SPECKIT_WORKSPACE:
    BASE_DIR = Path(SPECKIT_WORKSPACE)
    print(f"[WATCHER] Utilisation du workspace depuis l'extension : {BASE_DIR}")
else:
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

WATCH_DIR.mkdir(parents=True, exist_ok=True)

# API Endpoints
API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

IGNORED_FILES = {"template.md", "spec-template.md"}
IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

ALLOWED_ARTIFACT_TYPES = {
    "spec",
    "plan",
    "tasks",
    "task",
    "constitution",
    "requirements",
    "contracts",
    "data-model",
    "research",
    "quickstart",
    "autres",
}

file_queue = Queue()
pending_files = set()
pending_lock = Lock()

_last_event_time = defaultdict(float)
_DEBOUNCE_SECONDS = 2.0

CONSTITUTION_FILE = BASE_DIR / ".specify" / "memory" / "constitution.md"


# ============================================
# UTILITAIRES POSIX
# ============================================
def sanitize_path_string(path_str: str) -> str:
    """Nettoyage préventif des caractères de contrôle ASCII et conversion des backslashes Windows."""
    clean_str = str(path_str)
    clean_str = clean_str.replace("\\", "/")
    for i in range(0, 32):
        clean_str = clean_str.replace(chr(i), "")
    return clean_str


def to_posix_str(path_obj) -> str:
    """Convertit un chemin au format POSIX strict."""
    if path_obj is None:
        return ""
    return sanitize_path_string(Path(path_obj).as_posix())


# ============================================
# VALIDATION STRUCTURELLE DU MARKDOWN
# ============================================
def is_markdown_structurally_complete(content: str) -> bool:
    """
    Vérifie si le Markdown généré est valide et complet :
    1. Doit dépasser une longueur minimale (150 caractères).
    2. Blocs de code Markdown (```) fermés (nombre pair).
    3. Ne se termine pas sur un titre ou une liste suspendue.
    """
    if not content or len(content.strip()) < 150:
        return False

    backtick_count = content.count("```")
    if backtick_count % 2 != 0:
        return False

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return False

    last_line = lines[-1]
    if last_line in ("-", "*", "+", "1.", "#", "##", "###", "####", "#####", "######") or last_line.endswith("..."):
        return False

    return True


# ============================================
# LOGIQUE DE STABILISATION ET D'ENVOI
# ============================================
def wait_until_file_is_stable(
    file_path: Path,
    wait_seconds: float = 8.0,
    check_interval: float = 1.0,
    max_timeout: float = 180.0,
    min_size_bytes: int = 150
) -> bool:
    """⏳ Attend que l'outil d'écriture termine la rédaction complète du fichier."""
    if not file_path.exists():
        return False

    last_size = -1
    stable_time = 0.0
    total_time = 0.0

    print(
        f"⏳ [WATCHER] Attente de stabilisation/écriture IA (8s inactivité + structure MD) pour : {file_path.name}",
        flush=True,
    )

    while total_time < max_timeout:
        try:
            if not file_path.exists():
                return False

            current_size = file_path.stat().st_size

            if current_size < min_size_bytes:
                time.sleep(check_interval)
                total_time += check_interval
                continue

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            structurally_ok = is_markdown_structurally_complete(content)

            if current_size > 0 and current_size == last_size and structurally_ok:
                stable_time += check_interval
            else:
                last_size = current_size
                stable_time = 0.0

        except (OSError, PermissionError):
            current_size = -1
            stable_time = 0.0

        if stable_time >= wait_seconds:
            print(
                f"✅ [WATCHER] Fichier complété et stabilisé ({last_size} octets) : {file_path.name}",
                flush=True,
            )
            return True

        time.sleep(check_interval)
        total_time += check_interval

    print(
        f"⚠️ [WATCHER] Timeout de stabilisation dépassé pour : {file_path.name}",
        flush=True,
    )
    return False


def is_valid_spec_file(abs_path: Path) -> bool:
    """Valide tout fichier .md situé sous specs/<projet_name>/..."""
    if abs_path.resolve() == CONSTITUTION_FILE.resolve():
        return True

    if abs_path.suffix.lower() != ".md":
        return False

    if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
        return False

    if any(
        folder in abs_path.parts
        for folder in IGNORED_FOLDERS
        if folder != ".specify"
    ):
        return False

    try:
        relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
        if len(relative_parts) >= 2:
            return True
    except ValueError:
        return False

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
    """🗂️ Interroge l'API FastAPI pour savoir si la version actuelle du fichier existe déjà en BDD."""
    try:
        file_path_posix = to_posix_str(file_path.resolve())
        response = requests.get(
            API_CHECK_URL, params={"file_path": file_path_posix}, timeout=3
        )
        if response.status_code == 200:
            return response.json().get("exists_in_db", False)
    except Exception as e:
        print(
            f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}",
            flush=True,
        )

    return False


def resolve_constitution_project_name() -> str:
    root_project_name = (
        BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
    )
    specs_dir = WATCH_DIR.resolve()

    if not specs_dir.exists():
        return root_project_name

    project_dirs = [
        d
        for d in specs_dir.iterdir()
        if d.is_dir()
        and d.name not in IGNORED_FOLDERS
        and not d.name.startswith(".")
    ]

    if not project_dirs:
        return root_project_name

    def get_latest_mtime(folder: Path) -> float:
        mtime = folder.stat().st_mtime
        for item in folder.rglob("*"):
            try:
                mtime = max(mtime, item.stat().st_mtime)
            except OSError:
                pass
        return mtime

    latest_project_dir = max(project_dirs, key=get_latest_mtime)
    return latest_project_dir.name


def trigger_pipeline(file_path: Path):
    """Envoie le fichier Markdown et le nom de projet à l'endpoint FastAPI /upload."""
    abs_path = file_path.resolve()

    try:
        rel_path = abs_path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        rel_path = abs_path.name

    root_project_name = (
        BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
    )

    if (
        abs_path.name.lower() == "constitution.md"
        and ".specify" in abs_path.parts
    ):
        project_name = resolve_constitution_project_name()
    else:
        try:
            relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
            if len(relative_parts) > 1:
                project_name = relative_parts[0]
            else:
                project_name = root_project_name
        except ValueError:
            project_name = root_project_name

    print(
        f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})",
        flush=True,
    )

    try:
        with open(abs_path, "rb") as f:
            files = {"file": (abs_path.name, f, "text/markdown")}
            data = {"projectName": project_name}
            response = requests.post(
                API_RUN_URL, files=files, data=data, timeout=None
            )

        if response.status_code in (200, 201):
            print(
                f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n",
                flush=True,
            )
        elif response.status_code == 429:
            print(
                f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}",
                flush=True,
            )
            file_queue.put(abs_path)
        else:
            print(
                f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n",
                flush=True,
            )
    except Exception as e:
        print(
            f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n",
            flush=True,
        )


def queue_worker():
    """👷 Worker en arrière-plan traitant séquentiellement les fichiers Markdown."""
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
    """📥 Vérifie la stabilité puis ajoute le fichier (création v1 ou mise à jour v2...vn) à la file."""
    abs_path = file_path.resolve()
    now = time.time()

    if now - _last_event_time[abs_path] < _DEBOUNCE_SECONDS:
        return
    _last_event_time[abs_path] = now

    with pending_lock:
        if abs_path in pending_files:
            return
        pending_files.add(abs_path)

    if wait_until_file_is_stable(abs_path, wait_seconds=8.0):
        print(
            f"📥 [WATCHER] Fichier validé et complet ! Ajouté à la file d'attente : {abs_path.name}",
            flush=True,
        )
        file_queue.put(abs_path)
    else:
        with pending_lock:
            pending_files.discard(abs_path)


# ============================================
# WATCHER PRINCIPAL
# ============================================
class SpecWatcherHandler(FileSystemEventHandler):
    """🔍 Gestionnaire d'événements du système de fichiers (Création v1, Modifications v2...vN)."""

    def process_path(self, file_path: Path, event_type: str = "Événement"):
        abs_path = file_path.resolve()

        if not is_valid_spec_file(abs_path):
            return

        if abs_path == CONSTITUTION_FILE.resolve():
            print(
                f"👁️ [WATCHER] [{event_type}] Constitution.md détecté : {abs_path.name}",
                flush=True,
            )
        else:
            print(
                f"👁️ [WATCHER] [{event_type}] Traitement déclenché pour : {abs_path.relative_to(WATCH_DIR.resolve())}",
                flush=True,
            )

        Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

    def on_modified(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path), event_type="Modification v+1")

    def on_created(self, event):
        if not event.is_directory:
            self.process_path(Path(event.src_path), event_type="Création v1")

    def on_moved(self, event):
        if not event.is_directory:
            self.process_path(Path(event.dest_path), event_type="Renommage")


def wait_for_server(max_wait: int = 60) -> bool:
    print(
        f"⏳ [WATCHER] Attente du serveur FastAPI (max {max_wait}s)...",
        flush=True,
    )
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
    """🔍 Scanne tous les fichiers .md sous specs/ au démarrage et les envoie s'ils n'existent pas dans leur version actuelle en BDD."""
    if not wait_for_server():
        print("❌ [WATCHER] Serveur inaccessible, scan initial annulé", flush=True)
        return

    print(
        f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...",
        flush=True,
    )

    for file_path in WATCH_DIR.glob("**/*.md"):
        abs_path = file_path.resolve()

        if not is_valid_spec_file(abs_path):
            continue

        if is_file_already_in_db(abs_path):
            print(
                f"⏩ [WATCHER] Ignoré au démarrage (version actuelle déjà en BDD) : {abs_path.name}",
                flush=True,
            )
        else:
            print(
                f"🆕 [WATCHER] Nouvelle version détectée (absente de la BDD) : {abs_path.name}",
                flush=True,
            )
            Thread(
                target=handle_file_event, args=(abs_path,), daemon=True
            ).start()

    if CONSTITUTION_FILE.exists():
        abs_constitution = CONSTITUTION_FILE.resolve()
        if is_file_already_in_db(abs_constitution):
            print(
                f"⏩ [WATCHER] Ignoré au démarrage (version actuelle déjà en BDD) : constitution.md",
                flush=True,
            )
        else:
            print(
                f"🆕 [WATCHER] Nouvelle version de constitution.md détectée",
                flush=True,
            )
            Thread(
                target=handle_file_event, args=(abs_constitution,), daemon=True
            ).start()


# ============================================
# POINT D'ENTRÉE
# ============================================
if __name__ == "__main__":
    print(
        f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}",
        flush=True,
    )
    print(
        f"🎯 [WATCHER] Types d'artefacts autorisés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n",
        flush=True,
    )

    CONSTITUTION_FILE.parent.mkdir(parents=True, exist_ok=True)

    Thread(target=queue_worker, daemon=True).start()

    initial_scan()

    event_handler = SpecWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)

    constitution_dir = CONSTITUTION_FILE.parent.resolve()
    if constitution_dir.exists():
        observer.schedule(
            event_handler, str(constitution_dir), recursive=False
        )
        print(
            f"👀 [WATCHER] Surveillance aussi sur : {constitution_dir} (constitution.md)",
            flush=True,
        )

    observer.start()

    try:
        print("🟢 [WATCHER] En attente d'événements...\n", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
        observer.stop()
    observer.join()
# import os
# import sys
# import time
# from collections import defaultdict
# from pathlib import Path
# from queue import Queue
# from threading import Lock, Thread

# import requests
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

# # ============================================
# # CONFIGURATION CONSOLE & ENCODAGE (Windows)
# # ============================================
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")

# # ============================================
# # CONFIGURATION DE BASE & DÉTECTION SPECS
# # ============================================
# CURRENT_FILE = Path(__file__).resolve()

# # Hiérarchie des dossiers :
# # parents[0] = python/
# # parents[1] = scripts/
# # parents[2] = agentdocx-speckit/
# # parents[3] = StageTalan/
# STAGE_TALAN_DIR = (
#     CURRENT_FILE.parents[3]
#     if len(CURRENT_FILE.parents) > 3
#     else CURRENT_FILE.parents[2]
# )
# AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# # PRIORITÉ 1 : Variable d'environnement SPECKIT_WORKSPACE (extension VS Code)
# SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
# SPECKIT_SPECS_DIR = os.environ.get("SPECKIT_SPECS_DIR")
# SPECKIT_BACKEND_DIR = os.environ.get("SPECKIT_BACKEND_DIR")
# SPECKIT_SCRIPTS_DIR = os.environ.get("SPECKIT_SCRIPTS_DIR")

# if SPECKIT_WORKSPACE:
#     BASE_DIR = Path(SPECKIT_WORKSPACE)
#     print(f"[WATCHER] Utilisation du workspace depuis l'extension : {BASE_DIR}")
# else:
#     # Fallback : détection automatique (mode standalone)
#     print(f"[WATCHER] Mode standalone - détection automatique du workspace")
#     if (STAGE_TALAN_DIR / "specs").exists():
#         BASE_DIR = STAGE_TALAN_DIR
#     elif (AGENTDOCX_DIR / "specs").exists():
#         BASE_DIR = AGENTDOCX_DIR
#     else:
#         BASE_DIR = STAGE_TALAN_DIR

# if SPECKIT_SPECS_DIR:
#     WATCH_DIR = Path(SPECKIT_SPECS_DIR)
# else:
#     WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# # API Endpoints
# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Fichiers et dossiers à ignorer strictement
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# # Types d'artefacts autorisés à déclencher le pipeline (10 types)
# ALLOWED_ARTIFACT_TYPES = {
#     "spec",
#     "plan",
#     "tasks",
#     "task",
#     "constitution",
#     "requirements",
#     "contracts",
#     "data-model",
#     "research",
#     "quickstart",
#     "autres",
# }

# # File d'attente & verrous pour la synchronisation des événements
# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()

# _last_event_time = defaultdict(float)
# _DEBOUNCE_SECONDS = 2.0

# # Chemin constitution.md (dans .specify/memory)
# CONSTITUTION_FILE = BASE_DIR / ".specify" / "memory" / "constitution.md"


# # ============================================
# # UTILITAIRES POSIX
# # ============================================
# def sanitize_path_string(path_str: str) -> str:
#     """Nettoyage préventif des caractères de contrôle ASCII (0x00-0x1F) et conversion des backslashes Windows."""
#     clean_str = str(path_str)
#     clean_str = clean_str.replace("\\", "/")
#     for i in range(0, 32):
#         clean_str = clean_str.replace(chr(i), "")
#     return clean_str


# def to_posix_str(path_obj) -> str:
#     """Convertit un chemin (Path ou str) au format POSIX strict."""
#     if path_obj is None:
#         return ""
#     return sanitize_path_string(Path(path_obj).as_posix())


# # ============================================
# # VALIDATION STRUCTURELLE DU MARKDOWN (ANTI-TRONCATURE LLM)
# # ============================================
# def is_markdown_structurally_complete(content: str) -> bool:
#     """
#     Vérifie si le Markdown généré par Claude Code / Copilot / Aider est valide et complet :
#     1. Doit dépasser une longueur minimale (150 caractères).
#     2. Tous les blocs de code Markdown (```) doivent être fermés (nombre pair de ```).
#     3. Ne doit pas se terminer brutalement sur un titre ou une liste suspendue.
#     """
#     if not content or len(content.strip()) < 150:
#         return False

#     # 1. Vérification de la fermeture de tous les blocs de code (Mermaid, Python, etc.)
#     backtick_count = content.count("```")
#     if backtick_count % 2 != 0:
#         # Le LLM est actuellement en train de générer l'intérieur d'un bloc de code !
#         return False

#     # 2. Vérification de la dernière ligne non vide du document
#     lines = [line.strip() for line in content.splitlines() if line.strip()]
#     if not lines:
#         return False

#     last_line = lines[-1]
#     # Détection de génération interrompue en cours de frappe
#     if last_line in ("-", "*", "+", "1.", "#", "##", "###", "####", "#####", "######") or last_line.endswith("..."):
#         return False

#     return True


# # ============================================
# # LOGIQUE DE STABILISATION ET D'ENVOI
# # ============================================
# def wait_until_file_is_stable(
#     file_path: Path,
#     wait_seconds: float = 8.0,     # Temporisation de 8 secondes d'inactivité pour tolérer le streaming LLM
#     check_interval: float = 1.0,   # Vérification chaque seconde
#     max_timeout: float = 180.0,    # Timeout maximal étendu pour les très longues specs
#     min_size_bytes: int = 150      # Ignorer les stubs initiaux
# ) -> bool:
#     """⏳ Attend que l'outil d'écriture (ex: Claude Code / Copilot / Aider) termine la rédaction complète du fichier."""
#     if not file_path.exists():
#         return False

#     last_size = -1
#     stable_time = 0.0
#     total_time = 0.0

#     print(
#         f"⏳ [WATCHER] Attente de stabilisation/écriture IA (8s inactivité + structure MD) pour : {file_path.name}",
#         flush=True,
#     )

#     while total_time < max_timeout:
#         try:
#             if not file_path.exists():
#                 return False

#             current_size = file_path.stat().st_size

#             if current_size < min_size_bytes:
#                 time.sleep(check_interval)
#                 total_time += check_interval
#                 continue

#             with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
#                 content = f.read()

#             # Contrôle de structure Markdown (blocs de code fermés + ligne finale valide)
#             structurally_ok = is_markdown_structurally_complete(content)

#             # Requis : La taille reste inchangée ET la structure Markdown est valide
#             if current_size > 0 and current_size == last_size and structurally_ok:
#                 stable_time += check_interval
#             else:
#                 last_size = current_size
#                 stable_time = 0.0  # Réinitialise dès que le LLM écrit du texte ou ferme un bloc de code

#         except (OSError, PermissionError):
#             current_size = -1
#             stable_time = 0.0

#         if stable_time >= wait_seconds:
#             print(
#                 f"✅ [WATCHER] Fichier complété et stabilisé ({last_size} octets) : {file_path.name}",
#                 flush=True,
#             )
#             return True

#         time.sleep(check_interval)
#         total_time += check_interval

#     print(
#         f"⚠️ [WATCHER] Timeout de stabilisation dépassé pour : {file_path.name}",
#         flush=True,
#     )
#     return False


# def is_valid_spec_file(abs_path: Path) -> bool:
#     """Valide tout fichier .md situé sous specs/<projet_name>/... à n'importe quelle profondeur."""
#     # 1. Accepter le cas particulier constitution.md
#     if abs_path.resolve() == CONSTITUTION_FILE.resolve():
#         return True

#     # 2. Rejeter si ce n'est pas un fichier .md
#     if abs_path.suffix.lower() != ".md":
#         return False

#     # 3. Rejeter les fichiers et dossiers ignorés
#     if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#         return False

#     if any(
#         folder in abs_path.parts
#         for folder in IGNORED_FOLDERS
#         if folder != ".specify"
#     ):
#         return False

#     # 4. Vérifier qu'il appartient à un dossier projet sous WATCH_DIR (specs/)
#     try:
#         relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#         if len(relative_parts) >= 2:
#             return True
#     except ValueError:
#         return False

#     return False


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
#     """🗂️ Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
#     try:
#         file_path_posix = to_posix_str(file_path.resolve())
#         response = requests.get(
#             API_CHECK_URL, params={"file_path": file_path_posix}, timeout=3
#         )
#         if response.status_code == 200:
#             return response.json().get("exists_in_db", False)
#     except Exception as e:
#         print(
#             f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}",
#             flush=True,
#         )

#     return False


# def resolve_constitution_project_name() -> str:
#     """Détermine le projectName pour constitution.md :

#     1. Initialisation Specify (aucun projet sous specs/) -> Nom du workspace racine.
#     2. Modification liée à un projet (ex: specs/expense-tracker) -> Nom du dossier projet actif sous specs/.
#     """
#     root_project_name = (
#         BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
#     )
#     specs_dir = WATCH_DIR.resolve()

#     if not specs_dir.exists():
#         return root_project_name

#     # Récupération des dossiers de projets existants sous specs/
#     project_dirs = [
#         d
#         for d in specs_dir.iterdir()
#         if d.is_dir()
#         and d.name not in IGNORED_FOLDERS
#         and not d.name.startswith(".")
#     ]

#     if not project_dirs:
#         return root_project_name

#     def get_latest_mtime(folder: Path) -> float:
#         mtime = folder.stat().st_mtime
#         for item in folder.rglob("*"):
#             try:
#                 mtime = max(mtime, item.stat().st_mtime)
#             except OSError:
#                 pass
#         return mtime

#     latest_project_dir = max(project_dirs, key=get_latest_mtime)
#     return latest_project_dir.name


# def trigger_pipeline(file_path: Path):
#     """Envoie le fichier Markdown et le nom de projet à l'endpoint FastAPI /upload."""
#     abs_path = file_path.resolve()

#     try:
#         rel_path = abs_path.relative_to(BASE_DIR).as_posix()
#     except ValueError:
#         rel_path = abs_path.name

#     root_project_name = (
#         BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
#     )

#     # Traitement spécifique du projectName pour constitution.md
#     if (
#         abs_path.name.lower() == "constitution.md"
#         and ".specify" in abs_path.parts
#     ):
#         project_name = resolve_constitution_project_name()
#     else:
#         try:
#             relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#             if len(relative_parts) > 1:
#                 project_name = relative_parts[0]
#             else:
#                 project_name = root_project_name
#         except ValueError:
#             project_name = root_project_name

#     print(
#         f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})",
#         flush=True,
#     )

#     try:
#         with open(abs_path, "rb") as f:
#             files = {"file": (abs_path.name, f, "text/markdown")}
#             data = {"projectName": project_name}
#             response = requests.post(
#                 API_RUN_URL, files=files, data=data, timeout=None
#             )

#         if response.status_code in (200, 201):
#             print(
#                 f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n",
#                 flush=True,
#             )
#         elif response.status_code == 429:
#             print(
#                 f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}",
#                 flush=True,
#             )
#             file_queue.put(abs_path)
#         else:
#             print(
#                 f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n",
#                 flush=True,
#             )
#     except Exception as e:
#         print(
#             f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n",
#             flush=True,
#         )


# def queue_worker():
#     """👷 Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
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
#     """📥 Vérifie la stabilité (8s d'inactivité + structure MD) puis ajoute le fichier (création ou version v+1) à la file."""
#     abs_path = file_path.resolve()
#     now = time.time()

#     # Debounce : ignorer si le même fichier a été soumis très récemment
#     if now - _last_event_time[abs_path] < _DEBOUNCE_SECONDS:
#         return
#     _last_event_time[abs_path] = now

#     with pending_lock:
#         if abs_path in pending_files:
#             return
#         pending_files.add(abs_path)

#     if wait_until_file_is_stable(abs_path, wait_seconds=8.0):
#         print(
#             f"📥 [WATCHER] Fichier validé et complet ! Ajouté à la file d'attente : {abs_path.name}",
#             flush=True,
#         )
#         file_queue.put(abs_path)
#     else:
#         with pending_lock:
#             pending_files.discard(abs_path)


# # ============================================
# # WATCHER PRINCIPAL
# # ============================================
# class SpecWatcherHandler(FileSystemEventHandler):
#     """🔍 Gestionnaire d'événements du système de fichiers (Création, Modification version v+1...vN)."""

#     def process_path(self, file_path: Path, event_type: str = "Événement"):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             return

#         if abs_path == CONSTITUTION_FILE.resolve():
#             print(
#                 f"👁️ [WATCHER] [{event_type}] Constitution.md détecté : {abs_path.name}",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"👁️ [WATCHER] [{event_type}] Traitement déclenché pour : {abs_path.relative_to(WATCH_DIR.resolve())}",
#                 flush=True,
#             )

#         Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

#     def on_modified(self, event):
#         """Gestion native de la modification d'un fichier existant (Version +1, +2, ... +N)."""
#         if not event.is_directory:
#             self.process_path(Path(event.src_path), event_type="Modification v+1")

#     def on_created(self, event):
#         """Gestion de la création d'un nouveau fichier (Version initiale v1)."""
#         if not event.is_directory:
#             self.process_path(Path(event.src_path), event_type="Création v1")

#     def on_moved(self, event):
#         """Gestion du déplacement ou renommage de fichier."""
#         if not event.is_directory:
#             self.process_path(Path(event.dest_path), event_type="Renommage")


# def wait_for_server(max_wait: int = 60) -> bool:
#     """Attend que le serveur FastAPI soit prêt (endpoint status répond 200)."""
#     print(
#         f"⏳ [WATCHER] Attente du serveur FastAPI (max {max_wait}s)...",
#         flush=True,
#     )
#     start = time.time()
#     while time.time() - start < max_wait:
#         try:
#             response = requests.get(API_STATUS_URL, timeout=2)
#             if response.status_code == 200:
#                 print("✅ [WATCHER] Serveur FastAPI prêt", flush=True)
#                 return True
#         except Exception:
#             pass
#         time.sleep(1)
#     print("⚠️ [WATCHER] Timeout : serveur non disponible", flush=True)
#     return False


# def initial_scan():
#     """🔍 Scanne tous les fichiers .md sous specs/ au démarrage et les envoie si absents de la BDD."""
#     if not wait_for_server():
#         print("❌ [WATCHER] Serveur inaccessible, scan initial annulé", flush=True)
#         return

#     print(
#         f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...",
#         flush=True,
#     )

#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             continue

#         if is_file_already_in_db(abs_path):
#             print(
#                 f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}",
#                 flush=True,
#             )
#             Thread(
#                 target=handle_file_event, args=(abs_path,), daemon=True
#             ).start()

#     # Scan spécifique de constitution.md dans .specify/memory
#     if CONSTITUTION_FILE.exists():
#         abs_constitution = CONSTITUTION_FILE.resolve()
#         if is_file_already_in_db(abs_constitution):
#             print(
#                 f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : constitution.md",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"🆕 [WATCHER] Nouveau constitution.md détecté (absent de la BDD)",
#                 flush=True,
#             )
#             Thread(
#                 target=handle_file_event, args=(abs_constitution,), daemon=True
#             ).start()


# # ============================================
# # POINT D'ENTRÉE
# # ============================================
# if __name__ == "__main__":
#     print(
#         f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}",
#         flush=True,
#     )
#     print(
#         f"🎯 [WATCHER] Types d'artefacts autorisés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n",
#         flush=True,
#     )

#     # Garantit l'existence du dossier de constitution
#     CONSTITUTION_FILE.parent.mkdir(parents=True, exist_ok=True)

#     # Démarrage du worker en arrière-plan
#     Thread(target=queue_worker, daemon=True).start()

#     # Exécution du scan initial
#     initial_scan()

#     # Démarrage Watchdog pour specs/
#     event_handler = SpecWatcherHandler()
#     observer = Observer()
#     observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)

#     # Démarrage Watchdog pour .specify/memory (constitution.md)
#     constitution_dir = CONSTITUTION_FILE.parent.resolve()
#     if constitution_dir.exists():
#         observer.schedule(
#             event_handler, str(constitution_dir), recursive=False
#         )
#         print(
#             f"👀 [WATCHER] Surveillance aussi sur : {constitution_dir} (constitution.md)",
#             flush=True,
#         )

#     observer.start()

#     try:
#         print("🟢 [WATCHER] En attente d'événements...\n", flush=True)
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
#         observer.stop()
#     observer.join()
# import os
# import sys
# import time
# from collections import defaultdict
# from pathlib import Path
# from queue import Queue
# from threading import Lock, Thread

# import requests
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

# # ============================================
# # CONFIGURATION CONSOLE & ENCODAGE (Windows)
# # ============================================
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")

# # ============================================
# # CONFIGURATION DE BASE & DÉTECTION SPECS
# # ============================================
# CURRENT_FILE = Path(__file__).resolve()

# # Hiérarchie des dossiers :
# # parents[0] = python/
# # parents[1] = scripts/
# # parents[2] = agentdocx-speckit/
# # parents[3] = StageTalan/
# STAGE_TALAN_DIR = (
#     CURRENT_FILE.parents[3]
#     if len(CURRENT_FILE.parents) > 3
#     else CURRENT_FILE.parents[2]
# )
# AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# # PRIORITÉ 1 : Variable d'environnement SPECKIT_WORKSPACE (extension VS Code)
# SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
# SPECKIT_SPECS_DIR = os.environ.get("SPECKIT_SPECS_DIR")
# SPECKIT_BACKEND_DIR = os.environ.get("SPECKIT_BACKEND_DIR")
# SPECKIT_SCRIPTS_DIR = os.environ.get("SPECKIT_SCRIPTS_DIR")

# if SPECKIT_WORKSPACE:
#     BASE_DIR = Path(SPECKIT_WORKSPACE)
#     print(f"[WATCHER] Utilisation du workspace depuis l'extension : {BASE_DIR}")
# else:
#     # Fallback : détection automatique (mode standalone)
#     print(f"[WATCHER] Mode standalone - détection automatique du workspace")
#     if (STAGE_TALAN_DIR / "specs").exists():
#         BASE_DIR = STAGE_TALAN_DIR
#     elif (AGENTDOCX_DIR / "specs").exists():
#         BASE_DIR = AGENTDOCX_DIR
#     else:
#         BASE_DIR = STAGE_TALAN_DIR

# if SPECKIT_SPECS_DIR:
#     WATCH_DIR = Path(SPECKIT_SPECS_DIR)
# else:
#     WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# # API Endpoints
# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Fichiers et dossiers à ignorer strictement
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# # Types d'artefacts autorisés à déclencher le pipeline (10 types)
# ALLOWED_ARTIFACT_TYPES = {
#     "spec",
#     "plan",
#     "tasks",
#     "task",
#     "constitution",
#     "requirements",
#     "contracts",
#     "data-model",
#     "research",
#     "quickstart",
#     "autres",
# }

# # File d'attente & verrous pour la synchronisation des événements
# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()

# _last_event_time = defaultdict(float)
# _DEBOUNCE_SECONDS = 1.0

# # Chemin constitution.md (dans .specify/memory)
# CONSTITUTION_FILE = BASE_DIR / ".specify" / "memory" / "constitution.md"


# # ============================================
# # UTILITAIRES POSIX
# # ============================================
# def sanitize_path_string(path_str: str) -> str:
#     """Nettoyage préventif des caractères de contrôle ASCII (0x00-0x1F) et conversion des backslashes Windows."""
#     clean_str = str(path_str)
#     clean_str = clean_str.replace("\\", "/")
#     for i in range(0, 32):
#         clean_str = clean_str.replace(chr(i), "")
#     return clean_str


# def to_posix_str(path_obj) -> str:
#     """Convertit un chemin (Path ou str) au format POSIX strict."""
#     if path_obj is None:
#         return ""
#     return sanitize_path_string(Path(path_obj).as_posix())


# # ============================================
# # LOGIQUE DE STABILISATION ET D'ENVOI
# # ============================================
# def wait_until_file_is_stable(
#     file_path: Path,
#     wait_seconds: float = 4.0,     # Augmenté à 4.0s pour s'adapter aux pauses d'écriture LLM/Claude Code
#     check_interval: float = 0.8,   # Intervalle de vérification
#     max_timeout: float = 60.0,     # Délai maximal d'attente
#     min_size_bytes: int = 150      # Évite la prise en compte des stubs de création vifs/vides
# ) -> bool:
#     """⏳ Attend que l'outil d'écriture (ex: Claude Code / IDE) termine entièrement la rédaction du fichier."""
#     if not file_path.exists():
#         return False

#     last_size = -1
#     stable_time = 0.0
#     total_time = 0.0

#     print(
#         f"⏳ [WATCHER] Attente de stabilisation/écriture IA pour : {file_path.name}",
#         flush=True,
#     )

#     while stable_time < wait_seconds and total_time < max_timeout:
#         try:
#             if not file_path.exists():
#                 return False

#             current_size = file_path.stat().st_size

#             # Si le fichier est trop petit, l'écriture par l'IA commence à peine
#             if current_size < min_size_bytes:
#                 time.sleep(check_interval)
#                 total_time += check_interval
#                 continue

#             with open(file_path, "r", encoding="utf-8") as f:
#                 _ = f.read(100)
#         except (OSError, PermissionError):
#             current_size = -1

#         if current_size > 0 and current_size == last_size:
#             stable_time += check_interval
#         else:
#             last_size = current_size
#             stable_time = 0.0  # Réinitialise la temporisation si la taille évolue encore

#         time.sleep(check_interval)
#         total_time += check_interval

#     if stable_time >= wait_seconds:
#         print(
#             f"✅ [WATCHER] Fichier stabilisé ({last_size} octets) : {file_path.name}",
#             flush=True,
#         )
#         return True
#     else:
#         print(
#             f"⚠️ [WATCHER] Délai dépassé pour la stabilisation : {file_path.name}",
#             flush=True,
#         )
#         return False


# def is_valid_spec_file(abs_path: Path) -> bool:
#     """Valide tout fichier .md situé sous specs/<projet_name>/... à n'importe quelle profondeur."""
#     # 1. Accepter le cas particulier constitution.md
#     if abs_path.resolve() == CONSTITUTION_FILE.resolve():
#         return True

#     # 2. Rejeter si ce n'est pas un fichier .md
#     if abs_path.suffix.lower() != ".md":
#         return False

#     # 3. Rejeter les fichiers et dossiers ignorés
#     if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#         return False

#     if any(
#         folder in abs_path.parts
#         for folder in IGNORED_FOLDERS
#         if folder != ".specify"
#     ):
#         return False

#     # 4. Vérifier qu'il appartient à un dossier projet sous WATCH_DIR (specs/)
#     try:
#         relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#         if len(relative_parts) >= 2:
#             return True
#     except ValueError:
#         return False

#     return False


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
#     """🗂️ Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
#     try:
#         file_path_posix = to_posix_str(file_path.resolve())
#         response = requests.get(
#             API_CHECK_URL, params={"file_path": file_path_posix}, timeout=3
#         )
#         if response.status_code == 200:
#             return response.json().get("exists_in_db", False)
#     except Exception as e:
#         print(
#             f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}",
#             flush=True,
#         )

#     return False


# def resolve_constitution_project_name() -> str:
#     """Détermine le projectName pour constitution.md :

#     1. Initialisation Specify (aucun projet sous specs/) -> Nom du workspace racine.
#     2. Modification liée à un projet (ex: specs/expense-tracker) -> Nom du dossier projet actif sous specs/.
#     """
#     root_project_name = (
#         BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
#     )
#     specs_dir = WATCH_DIR.resolve()

#     if not specs_dir.exists():
#         return root_project_name

#     # Récupération des dossiers de projets existants sous specs/
#     project_dirs = [
#         d
#         for d in specs_dir.iterdir()
#         if d.is_dir()
#         and d.name not in IGNORED_FOLDERS
#         and not d.name.startswith(".")
#     ]

#     if not project_dirs:
#         return root_project_name

#     def get_latest_mtime(folder: Path) -> float:
#         mtime = folder.stat().st_mtime
#         for item in folder.rglob("*"):
#             try:
#                 mtime = max(mtime, item.stat().st_mtime)
#             except OSError:
#                 pass
#         return mtime

#     latest_project_dir = max(project_dirs, key=get_latest_mtime)
#     return latest_project_dir.name


# def trigger_pipeline(file_path: Path):
#     """Envoie le fichier Markdown et le nom de projet à l'endpoint FastAPI /upload."""
#     abs_path = file_path.resolve()

#     try:
#         rel_path = abs_path.relative_to(BASE_DIR).as_posix()
#     except ValueError:
#         rel_path = abs_path.name

#     root_project_name = (
#         BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
#     )

#     # Traitement spécifique du projectName pour constitution.md
#     if (
#         abs_path.name.lower() == "constitution.md"
#         and ".specify" in abs_path.parts
#     ):
#         project_name = resolve_constitution_project_name()
#     else:
#         try:
#             relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#             if len(relative_parts) > 1:
#                 project_name = relative_parts[0]
#             else:
#                 project_name = root_project_name
#         except ValueError:
#             project_name = root_project_name

#     print(
#         f"\n🚀 [WATCHER] Lancement du pipeline pour : {rel_path} (Projet: {project_name})",
#         flush=True,
#     )

#     try:
#         with open(abs_path, "rb") as f:
#             files = {"file": (abs_path.name, f, "text/markdown")}
#             data = {"projectName": project_name}
#             response = requests.post(
#                 API_RUN_URL, files=files, data=data, timeout=None
#             )

#         if response.status_code in (200, 201):
#             print(
#                 f"✅ [WATCHER] Pipeline exécuté avec succès pour : {rel_path}\n",
#                 flush=True,
#             )
#         elif response.status_code == 429:
#             print(
#                 f"⚠️ [WATCHER] Serveur occupé (429), réinsertion dans la file d'attente : {rel_path}",
#                 flush=True,
#             )
#             file_queue.put(abs_path)
#         else:
#             print(
#                 f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n",
#                 flush=True,
#             )
#     except Exception as e:
#         print(
#             f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n",
#             flush=True,
#         )


# def queue_worker():
#     """👷 Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
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
#     """📥 Vérifie la stabilité puis ajoute le fichier à la file d'attente (avec debounce)."""
#     abs_path = file_path.resolve()
#     now = time.time()

#     # Debounce : ignorer si le même fichier a été soumis très récemment
#     if now - _last_event_time[abs_path] < _DEBOUNCE_SECONDS:
#         return
#     _last_event_time[abs_path] = now

#     with pending_lock:
#         if abs_path in pending_files:
#             return
#         pending_files.add(abs_path)

#     if wait_until_file_is_stable(abs_path, wait_seconds=4.0):
#         print(
#             f"📥 [WATCHER] Fichier prêt ! Ajouté à la file d'attente : {abs_path.name}",
#             flush=True,
#         )
#         file_queue.put(abs_path)
#     else:
#         with pending_lock:
#             pending_files.discard(abs_path)


# # ============================================
# # WATCHER PRINCIPAL
# # ============================================
# class SpecWatcherHandler(FileSystemEventHandler):
#     """🔍 Gestionnaire d'événements du système de fichiers."""

#     def process_path(self, file_path: Path):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             return

#         if abs_path == CONSTITUTION_FILE.resolve():
#             print(
#                 f"👁️ [WATCHER] Constitution.md modifié/créé : {abs_path}",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"👁️ [WATCHER] Modification/Création détectée : {abs_path.relative_to(WATCH_DIR.resolve())}",
#                 flush=True,
#             )

#         Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

#     def on_modified(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_created(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_moved(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.dest_path))


# def wait_for_server(max_wait: int = 60) -> bool:
#     """Attend que le serveur FastAPI soit prêt (endpoint status/health répond 200)."""
#     print(
#         f"⏳ [WATCHER] Attente du serveur FastAPI (max {max_wait}s)...",
#         flush=True,
#     )
#     start = time.time()
#     while time.time() - start < max_wait:
#         try:
#             response = requests.get(API_STATUS_URL, timeout=2)
#             if response.status_code == 200:
#                 print("✅ [WATCHER] Serveur FastAPI prêt", flush=True)
#                 return True
#         except Exception:
#             pass
#         time.sleep(1)
#     print("⚠️ [WATCHER] Timeout : serveur non disponible", flush=True)
#     return False


# def initial_scan():
#     """🔍 Scanne tous les fichiers .md sous specs/ (profondeur infinie) au démarrage."""
#     if not wait_for_server():
#         print("❌ [WATCHER] Serveur inaccessible, scan initial annulé", flush=True)
#         return

#     print(
#         f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...",
#         flush=True,
#     )

#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             continue

#         if is_file_already_in_db(abs_path):
#             print(
#                 f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}",
#                 flush=True,
#             )
#             Thread(
#                 target=handle_file_event, args=(abs_path,), daemon=True
#             ).start()

#     # Scan spécifique de constitution.md dans .specify/memory
#     if CONSTITUTION_FILE.exists():
#         abs_constitution = CONSTITUTION_FILE.resolve()
#         if is_file_already_in_db(abs_constitution):
#             print(
#                 f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : constitution.md",
#                 flush=True,
#             )
#         else:
#             print(
#                 f"🆕 [WATCHER] Nouveau constitution.md détecté (absent de la BDD)",
#                 flush=True,
#             )
#             Thread(
#                 target=handle_file_event, args=(abs_constitution,), daemon=True
#             ).start()


# # ============================================
# # POINT D'ENTRÉE
# # ============================================
# if __name__ == "__main__":
#     print(
#         f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}",
#         flush=True,
#     )
#     print(
#         f"🎯 [WATCHER] Types d'artefacts autorisés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n",
#         flush=True,
#     )

#     # Garantit l'existence du dossier de constitution
#     CONSTITUTION_FILE.parent.mkdir(parents=True, exist_ok=True)

#     # Worker thread
#     Thread(target=queue_worker, daemon=True).start()

#     # Scan initial
#     initial_scan()

#     # Démarrage Watchdog pour specs/
#     event_handler = SpecWatcherHandler()
#     observer = Observer()
#     observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)

#     # Démarrage Watchdog pour .specify/memory (constitution.md)
#     constitution_dir = CONSTITUTION_FILE.parent.resolve()
#     if constitution_dir.exists():
#         observer.schedule(
#             event_handler, str(constitution_dir), recursive=False
#         )
#         print(
#             f"👀 [WATCHER] Surveillance aussi sur : {constitution_dir} (constitution.md)",
#             flush=True,
#         )

#     observer.start()

#     try:
#         print("🟢 [WATCHER] En attente d'événements...\n", flush=True)
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
#         observer.stop()
#     observer.join()
# import sys
# import time
# import requests
# import os
# from pathlib import Path
# from queue import Queue
# from threading import Thread, Lock
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# # ============================================
# # CONFIGURATION CONSOLE & ENCODAGE (Windows)
# # ============================================
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# # ============================================
# # CONFIGURATION DE BASE & DÉTECTION SPECS
# # ============================================
# CURRENT_FILE = Path(__file__).resolve()

# # Hiérarchie des dossiers :
# # parents[0] = python/
# # parents[1] = scripts/
# # parents[2] = agentdocx-speckit/
# # parents[3] = StageTalan/
# STAGE_TALAN_DIR = CURRENT_FILE.parents[3] if len(CURRENT_FILE.parents) > 3 else CURRENT_FILE.parents[2]
# AGENTDOCX_DIR = CURRENT_FILE.parents[2]

# # 🎯 PRIORITÉ 1 : Variable d'environnement SPECKIT_WORKSPACE (définie par l'extension VS Code)
# SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
# SPECKIT_SPECS_DIR = os.environ.get("SPECKIT_SPECS_DIR")
# SPECKIT_BACKEND_DIR = os.environ.get("SPECKIT_BACKEND_DIR")
# SPECKIT_SCRIPTS_DIR = os.environ.get("SPECKIT_SCRIPTS_DIR")

# if SPECKIT_WORKSPACE:
#     BASE_DIR = Path(SPECKIT_WORKSPACE)
#     print(f"[WATCHER] Utilisation du workspace depuis l'extension : {BASE_DIR}")
# else:
#     # Fallback : détection automatique (mode standalone)
#     print(f"[WATCHER] Mode standalone - détection automatique du workspace")
#     if (STAGE_TALAN_DIR / "specs").exists():
#         BASE_DIR = STAGE_TALAN_DIR
#     elif (AGENTDOCX_DIR / "specs").exists():
#         BASE_DIR = AGENTDOCX_DIR
#     else:
#         BASE_DIR = STAGE_TALAN_DIR

# if SPECKIT_SPECS_DIR:
#     WATCH_DIR = Path(SPECKIT_SPECS_DIR)
# else:
#     WATCH_DIR = BASE_DIR / "specs"

# # Sécurité : crée automatiquement le dossier 'specs' s'il n'existe pas encore
# WATCH_DIR.mkdir(parents=True, exist_ok=True)

# # API Endpoints
# API_RUN_URL = "http://127.0.0.1:8000/api/v1/pipeline/upload"
# API_STATUS_URL = "http://127.0.0.1:8000/api/v1/pipeline/status"
# API_CHECK_URL = "http://127.0.0.1:8000/api/v1/pipeline/check-file"

# # Fichiers et dossiers à ignorer strictement
# IGNORED_FILES = {"template.md", "spec-template.md"}
# IGNORED_FOLDERS = {"outputs", ".specify", ".git", "__pycache__", ".venv"}

# # 🎯 Types d'artefacts autorisés à déclencher le pipeline (10 types)
# ALLOWED_ARTIFACT_TYPES = {"spec", "plan", "tasks", "task", "constitution", "requirements", "contracts", "data-model", "research", "quickstart", "autres"}

# # 🎯 File d'attente & verrous pour la synchronisation des événements
# file_queue = Queue()
# pending_files = set()
# pending_lock = Lock()


# # ============================================
# # UTILITAIRES POSIX
# # ============================================
# def sanitize_path_string(path_str: str) -> str:
#     """
#     Nettoyage preventif de TOUS les caracteres de controle ASCII (0x00-0x1F)
#     et remplacement des backslashes Windows par des slashes POSIX.
#     """
#     clean_str = str(path_str)
#     clean_str = clean_str.replace("\\", "/")
#     for i in range(0, 32):
#         clean_str = clean_str.replace(chr(i), "")
#     return clean_str


# def to_posix_str(path_obj) -> str:
#     """
#     Convertit n'importe quel chemin (Path ou str) en format POSIX strict,
#     SANS caracteres de controle.
#     """
#     if path_obj is None:
#         return ""
#     return sanitize_path_string(Path(path_obj).as_posix())


# # ============================================
# # LOGIQUE DE STABILISATION ET D'ENVOI
# # ============================================
# def wait_until_file_is_stable(
#     file_path: Path, 
#     wait_seconds: float = 2.0, 
#     check_interval: float = 0.5,
#     max_timeout: float = 20.0
# ) -> bool:
#     """⏳ Attend que l'outil d'écriture (ex: Claude Code / IDE) termine la modification du fichier."""
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

# def is_valid_spec_file(abs_path: Path) -> bool:
#     """
#     Valide tout fichier .md situé sous specs/<projet_name>/... à n'importe quelle profondeur.
#     """
#     # 1. Accepter le cas particulier constitution.md
#     if abs_path.resolve() == CONSTITUTION_FILE.resolve():
#         return True

#     # 2. Rejeter si ce n'est pas un fichier .md
#     if abs_path.suffix.lower() != ".md":
#         return False

#     # 3. Rejeter les fichiers et dossiers ignorés
#     if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
#         return False

#     if any(folder in abs_path.parts for folder in IGNORED_FOLDERS if folder != ".specify"):
#         return False

#     # 4. Vérifier qu'il appartient à un dossier projet sous WATCH_DIR (specs/)
#     try:
#         relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#         # relative_parts[0] = nom du projet (ex: 001-course-management)
#         # relative_parts[1+] = sous-dossiers et fichier (ex: contracts/rest-api.md)
#         if len(relative_parts) >= 2:
#             return True
#     except ValueError:
#         return False

#     return False

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
#     """🗂️ Interroge l'API FastAPI pour savoir si le fichier existe déjà en BDD."""
#     try:
#         file_path_posix = to_posix_str(file_path.resolve())
#         response = requests.get(
#             API_CHECK_URL,
#             params={"file_path": file_path_posix},
#             timeout=3
#         )
#         if response.status_code == 200:
#             return response.json().get("exists_in_db", False)
#     except Exception as e:
#         print(f"⚠️ [WATCHER] Impossible de vérifier la BDD pour {file_path.name} : {e}", flush=True)
    
#     return False
# def resolve_constitution_project_name() -> str:
#     """
#     Détermine le projectName pour constitution.md :
#     1. Initialisation Specify (aucun projet sous specs/) -> Nom du workspace racine.
#     2. Modification liée à un projet (ex: specs/expense-tracker) -> Nom du dossier projet actif sous specs/.
#     """
#     root_project_name = BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"
#     specs_dir = WATCH_DIR.resolve()

#     if not specs_dir.exists():
#         return root_project_name

#     # Récupération des dossiers de projets existants sous specs/
#     project_dirs = [
#         d for d in specs_dir.iterdir()
#         if d.is_dir() and d.name not in IGNORED_FOLDERS and not d.name.startswith(".")
#     ]

#     # Cas 1 : Seule l'initialisation de specify a eu lieu (aucun projet sous specs/)
#     if not project_dirs:
#         return root_project_name

#     # Cas 2 : Un ou plusieurs projets existent -> Trouver le dossier projet le plus récemment actif
#     def get_latest_mtime(folder: Path) -> float:
#         mtime = folder.stat().st_mtime
#         for item in folder.rglob("*"):
#             try:
#                 mtime = max(mtime, item.stat().st_mtime)
#             except OSError:
#                 pass
#         return mtime

#     latest_project_dir = max(project_dirs, key=get_latest_mtime)
#     return latest_project_dir.name
# def trigger_pipeline(file_path: Path):
#     """Envoie le fichier Markdown et le nom de projet à l'endpoint FastAPI /upload."""
#     abs_path = file_path.resolve()
    
#     try:
#         rel_path = abs_path.relative_to(BASE_DIR).as_posix()
#     except ValueError:
#         rel_path = abs_path.name

#     root_project_name = BASE_DIR.name if BASE_DIR.name not in (".", "") else "Default Project"

#     # Traitement spécifique du projectName pour constitution.md
#     if abs_path.name.lower() == "constitution.md" and ".specify" in abs_path.parts:
#         project_name = resolve_constitution_project_name()
#     else:
#         try:
#             relative_parts = abs_path.relative_to(WATCH_DIR.resolve()).parts
#             if len(relative_parts) > 1:
#                 project_name = relative_parts[0]
#             else:
#                 project_name = root_project_name
#         except ValueError:
#             project_name = root_project_name

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
#             file_queue.put(abs_path)
#         else:
#             print(f"❌ [WATCHER] Erreur API ({response.status_code}) : {response.text}\n", flush=True)
#     except Exception as e:
#         print(f"❌ [WATCHER] Connexion impossible au serveur FastAPI : {e}\n", flush=True)
# def queue_worker():
#     """👷 Worker en arrière-plan traitant séquentiellement les fichiers Markdown de la file."""
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


# # ============================================
# # WATCHER PRINCIPAL
# # ============================================
# from collections import defaultdict
# import time

# _last_event_time = defaultdict(float)
# _DEBOUNCE_SECONDS = 1.0

# # Constitution file path (from .specify/memory)
# CONSTITUTION_FILE = BASE_DIR / ".specify" / "memory" / "constitution.md"

# def handle_file_event(file_path: Path):
#     """📥 Vérifie la stabilité puis ajoute le fichier à la file d'attente (avec debounce)."""
#     abs_path = file_path.resolve()
#     now = time.time()
    
#     # Debounce : ignorer si même fichier traité récemment
#     if now - _last_event_time[abs_path] < _DEBOUNCE_SECONDS:
#         return
#     _last_event_time[abs_path] = now
    
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


# # ============================================
# # WATCHER PRINCIPAL
# # ============================================
# class SpecWatcherHandler(FileSystemEventHandler):
#     """🔍 Gestionnaire d'événements du système de fichiers."""
    
#     def process_path(self, file_path: Path):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             return

#         if abs_path == CONSTITUTION_FILE.resolve():
#             print(f"👁️ [WATCHER] Constitution.md modifié/créé : {abs_path}", flush=True)
#         else:
#             print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.relative_to(WATCH_DIR.resolve())}", flush=True)

#         Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

#     def on_modified(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_created(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.src_path))

#     def on_moved(self, event):
#         if not event.is_directory:
#             self.process_path(Path(event.dest_path))
# # class SpecWatcherHandler(FileSystemEventHandler):
# #     """🔍 Gestionnaire d'événements du système de fichiers."""
    
# #     def process_path(self, file_path: Path):
# #         abs_path = file_path.resolve()

# #         # 1️⃣ Ignorer les dossiers système ou réservés (sauf .specify/memory pour constitution.md)
# #         if any(folder in abs_path.parts for folder in IGNORED_FOLDERS if folder != ".specify"):
# #             # Allow .specify/memory for constitution.md
# #             if ".specify" in abs_path.parts and "memory" in abs_path.parts:
# #                 pass  # Allow this specific path
# #             else:
# #                 return

# #         # 2️⃣ Ignorer les templates
# #         if abs_path.name in IGNORED_FILES or "template" in abs_path.name.lower():
# #             return

# #         # 3️⃣ Traiter les fichiers .md
# #         if abs_path.suffix.lower() == ".md":
# #             # Special handling for constitution.md from .specify/memory
# #             if abs_path == CONSTITUTION_FILE.resolve():
# #                 print(f"👁️ [WATCHER] Constitution.md modifié/créé : {abs_path}", flush=True)
# #                 Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()
# #                 return
            
# #             # Regular specs folder files
# #             clean_stem = abs_path.stem.lower().split('(')[0].split('_')[0].strip()
# #             if clean_stem not in ALLOWED_ARTIFACT_TYPES:
# #                 return

# #             print(f"👁️ [WATCHER] Modification/Création détectée : {abs_path.name}", flush=True)
# #             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()

# #     def on_modified(self, event):
# #         if not event.is_directory:
# #             self.process_path(Path(event.src_path))

# #     def on_created(self, event):
# #         if not event.is_directory:
# #             self.process_path(Path(event.src_path))

# #     def on_moved(self, event):
# #         if not event.is_directory:
# #             self.process_path(Path(event.dest_path))


# def wait_for_server(max_wait: int = 60) -> bool:
#     """Attend que le serveur FastAPI soit prêt (endpoint /health répond 200)."""
#     print(f"⏳ [WATCHER] Attente du serveur FastAPI (max {max_wait}s)...", flush=True)
#     start = time.time()
#     while time.time() - start < max_wait:
#         try:
#             response = requests.get(API_STATUS_URL, timeout=2)
#             if response.status_code == 200:
#                 print("✅ [WATCHER] Serveur FastAPI prêt", flush=True)
#                 return True
#         except Exception:
#             pass
#         time.sleep(1)
#     print("⚠️ [WATCHER] Timeout : serveur non disponible", flush=True)
#     return False


# def initial_scan():
#     """🔍 Scanne tous les fichiers .md sous specs/ (profondeur infinie) au démarrage."""
#     if not wait_for_server():
#         print("❌ [WATCHER] Serveur inaccessible, scan initial annulé", flush=True)
#         return
    
#     print(f"\n🔍 [WATCHER] Scan initial du dossier {WATCH_DIR.resolve()}...", flush=True)
    
#     for file_path in WATCH_DIR.glob("**/*.md"):
#         abs_path = file_path.resolve()

#         if not is_valid_spec_file(abs_path):
#             continue

#         if is_file_already_in_db(abs_path):
#             print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : {abs_path.name}", flush=True)
#         else:
#             print(f"🆕 [WATCHER] Nouveau fichier détecté (absent de la BDD) : {abs_path.name}", flush=True)
#             Thread(target=handle_file_event, args=(abs_path,), daemon=True).start()
    
#     # Scan spécifique de constitution.md dans .specify/memory
#     if CONSTITUTION_FILE.exists():
#         abs_constitution = CONSTITUTION_FILE.resolve()
#         if is_file_already_in_db(abs_constitution):
#             print(f"⏩ [WATCHER] Ignoré au démarrage (déjà en BDD) : constitution.md", flush=True)
#         else:
#             print(f"🆕 [WATCHER] Nouveau constitution.md détecté (absent de la BDD)", flush=True)
#             Thread(target=handle_file_event, args=(abs_constitution,), daemon=True).start()
# # ============================================
# # POINT D'ENTRÉE
# # ============================================
# if __name__ == "__main__":
#     print(f"👀 [WATCHER] Surveillance active sur le dossier : {WATCH_DIR.resolve()}", flush=True)
#     print(f"🎯 [WATCHER] Types d'artefacts autorisés : {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}\n", flush=True)
    
#     # Ensure constitution directory exists
#     CONSTITUTION_FILE.parent.mkdir(parents=True, exist_ok=True)

#     # Worker thread
#     Thread(target=queue_worker, daemon=True).start()

#     # Scan initial
#     initial_scan()

#     # Démarrage Watchdog pour specs/
#     event_handler = SpecWatcherHandler()
#     observer = Observer()
#     observer.schedule(event_handler, str(WATCH_DIR.resolve()), recursive=True)
    
#     # Démarrage Watchdog pour .specify/memory (constitution.md)
#     constitution_dir = CONSTITUTION_FILE.parent.resolve()
#     if constitution_dir.exists():
#         observer.schedule(event_handler, str(constitution_dir), recursive=False)
#         print(f"👀 [WATCHER] Surveillance aussi sur : {constitution_dir} (constitution.md)", flush=True)
    
#     observer.start()

#     try:
#         print("🟢 [WATCHER] En attente d'événements...\n", flush=True)
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n🛑 [WATCHER] Arrêt de la surveillance.", flush=True)
#         observer.stop()
#     observer.join()