# app/config.py
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Détermine le répertoire de base du projet
# Si WORKSPACE_DIR est défini (par l'extension), l'utiliser, sinon calculer depuis __file__
if os.environ.get("WORKSPACE_DIR"):
    BASE_DIR = Path(os.environ["WORKSPACE_DIR"])
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://speckit:speckit@localhost:5432/speckit"  # Valeur par défaut
    OPENAI_API_KEY: Optional[str] = None
    
    # --- CONFIGURATION FOURNISSEUR LLM ---
    LLM_PROVIDER: str = "ollama"  # Peut être : ollama, gemini, nvidia
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:31b-cloud"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_MODEL: str = "nvidia/nemotron"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    
    PDF_STORAGE_DIR: str = "./storage/pdfs"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),  # Convertir en string pour compatibilité
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # Ignorer la casse des variables d'environnement
    )

settings = Settings()