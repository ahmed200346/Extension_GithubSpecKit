# app/core/llm_client.py
"""
llm_client.py — Gestionnaire centralisé des connexions LLM (multi-fournisseurs)

Ce module initialise et distribue les clients LLM selon la configuration fournie
dans les settings. Supporte Ollama, Gemini, NVIDIA et tout autre fournisseur
compatibles OpenAI.

Il expose :
- Un client compatible OpenAI (pour les requêtes JSON structurées avec Pydantic).
- Des méthodes d'accès aux clients selon le fournisseur actif.
"""

from openai import OpenAI
from app.config import settings

# Déterminer le fournisseur actif depuis la configuration
LLM_PROVIDER = settings.LLM_PROVIDER or "ollama"


def _get_openai_client() -> OpenAI:
    """Crée un client OpenAI configuré selon le fournisseur actif."""
    if LLM_PROVIDER == "ollama":
        return OpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )
    elif LLM_PROVIDER == "gemini":
        # Google GenAI utilise le SDK google-genai
        from google import genai
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    elif LLM_PROVIDER == "nvidia":
        return OpenAI(
            base_url=f"{settings.NVIDIA_BASE_URL}/v1",
            api_key=settings.NVIDIA_API_KEY,
        )
    else:
        # Par défaut : Ollama
        return OpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )

# Client OpenAI compatible actif (injecté au démarrage)
# Les services doivent utiliser get_client_active() plutôt que la variable globale
# ollama_openai_client, mais pour garder la compatibilité, on expose tout de même
# la variable globale initialisée ci-dessous.
ollama_openai_client = _get_openai_client()


# Clients natifs par fournisseur
if LLM_PROVIDER == "ollama":
    import ollama
    ollama_native_client = ollama.Client(host=settings.OLLAMA_BASE_URL)
elif LLM_PROVIDER == "gemini":
    from google import genai
    ollama_native_client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    ollama_native_client = None


def get_llm_model() -> str:
    """Retourne le nom du modèle par défaut configuré selon le fournisseur actif."""
    if LLM_PROVIDER == "ollama":
        return settings.OLLAMA_MODEL
    elif LLM_PROVIDER == "gemini":
        return settings.GEMINI_MODEL
    elif LLM_PROVIDER == "nvidia":
        return settings.NVIDIA_MODEL
    return settings.OLLAMA_MODEL


get_ollama_model = get_llm_model

def get_client_active() -> OpenAI:
    """Retourne le client OpenAI actif selon la configuration actuelle."""
    return _get_openai_client()