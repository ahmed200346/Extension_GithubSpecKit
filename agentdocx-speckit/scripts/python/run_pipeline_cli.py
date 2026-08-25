import sys
import time
import argparse
import requests
from pathlib import Path

API_BASE_URL = "http://127.0.0.1:8000/api/v1/pipeline"

def wait_for_completion(file_path: str):
    file_name = Path(file_path).name
    print(f"\n🚀 [CLI] Lancement synchrone du pipeline pour : {file_name}")

    # 1. Attente si le serveur est déjà occupé
    while True:
        try:
            status_res = requests.get(f"{API_BASE_URL}/status", timeout=3)
            if status_res.status_code == 200:
                status_data = status_res.json()
                if not status_data.get("is_running"):
                    break
                print(f"⏳ [CLI] Serveur occupé sur '{status_data.get('current_file')}'. Attente...", end="\r")
        except Exception:
            print("❌ [CLI] Impossible de contacter FastAPI. Le serveur est-il démarré ?")
            sys.exit(1)
        time.sleep(2)

    # 2. Envoi de la requête d'exécution
    print(f"⚙️  [CLI] Traitement par les agents LangGraph en cours (veuillez patienter)...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/upload",
            json={"file_path": str(Path(file_path).resolve())},
            timeout=None  # Timeout de 5 minutes max pour les agents
        )
        
        elapsed = round(time.time() - start_time, 2)

        if response.status_code == 200:
            result = response.json()
            pdf_path = result.get("pdf_path", "N/A")
            print(f"\n✅ [CLI] Pipeline terminé avec succès en {elapsed}s !")
            print(f"📄 Document PDF généré : {pdf_path}\n")
        else:
            print(f"\n❌ [CLI] Erreur API ({response.status_code}) : {response.text}")
            sys.exit(1)

    except requests.exceptions.Timeout:
        print("\n⏳ [CLI] Le pipeline a dépassé le délai maximum de 5 minutes.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ [CLI] Erreur lors de l'exécution : {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exécute le pipeline SpecKit de façon synchrone.")
    parser.add_argument("--file", required=True, help="Chemin du fichier Markdown à traiter")
    args = parser.parse_args()

    wait_for_completion(args.file)