import os
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """Configuration centralisée pour l'application Task Management + LLM Providers"""
    
    # Application
    APP_NAME: str = "Task Management API"
    DATABASE_URL: str = "sqlite+aiosqlite:///./tasks.db"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    
    # LLM Provider Selection (ollama, gemini, nvidia)
    LLM_PROVIDER: Literal["ollama", "gemini", "nvidia"] = "ollama"
    
    # ============================================================================
    # CONFIGURATION DE TIMEOUT CENTRALISÉE (Commune à tous les providers)
    # ============================================================================
    # Ces valeurs s'appliquent à TOUS les clients LLM (Ollama, Gemini, NVIDIA)
    LLM_REQUEST_TIMEOUT: int = 60  # Timeout pour une requête simple (secondes)
    LLM_LONG_REQUEST_TIMEOUT: int = 300  # Timeout pour requêtes lourdes (5 min)
    LLM_CONNECTION_TIMEOUT: int = 10  # Timeout de connexion initiale
    LLM_RETRY_ATTEMPTS: int = 3  # Nombre de tentatives en cas d'erreur
    LLM_RETRY_DELAY: float = 1.0  # Délai entre les tentatives (secondes)
    
    # ============================================================================
    # OLLAMA Configuration
    # ============================================================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:31b-cloud"
    OLLAMA_KEEP_ALIVE: str = "5m"  # Délai avant arrêt du modèle en mémoire
    
    # ============================================================================
    # GEMINI Configuration
    # ============================================================================
    GEMINI_API_KEY: str = "votre_cle_api_gemini"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    
    # ============================================================================
    # NVIDIA Configuration
    # ============================================================================
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "meta/llama-3.1-70b-instruct"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_TEMPERATURE: float = 0.7
    NVIDIA_MAX_TOKENS: int = 2048
    
    # ============================================================================
    # Stockage & Logging
    # ============================================================================
    PDF_STORAGE_DIR: str = "./storage/pdfs"
    TARGET_PROJECT_PATH: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()


def get_active_provider() -> str:
    """Retourne le provider actif depuis la configuration"""
    return settings.LLM_PROVIDER
