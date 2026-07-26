# app/core/test_llm.py
"""
test_llm.py — Script de diagnostic robuste avec extraction Regex de JSON pour Ollama.
"""

import sys
from pydantic import BaseModel, Field
from app.core.llm_client import ollama_openai_client, get_ollama_model
from app.core.llm_utils import parse_and_validate_json

# Schéma de test
class DiagnosticResponse(BaseModel):
    connection_status: str = Field(..., description="Doit être 'SUCCESS' ou 'FAILURE'")
    model_name_confirmed: str = Field(..., description="Le nom exact du modèle qui a répondu")
    greeting_message: str = Field(..., description="Un message de bienvenue amical")

def run_diagnostics():
    model = get_ollama_model()
    print("=" * 60)
    print("   DIAGNOSTIC DU CLIENT LLM (OLLAMA) - SÉCURISÉ")
    print("=" * 60)
    print(f"[⚙️] Modèle configuré : {model}")
    print(f"[🔌] Connexion en cours...\n")

    # --- TEST 1 : Complétion standard ---
    print("--- TEST 1 : Complétion de texte standard ---")
    try:
        response = ollama_openai_client.chat.completions.create(
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
        print(f"[❌] ÉCHEC DU TEST 1 : Impossible de communiquer avec Ollama.")
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
        response = ollama_openai_client.chat.completions.create(
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
        print("🎉 [SUCCÈS GLOBAL] Votre configuration LLM est 100% opérationnelle !")
        print("   Ollama et la validation de schéma Pydantic fonctionnent parfaitement.")
        print("=" * 60)

    except Exception as e:
        print(f"[❌] ÉCHEC DU TEST 2 : Le modèle n'a pas pu être parsé.")
        print(f"    Détail de l'erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_diagnostics()