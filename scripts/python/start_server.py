import os
import sys
from pathlib import Path

# 1. Configurer l'encodage et l'affichage immédiat des logs (Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# 2. LOCALISATION ET NAVIGATION DEPUIS StageTalan
CURRENT_FILE = Path(__file__).resolve() # .../StageTalan/agentdocx-speckit/scripts/python/start_server.py
SCRIPT_DIR = CURRENT_FILE.parent        # .../scripts/python
RACINE_DIR = CURRENT_FILE.parents[3] # .../StageTalan
AGENTDOCX_DIR = CURRENT_FILE.parents[2]   # .../agentdocx-speckit

# 🎯 Support de la variable d'environnement SPECKIT_WORKSPACE (définie par l'extension VS Code)
SPECKIT_WORKSPACE = os.environ.get("SPECKIT_WORKSPACE")
if SPECKIT_WORKSPACE:
    RACINE_DIR = Path(SPECKIT_WORKSPACE)
    print(f"[VERIF] Workspace depuis extension VS Code : {RACINE_DIR}", flush=True)

print(f"[VERIF] Dossier StageTalan : {RACINE_DIR}", flush=True)

# Détection stricte : backend situé sous StageTalan (ou secours sous agentdocx-speckit)
if (RACINE_DIR / "backend" / "app").exists():
    TARGET_BACKEND = RACINE_DIR / "backend"
    print(f"[VERIF OK] Dossier 'app' trouvé sous StageTalan : {TARGET_BACKEND / 'app'}", flush=True)
elif (AGENTDOCX_DIR / "backend" / "app").exists():
    TARGET_BACKEND = AGENTDOCX_DIR / "backend"
    print(f"[VERIF OK] Dossier 'app' trouvé sous agentdocx-speckit : {TARGET_BACKEND / 'app'}", flush=True)
else:
    # Recherche ascendante globale par sécurité
    TARGET_BACKEND = None
    for p in CURRENT_FILE.parents:
        if (p / "backend" / "app").exists():
            TARGET_BACKEND = p / "backend"
            print(f"[VERIF OK] Recherche ascendante trouve : {TARGET_BACKEND}", flush=True)
            break

if not TARGET_BACKEND:
    print(f"[ERREUR CRITIQUE] Impossible de localiser le dossier backend sous {RACINE_DIR}", flush=True)
    sys.exit(1)

str_backend_dir = str(TARGET_BACKEND)
str_script_dir = str(SCRIPT_DIR)

# Force l'injection du dossier StageTalan/backend dans sys.path[0]
if str_backend_dir in sys.path:
    sys.path.remove(str_backend_dir)
sys.path.insert(0, str_backend_dir)

if str_script_dir not in sys.path:
    sys.path.insert(0, str_script_dir)

# Variables d'environnement pour Uvicorn et processus enfants Windows
os.environ["PYTHONPATH"] = str_backend_dir + os.pathsep + str_script_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
os.chdir(str_backend_dir)

print(f"[StartServer] sys.path[0] pointé sur : {sys.path[0]}", flush=True)

# 3. INITIALISATION FASTAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import engine, Base
import app.models  
from app.api.v1.endpoints import pipeline

# Base de données : Création automatique des tables
Base.metadata.create_all(bind=engine)

# Instance de l'application FastAPI
app = FastAPI(
    title="Spec Kit Extension - AgentDocx API",
    version="1.0.0",
    description="API FastAPI d'orchestration Multi-Agents LangGraph pour Spec Kit"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ Global exception handler : capture TOUTES les exceptions et retourne le traceback complet
from fastapi.responses import JSONResponse
from fastapi import Request
import traceback as tb_module

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb_str = "".join(tb_module.format_exception(type(exc), exc, exc.__traceback__))
    print(f"❌ [GLOBAL EXCEPTION] {request.method} {request.url}:\n{tb_str}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur: {str(exc)}\nTraceback:\n{tb_str}"}
    )

# Inclusion des Routers
app.include_router(pipeline.router, prefix="/api/v1/docs", tags=["Documents & Pipeline Frontend"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline CLI"])

# Endpoints de Santé (Health Checks)
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "SpecKit Extension API is running!", 
        "swagger_docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}

# 4. DEMARRAGE UVICORN
if __name__ == "__main__":
    print(f"[StartServer] Démarrage du serveur Uvicorn via start_server:app...", flush=True)
    
    uvicorn.run(
        "start_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        app_dir=str_script_dir,
        reload_dirs=[str_backend_dir, str_script_dir]
    )
# import os
# import sys
# from pathlib import Path
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

# # 1. Configurer l'encodage et l'affichage immédiat des logs (Windows)
# if hasattr(sys.stdout, "reconfigure"):
#     sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
# if hasattr(sys.stderr, "reconfigure"):
#     sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')

# # 2. LOCALISATION DYNAMIQUE DU DOSSIER REEL DU BACKEND
# CURRENT_FILE = Path(__file__).resolve()
# SCRIPT_DIR = CURRENT_FILE.parent  # scripts/python

# # On remonte d'au moins 2 niveaux pour balayer la RACINE du projet
# PROJECT_ROOT = CURRENT_FILE.parents[2] if len(CURRENT_FILE.parents) > 2 else CURRENT_FILE.parent

# def find_backend_dir(root: Path) -> Path:
#     """
#     Recherche automatiquement le dossier contenant le package 'app/config.py'.
#     """
#     # Test 1 : Vérification rapide sous root/backend ou root
#     for candidate in [root / "backend", root]:
#         if (candidate / "app" / "config.py").exists():
#             return candidate

#     # Test 2 : Recherche récursive dans tout le projet
#     for path in root.rglob("config.py"):
#         if path.parent.name == "app":
#             return path.parent.parent

#     return root

# BACKEND_DIR = find_backend_dir(PROJECT_ROOT)
# str_backend_dir = str(BACKEND_DIR)
# str_script_dir = str(SCRIPT_DIR)

# print(f"[StartServer] Racine backend détectée : {str_backend_dir}", flush=True)

# # 3. Injection dans sys.path et PYTHONPATH AVANT toute importation
# for d in [str_backend_dir, str_script_dir]:
#     if d not in sys.path:
#         sys.path.insert(0, d)

# os.environ["PYTHONPATH"] = str_backend_dir + os.pathsep + str_script_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
# os.chdir(str_backend_dir)

# # =========================================================================
# # 4. INITIALISATION DE FASTAPI (Importations désormais garanties)
# # =========================================================================
# from app.config import settings
# from app.database import engine, Base
# import app.models  
# from app.api.v1.endpoints import pipeline

# # Base de données : Création automatique des tables
# Base.metadata.create_all(bind=engine)

# # Instance de l'application FastAPI
# app = FastAPI(
#     title="Spec Kit Extension - AgentDocx API",
#     version="1.0.0",
#     description="API FastAPI d'orchestration Multi-Agents LangGraph pour Spec Kit"
# )

# # Configuration CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Inclusion des Routers
# app.include_router(pipeline.router, prefix="/api/v1/docs", tags=["Documents & Pipeline Frontend"])
# app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline CLI"])

# # Endpoints de Santé (Health Checks)
# @app.get("/", tags=["Health"])
# async def root():
#     return {
#         "message": "SpecKit Extension API is running!", 
#         "swagger_docs": "/docs"
#     }

# @app.get("/health", tags=["Health"])
# async def health():
#     return {"status": "ok", "version": "1.0.0"}

# # =========================================================================
# # 5. DEMARRAGE DU SERVEUR UVICORN
# # =========================================================================
# if __name__ == "__main__":
#     print(f"[StartServer] Démarrage du serveur Uvicorn via start_server:app...", flush=True)
    
#     uvicorn.run(
#         "start_server:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=True,
#         app_dir=str_script_dir,
#         reload_dirs=[str_backend_dir, str_script_dir]
#     )
