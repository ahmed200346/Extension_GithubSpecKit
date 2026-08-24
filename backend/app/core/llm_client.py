# app/core/llm_client.py
"""
llm_client.py – Orchestrateur central pour la gestion des providers LLM

Point d'entrée unique pour tous les clients LLM (Ollama, Gemini, NVIDIA).
- Charge le provider configuré dans .env (LLM_PROVIDER)
- Importe dynamiquement le client approprié
- Expose une interface uniforme pour toute l'application
"""

import logging
from typing import Optional, Any
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# LOGIQUE DE DISPATCH DU PROVIDER
# ============================================================================

_ACTIVE_PROVIDER = settings.LLM_PROVIDER.lower()

if _ACTIVE_PROVIDER == "ollama":
    from app.core.client_ollama import (
        get_ollama_client as _get_ollama_client,
        get_ollama_model as _get_ollama_model,
        verify_ollama_connection as _verify_ollama_connection,
    )
    logger.info(f"📌 Provider LLM sélectionné: OLLAMA")

elif _ACTIVE_PROVIDER == "gemini":
    from app.core.client_gemini import (
        get_gemini_client as _get_gemini_client,
        get_gemini_model as _get_gemini_model,
        verify_gemini_connection as _verify_gemini_connection,
    )
    logger.info(f"📌 Provider LLM sélectionné: GEMINI")

elif _ACTIVE_PROVIDER == "nvidia":
    from app.core.client_nvidia import (
        get_nvidia_client as _get_nvidia_client,
        get_nvidia_model as _get_nvidia_model,
        verify_nvidia_connection as _verify_nvidia_connection,
    )
    logger.info(f"📌 Provider LLM sélectionné: NVIDIA")

else:
    logger.error(f"✗ Provider LLM inconnu: {_ACTIVE_PROVIDER}")
    # On peut définir un fallback ou lever une erreur
    _ACTIVE_PROVIDER = "ollama" # Fallback par défaut

# ============================================================================
# INTERFACE UNIFORME
# ============================================================================

def get_llm_client() -> Any:
    """
    Retourne le client LLM actif selon la configuration.
    """
    if _ACTIVE_PROVIDER == "ollama":
        return _get_ollama_client()
    elif _ACTIVE_PROVIDER == "nvidia":
        return _get_nvidia_client()
    elif _ACTIVE_PROVIDER == "gemini":
        # Retourne le client compatible OpenAI pour Gemini pour maintenir l'interface uniforme
        from app.core.clients.client_gemini import get_gemini_openai_client
        return get_gemini_openai_client()
    else:
        raise ValueError(f"Provider LLM non supporté: {_ACTIVE_PROVIDER}")

def get_llm_model() -> str:
    """
    Retourne le nom du modèle LLM actif selon la configuration.
    """
    if _ACTIVE_PROVIDER == "ollama":
        return _get_ollama_model()
    elif _ACTIVE_PROVIDER == "nvidia":
        return _get_nvidia_model()
    elif _ACTIVE_PROVIDER == "gemini":
        return _get_gemini_model()
    else:
        raise ValueError(f"Provider LLM non supporté: {_ACTIVE_PROVIDER}")

def verify_llm_connection() -> bool:
    """
    Vérifie que la connexion au provider LLM est fonctionnelle.
    """
    if _ACTIVE_PROVIDER == "ollama":
        return _verify_ollama_connection()
    elif _ACTIVE_PROVIDER == "nvidia":
        return _verify_nvidia_connection()
    elif _ACTIVE_PROVIDER == "gemini":
        return _verify_gemini_connection()
    else:
        return False

def get_active_provider_name() -> str:
    """Retourne le nom du provider actif"""
    return _ACTIVE_PROVIDER.upper()

def get_provider_info() -> dict:
    """Retourne des informations détaillées sur le provider actif"""
    return {
        "provider": get_active_provider_name(),
        "model": get_llm_model(),
        "connection_ok": verify_llm_connection(),
    }

def initialize_llm_provider():
    """
    Initialise le provider LLM et vérifie la connexion.
    """
    logger.info("="*70)
    logger.info("Initialisation du Provider LLM")
    logger.info("="*70)

    try:
        info = get_provider_info()
        logger.info(f"📋 Configuration LLM: {info}")

        if verify_llm_connection():
            logger.info("✓ Provider LLM prêt et fonctionnel")
            return True
        else:
            logger.error("✗ Le provider LLM n'est pas accessible")
            return False
    except Exception as e:
        logger.error(f"✗ Erreur lors de l'initialisation du provider LLM: {e}")
        return False

# ============================================================================
# COMPATIBILITÉ LEGACY (Pour éviter les ImportError dans les services)
# ============================================================================
# Ces alias permettent aux services qui importaient directement
# 'ollama_openai_client' ou 'get_ollama_model' de continuer à fonctionner
# avec n'importe quel provider actif.

ollama_openai_client = get_llm_client()
get_ollama_model = get_llm_model
