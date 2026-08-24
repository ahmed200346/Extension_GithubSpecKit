# app/config.py
import os
from pathlib import Path
from typing import Optional, Literal
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

    # --- LLM PROVIDER CONFIGURATION ---
    # Supported providers: "ollama", "openai", "anthropic", "groq", "openai_compatible", "huggingface", "nvidia", "gemini"
    LLM_PROVIDER: Literal["ollama", "openai", "anthropic", "groq", "openai_compatible", "huggingface", "nvidia", "gemini"] = "ollama"

    # Gemini settings (Official SDK)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_TEMPERATURE: float = 1.0
    GEMINI_MAX_OUTPUT_TOKENS: int = 8192

    # Ollama settings (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:31b-cloud"
    OLLAMA_API_KEY: Optional[str] = None

    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = None

    # Anthropic settings
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Groq settings (OpenAI-compatible)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # NVIDIA NIM settings (OpenAI-compatible)
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Hugging Face settings (OpenAI-compatible inference API)
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    HUGGINGFACE_BASE_URL: str = "https://api-inference.huggingface.co/v1"

    # Generic OpenAI-compatible API settings
    OPENAI_COMPATIBLE_API_KEY: Optional[str] = None
    OPENAI_COMPATIBLE_MODEL: str = "gpt-4o"
    OPENAI_COMPATIBLE_BASE_URL: Optional[str] = None

    PDF_STORAGE_DIR: str = "./storage/pdfs"
    LOG_LEVEL: str = "INFO"

    # --- TARGET PROJECT CONFIGURATION ---
    # Path to the project being worked on (where current-task.json should be watched)
    TARGET_PROJECT_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),  # Convertir en string pour compatibilité
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # Ignorer la casse des variables d'environnement
    )

settings = Settings()
