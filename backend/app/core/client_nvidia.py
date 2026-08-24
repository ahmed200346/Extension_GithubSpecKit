# app/core/client_nvidia.py
"""
client_nvidia.py — Client LLM spécialisé pour NVIDIA API
"""

import logging
from typing import Optional
from openai import OpenAI, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)

# Configuration par défaut (mirrore l'ancienne config Be)
DEFAULT_TIMEOUT = 600
DEFAULT_RETRY_ATTEMPTS = 3

class NvidiaClientManager:
    """Gestionnaire du client NVIDIA avec gestion d'erreurs et retry"""

    def __init__(self):
        self._openai_client: Optional[OpenAI] = None
        self._initialize()

    def _initialize(self):
        """Initialise le client NVIDIA au démarrage"""
        try:
            self._openai_client = OpenAI(
                base_url=settings.NVIDIA_BASE_URL,
                api_key=settings.NVIDIA_API_KEY,
                timeout=DEFAULT_TIMEOUT,
                max_retries=DEFAULT_RETRY_ATTEMPTS,
            )
            logger.info(f"✓ Client NVIDIA OpenAI-compatible initialisé: {settings.NVIDIA_BASE_URL}")
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation de NVIDIA: {e}")
            raise

    def get_openai_client(self) -> OpenAI:
        """Retourne le client OpenAI-compatible NVIDIA"""
        if self._openai_client is None:
            self._initialize()
        return self._openai_client

    def get_model_name(self) -> str:
        """Retourne le nom du modèle NVIDIA configuré"""
        return settings.NVIDIA_MODEL

    def verify_connection(self) -> bool:
        """Vérifie que la connexion à NVIDIA API est valide"""
        try:
            self._openai_client.models.list()
            logger.info("✓ Connexion NVIDIA vérifiée")
            return True
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"✗ Timeout ou erreur de connexion NVIDIA: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Erreur lors de la vérification NVIDIA: {e}")
            return False

# Instance globale (singleton)
_nvidia_manager: Optional[NvidiaClientManager] = None

def get_nvidia_client() -> OpenAI:
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.get_openai_client()

def get_nvidia_model() -> str:
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.get_model_name()

def verify_nvidia_connection() -> bool:
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.verify_connection()
