# app/core/test_llm.py
"""
test_llm.py — Script de diagnostic robuste et universel pour les providers LLM.
"""

import sys
from pydantic import BaseModel, Field
from app.core.llm_client import (
    get_llm_client,
    get_llm_model,
    get_active_provider_name,
    verify_llm_connection
)
from app.core.llm_utils import parse_and_validate_json

# Schéma de test
class DiagnosticResponse(BaseModel):
    connection_status: str = Field(..., description="Doit être 'SUCCESS' ou 'FAILURE'")
    model_name_confirmed: str = Field(..., description="Le nom exact du modèle qui a répondu")
    greeting_message: str = Field(..., description="Un message de bienvenue amical")

def run_diagnostics():
    provider = get_active_provider_name()
    model = get_llm_model()
    client = get_llm_client()

    print("=" * 60)
    print(f"   DIAGNOSTIC DU CLIENT LLM ({provider}) - SÉCURISÉ")
    print("=" * 60)
    print(f"[⚙️] Modèle configuré : {model}")
    print(f"[🔌] Connexion en cours...\n")

    # --- TEST 0 : Vérification de connexion rapide ---
    if not verify_llm_connection():
        print(f"[❌] ÉCHEC CRITIQUE : Le provider {provider} n'est pas accessible.")
        sys.exit(1)
    print(f"[OK] Connexion réseau établie avec {provider}.")

    # --- TEST 1 : Complétion standard ---
    print("\n--- TEST 1 : Complétion de texte standard ---")
    try:
        if provider == "GEMINI":
            # Utilisation du SDK natif google-genai
            response = client.models.generate_content(
                model=model,
                contents="Dis-moi bonjour et confirme que tu fonctionnes correctement."
            )
            answer = response.text.strip()
        else:
            # Utilisation de l'interface OpenAI (Ollama / NVIDIA)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Tu es un assistant de test. Réponds de manière très concise."},
                    {"role": "user", "content": "Dis-moi bonjour et confirme que tu fonctionnes correctement."}
                ],
                max_tokens=50,
                temperature=0.3
            )
            answer = response.choices[0].message.content.strip()

        print(f"[OK] Réponse reçue avec succès !")
        print(f"🤖 Réponse du modèle : \"{answer}\"")
    except Exception as e:
        print(f"[❌] ÉCHEC DU TEST 1 : Impossible de communiquer avec {provider}.")
        print(f"    Erreur : {e}")
        sys.exit(1)

    print("-" * 60)

    # --- TEST 2 : JSON Mode avec Extracteur Robuste ---
    print("--- TEST 2 : Validation du Mode JSON (Pydantic + Regex) ---")
    print("[⌛] Envoi d'une requête structurée...")

    schema_instruction = (
        "Tu es un système automatisé de diagnostic technique.\n"
        "Tu dois obligatoirement répondre sous la forme d'un objet JSON unique respectant cette structure :\n"
        "{\n"
        '  "connection_status": "SUCCESS",\n'
        '  "model_name_confirmed": "nom-du-modèle",\n'
        '  "greeting_message": "ton message de bienvenue"\n'
        "}\n\n"
        "CONSIGNE STRICTE : Ne génère aucun texte d'introduction ou de conclusion en dehors du JSON. "
        "Pas de balise markdown, pas de phrases explicatives."
    )

    try:
        if provider == "GEMINI":
            # Gemini gère le format JSON via le paramètre response_mime_type
            response = client.models.generate_content(
                model=model,
                contents=f"{schema_instruction}\n\nGénère un diagnostic de succès pour le modèle '{model}'.",
                config={"response_mime_type": "application/json"}
            )
            raw_output = response.text
        else:
            # Interface OpenAI
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": schema_instruction},
                    {"role": "user", "content": f"Génère un diagnostic de succès pour le modèle '{model}'."}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            raw_output = response.choices[0].message.content

        print(f"[📝] Réponse brute reçue de l'IA :\n{raw_output}\n")

        # Validation robuste avec notre nouvel utilitaire
        parsed_data = parse_and_validate_json(raw_output, DiagnosticResponse)

        print(f"[OK] Extraction et validation JSON réussies avec succès !")
        print(f"📊 Données structurées obtenues :")
        print(f"    - Statut de connexion : {parsed_data.connection_status}")
        print(f"    - Modèle confirmé     : {parsed_data.model_name_confirmed}")
        print(f"    - Message de l'IA     : {parsed_data.greeting_message}")

        print("\n" + "=" * 60)
        print(f"🎉 [SUCCÈS GLOBAL] Votre configuration LLM ({provider}) est 100% opérationnelle !")
        print("   L'inférence et la validation de schéma Pydantic fonctionnent parfaitement.")
        print("=" * 60)

    except Exception as e:
        print(f"[❌] ÉCHEC DU TEST 2 : Le modèle n'a pas pu être parsé.")
        print(f"    Détail de l'erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_diagnostics()