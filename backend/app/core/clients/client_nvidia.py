# app/core/clients/client_nvidia.py
"""
client_nvidia.py – Client LLM spécialisé pour NVIDIA API

Module dédié à la gestion des connexions NVIDIA API.
- Client OpenAI-compatible (NVIDIA expose une API OpenAI-compatible)
- Gestion d'erreurs et retry avec configuration centralisée
- Applique les configurations de timeout centralisées depuis config.py
"""

import logging
from typing import Optional
from openai import OpenAI, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


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
                timeout=settings.LLM_REQUEST_TIMEOUT,
                max_retries=settings.LLM_RETRY_ATTEMPTS,
            )
            logger.info(f"✓ Client NVIDIA OpenAI-compatible initialisé")
            logger.info(f"  Base URL: {settings.NVIDIA_BASE_URL}")
            logger.info(f"  Modèle: {settings.NVIDIA_MODEL}")
            logger.info(f"  Timeout: {settings.LLM_REQUEST_TIMEOUT}s")
            logger.info(f"  Retry attempts: {settings.LLM_RETRY_ATTEMPTS}")
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation de NVIDIA: {e}")
            raise
    
    def get_openai_client(self) -> OpenAI:
        """Retourne le client OpenAI compatible NVIDIA"""
        if self._openai_client is None:
            self._initialize()
        return self._openai_client
    
    def get_model_name(self) -> str:
        """Retourne le nom du modèle NVIDIA configuré"""
        return settings.NVIDIA_MODEL
    
    def verify_connection(self) -> bool:
        """Vérifie que la connexion à NVIDIA API est valide"""
        try:
            response = self._openai_client.models.list()
            models = list(response)
            logger.info(f"✓ Connexion NVIDIA vérifiée. Modèles accessibles: {len(models)}")
            
            # Vérifier que le modèle configuré est disponible
            available_models = [m.id for m in models]
            if settings.NVIDIA_MODEL in available_models:
                logger.info(f"✓ Modèle '{settings.NVIDIA_MODEL}' est disponible")
                return True
            else:
                logger.warning(
                    f"⚠ Modèle '{settings.NVIDIA_MODEL}' non trouvé. "
                    f"Modèles disponibles: {available_models}"
                )
                return True  # Connexion OK, mais modèle peut ne pas être accessible
        
        except APITimeoutError as e:
            logger.error(f"✗ Timeout lors de la vérification de la connexion NVIDIA: {e}")
            return False
        except APIConnectionError as e:
            logger.error(f"✗ Erreur de connexion à NVIDIA API: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Erreur lors de la vérification de la connexion NVIDIA: {e}")
            return False
    
    def create_request_config(self) -> dict:
        """Crée la configuration standard pour les requêtes NVIDIA"""
        return {
            "temperature": settings.NVIDIA_TEMPERATURE,
            "max_tokens": settings.NVIDIA_MAX_TOKENS,
            "top_p": 0.95,
            "timeout": settings.LLM_REQUEST_TIMEOUT,
        }
    
    def apply_timeout_config(self):
        """Applique les configurations de timeout centralisées"""
        logger.info(
            f"ℹ Configuration de timeout appliquée: "
            f"request_timeout={settings.LLM_REQUEST_TIMEOUT}s, "
            f"retry_attempts={settings.LLM_RETRY_ATTEMPTS}"
        )


# Instance globale (singleton)
_nvidia_manager: Optional[NvidiaClientManager] = None


def get_nvidia_client() -> OpenAI:
    """Retourne le client NVIDIA OpenAI-compatible"""
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.get_openai_client()


def get_nvidia_model() -> str:
    """Retourne le nom du modèle NVIDIA"""
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.get_model_name()


def verify_nvidia_connection() -> bool:
    """Vérifie la connexion à NVIDIA API"""
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.verify_connection()


def get_nvidia_request_config() -> dict:
    """Retourne la configuration standard pour les requêtes NVIDIA"""
    global _nvidia_manager
    if _nvidia_manager is None:
        _nvidia_manager = NvidiaClientManager()
    return _nvidia_manager.create_request_config()