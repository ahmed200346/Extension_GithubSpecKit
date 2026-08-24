# app/core/clients/client_ollama.py
"""
client_ollama.py – Client LLM spécialisé pour Ollama

Module dédié à la gestion des connexions Ollama.
- Client OpenAI-compatible pour structuration JSON/Pydantic
- Client natif Ollama pour streaming et contrôle bas-niveau
- Applique les configurations de timeout centralisées depuis config.py
"""

import logging
from typing import Optional
from openai import OpenAI, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClientManager:
    """Gestionnaire du client Ollama avec gestion d'erreurs et retry"""
    
    def __init__(self):
        self._openai_client: Optional[OpenAI] = None
        self._native_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialise les clients Ollama au démarrage"""
        try:
            # Client OpenAI-compatible (pour requêtes structurées)
            self._openai_client = OpenAI(
                base_url=f"{settings.OLLAMA_BASE_URL}/v1",
                api_key="ollama",
                timeout=settings.LLM_REQUEST_TIMEOUT,
                max_retries=settings.LLM_RETRY_ATTEMPTS,
            )
            logger.info(f"✓ Client Ollama OpenAI-compatible initialisé: {settings.OLLAMA_BASE_URL}")
            
            # Client natif Ollama
            try:
                import ollama
                self._native_client = ollama.Client(
                    host=settings.OLLAMA_BASE_URL,
                    timeout=settings.LLM_REQUEST_TIMEOUT,
                )
                logger.info(f"✓ Client Ollama natif initialisé: {settings.OLLAMA_BASE_URL}")
            except ImportError:
                logger.warning("⚠ Bibliothèque 'ollama' non installée. Seul le client OpenAI-compatible est disponible.")
                self._native_client = None
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation d'Ollama: {e}")
            raise
    
    def get_openai_client(self) -> OpenAI:
        """Retourne le client OpenAI-compatible Ollama"""
        if self._openai_client is None:
            self._initialize()
        return self._openai_client
    
    def get_native_client(self):
        """Retourne le client natif Ollama (optionnel)"""
        return self._native_client
    
    def get_model_name(self) -> str:
        """Retourne le nom du modèle Ollama configuré"""
        return settings.OLLAMA_MODEL
    
    def verify_connection(self) -> bool:
        """Vérifie que le serveur Ollama est accessible"""
        try:
            if self._native_client:
                # Utiliser le client natif pour un ping léger
                response = self._native_client.list()
                logger.info("✓ Connexion Ollama vérifiée")
                return True
            else:
                # Fallback avec le client OpenAI
                response = self._openai_client.models.list()
                logger.info("✓ Connexion Ollama vérifiée (via OpenAI)")
                return True
        except (APIConnectionError, APITimeoutError) as e:
            logger.error(f"✗ Impossibile de se connecter à Ollama: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Erreur lors de la vérification de la connexion Ollama: {e}")
            return False


# Instance globale (singleton)
_ollama_manager: Optional[OllamaClientManager] = None


def get_ollama_client() -> OpenAI:
    """Retourne le client Ollama OpenAI-compatible"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaClientManager()
    return _ollama_manager.get_openai_client()


def get_ollama_native_client():
    """Retourne le client natif Ollama"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaClientManager()
    return _ollama_manager.get_native_client()


def get_ollama_model() -> str:
    """Retourne le nom du modèle Ollama"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaClientManager()
    return _ollama_manager.get_model_name()


def verify_ollama_connection() -> bool:
    """Vérifie la connexion au serveur Ollama"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaClientManager()
    return _ollama_manager.verify_connection()
