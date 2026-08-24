# app/core/client_gemini.py
"""
client_gemini.py — Client Google Gemini (via google-genai SDK)
"""

import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Configuration par défaut
DEFAULT_TIMEOUT = 600

class GeminiClientManager:
    """Gestionnaire du client Gemini avec gestion d'erreurs"""

    def __init__(self):
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initialise le client Gemini au démarrage"""
        try:
            from google import genai
            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                # Note: google-genai handles timeout differently,
                # but we aim for consistency in the manager structure.
            )
            logger.info(f"✓ Client Gemini initialisé avec le modèle: {settings.GEMINI_MODEL}")
        except ImportError:
            logger.error("✗ Bibliothèque 'google-genai' non installée.")
            raise
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation de Gemini: {e}")
            raise

    def get_client(self):
        """Retourne le client Gemini"""
        if self._client is None:
            self._initialize()
        return self._client

    def get_model_name(self) -> str:
        """Retourne le nom du modèle Gemini configuré"""
        return settings.GEMINI_MODEL

    def verify_connection(self) -> bool:
        """Vérifie la connexion à Gemini API"""
        try:
            # Simple check: try to list models or do a minimal call
            # For Gemini, we can try to generate a very short response or list models
            self._client.models.list()
            logger.info("✓ Connexion Gemini vérifiée")
            return True
        except Exception as e:
            logger.error(f"✗ Erreur lors de la vérification de la connexion Gemini: {e}")
            return False

# Instance globale (singleton)
_gemini_manager: Optional[GeminiClientManager] = None

def get_gemini_client():
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.get_client()

def get_gemini_model() -> str:
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.get_model_name()

def verify_gemini_connection() -> bool:
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.verify_connection()
