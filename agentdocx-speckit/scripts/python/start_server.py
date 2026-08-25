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

# 3. INITIALISATION FASTAPI — assurer que TicketManager logs sont visibles
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
logging.getLogger("app.agents.ticket_agent").setLevel(logging.INFO)
logging.getLogger("app.agents.ticket_agent.manager").setLevel(logging.INFO)
logging.getLogger("app.agents.ticket_agent.watcher").setLevel(logging.INFO)
logging.getLogger("app.agents.ticket_agent.sync_service").setLevel(logging.INFO)

import uvicorn
from app.main import app # 🎯 IMPORTANT: On importe l'app configurée dans main.py (incluant tous les routers et lifespan=ticket_agent_lifespan)

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

# 4. DEMARRAGE UVICORN — aligné avec BrancheMain (logique principale identique)
#
# IMPORTANT : on lance directement l'application réelle définie dans
# app/main.py (app.main:app). Cette application inclut TOUS les routers,
# y compris tickets.router et le lifespan ticket_agent_lifespan (TicketManager).
# Ne PAS créer d'instance FastAPI locale ici : app.main est la seule source de vérité.
if __name__ == "__main__":
    import uvicorn

    print(f"[StartServer] Démarrage du serveur Uvicorn via app.main:app (TicketManager lifespan actif)...", flush=True)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        app_dir=str_backend_dir,
        reload_dirs=[str_backend_dir, str_script_dir],
        log_level="info",
    )
