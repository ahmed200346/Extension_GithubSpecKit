import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base

import app.models  

# Import du router pipeline (BDD & LangGraph)
from app.api.v1.endpoints import pipeline

# 1. Création automatique des tables BDD si elles n'existent pas
Base.metadata.create_all(bind=engine)


# 2. Initialisation UNIQUE de FastAPI
app = FastAPI(
    title="Spec Kit Extension - AgentDocx API",
    version="1.0.0",
    description="API FastAPI d'orchestration Multi-Agents LangGraph pour Spec Kit"
)

# 3. Configuration CORS (Indispensable pour autoriser React sur http://localhost:3000 ou 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Inclusion du Router Pipeline 
# -> Prefix /api/v1/docs : Requis par le Frontend React (AddDocument.jsx & Documents.jsx)
app.include_router(pipeline.router, prefix="/api/v1/docs", tags=["Documents & Pipeline Frontend"])

# -> Prefix /api/v1/pipeline : Conservé pour vos scripts CLI, Watcher ou outils externes
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline CLI"])


# 5. Endpoints de santé (Health Checks)
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "SpecKit Extension API is running!", 
        "swagger_docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
# import os
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.config import settings
# from app.database import engine, Base


# import app.models  

# # Import du router pipeline (qui contient la logique BDD & LangGraph)
# from app.api.v1.endpoints import pipeline

# # 1. Création automatique des tables BDD si elles n'existent pas
# Base.metadata.create_all(bind=engine)


# # 3. Initialisation UNIQUE de FastAPI
# app = FastAPI(
#     title="Spec Kit Extension - AgentDocx API",
#     version="1.0.0",
#     description="API FastAPI d'orchestration Multi-Agents LangGraph pour Spec Kit"
# )

# # 4. Configuration CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 5. Inclusion du Router Pipeline (Incorpore /status, /run et la BDD)
# app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])


# # 6. Endpoints de santé (Health Checks)
# @app.get("/", tags=["Health"])
# async def root():
#     return {
#         "message": "SpecKit Extension API is running!", 
#         "docs_url": "/docs"
#     }


# @app.get("/health", tags=["Health"])
# async def health():
#     return {"status": "ok", "version": "1.0.0"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
