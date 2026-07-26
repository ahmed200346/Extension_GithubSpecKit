# app/core/llm_client.py
"""
llm_client.py — Gestionnaire centralisé des connexions LLM (Ollama)

Ce module initialise et distribue les clients Ollama pour l'ensemble des agents.
Il expose :
- Un client compatible OpenAI (pour les requêtes JSON structurées avec Pydantic).
- Un client natif Ollama (pour les requêtes de base, le streaming, ou la gestion des modèles).
"""

from openai import OpenAI
import ollama
from app.config import settings

# 1. Initialisation du client compatible OpenAI (Indispensable pour l'utilisation de .beta.chat.completions.parse)
# Note : Pour Ollama, l'API compatible OpenAI est hébergée sur l'URL de base suivie de '/v1'
ollama_openai_client = OpenAI(
    base_url=f"{settings.OLLAMA_BASE_URL}/v1",
    api_key="ollama"  # Clé factice requise pour valider l'initialisation du SDK OpenAI
)

# 2. Initialisation du client natif Ollama (Optionnel mais utile pour d'autres fonctionnalités)
ollama_native_client = ollama.Client(host=settings.OLLAMA_BASE_URL)


def get_ollama_model() -> str:
    """Retourne le nom du modèle par défaut configuré dans le .env"""
    return settings.OLLAMA_MODEL