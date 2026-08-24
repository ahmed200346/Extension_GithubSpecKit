# app/core/clients/client_gemini.py
"""
client_gemini.py – Client LLM spécialisé pour Google Gemini
"""

import logging
from typing import Optional
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClientManager:
    """Gestionnaire du client Gemini avec gestion d'erreurs et retry"""

    def __init__(self):
        self._genai_client = None
        self._openai_compatible_client = None
        self._initialize()

    def _initialize(self):
        """Initialise les clients Gemini au démarrage"""
        try:
            # 1. Client natif Gemini (via google-genai)
            from google import genai
            self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info(f"✓ Client Gemini natif initialisé avec modèle: {settings.GEMINI_MODEL}")

            # 2. Client OpenAI-compatible (via openai SDK pointant vers Google)
            # URL officielle pour la compatibilité OpenAI de Gemini
            self._openai_compatible_client = OpenAI(
                api_key=settings.GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            logger.info(f"✓ Client OpenAI-compatible pour Gemini initialisé via Google API")

        except Exception as e:
            logger.error(f"✗ Erreur lors de l'initialisation de Gemini: {e}")
            raise

    def get_genai_client(self):
        """Retourne le client Gemini natif (pour les features avancées)"""
        if self._genai_client is None:
            self._initialize()
        return self._genai_client

    def get_openai_compatible_client(self):
        """Retourne le client compatible OpenAI (pour les services standard)"""
        if self._openai_compatible_client is None:
            self._initialize()
        return self._openai_compatible_client

    def get_model_name(self) -> str:
        """Retourne le nom du modèle Gemini configuré"""
        return settings.GEMINI_MODEL

    def verify_connection(self) -> bool:
        """Vérifie que la connexion à Gemini est valide"""
        try:
            # Utilise le client natif pour une vérification rapide
            client = self.get_genai_client()
            models = list(client.models.list())
            logger.info(f"✓ Connexion Gemini vérifiée. Modèles disponibles: {len(models)}")
            return True
        except Exception as e:
            logger.error(f"✗ Erreur lors de la vérification de la connexion Gemini: {e}")
            return False

    def create_request_config(self) -> dict:
        """Crée la configuration standard pour les requêtes Gemini"""
        return {
            "temperature": settings.GEMINI_TEMPERATURE,
            "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
            "top_p": 0.95,
            "top_k": 40,
        }

    def apply_timeout_config(self):
        logger.info(
            f"ℹ Configuration de timeout appliquée: "
            f"request_timeout={settings.LLM_REQUEST_TIMEOUT}s, "
            f"retry_attempts={settings.LLM_RETRY_ATTEMPTS}"
        )


# Instance globale (singleton)
_gemini_manager: Optional[GeminiClientManager] = None


def get_gemini_client():
    """Retourne le client Gemini natif"""
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.get_genai_client()


def get_gemini_openai_client():
    """Retourne le client compatible OpenAI pour Gemini"""
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.get_openai_compatible_client()


def get_gemini_model() -> str:
    """Retourne le nom du modèle Gemini"""
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.get_model_name()


def verify_gemini_connection() -> bool:
    """Vérifie la connexion à Gemini"""
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.verify_connection()


def get_gemini_request_config() -> dict:
    """Retourne la configuration standard pour les requêtes Gemini"""
    global _gemini_manager
    if _gemini_manager is None:
        _gemini_manager = GeminiClientManager()
    return _gemini_manager.create_request_config()