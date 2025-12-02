#!/usr/bin/env python3
"""
Script pour activer le workflow n8n Module A
"""
import requests
import json

# Configuration
N8N_URL = "https://n8n.w3lg.fr"
N8N_EMAIL = "w3lgcom@gmail.com"
N8N_PASSWORD = "no26CG73Lg@"
WORKFLOW_ID = "IgEn1CU6IUTbK09M"

def activate_workflow():
    """Active le workflow n8n"""
    session = requests.Session()
    session.verify = False
    
    # Se connecter
    print("🔐 Connexion à n8n...")
    login_url = f"{N8N_URL}/rest/login"
    login_data = {
        "emailOrLdapLoginId": N8N_EMAIL,
        "password": N8N_PASSWORD
    }
    
    response = session.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"❌ Erreur de connexion: {response.status_code}")
        return False
    
    print("✅ Connecté à n8n")
    
    # Récupérer le workflow pour obtenir le versionId
    print(f"📖 Récupération du workflow {WORKFLOW_ID}...")
    get_url = f"{N8N_URL}/rest/workflows/{WORKFLOW_ID}"
    response = session.get(get_url)
    
    if response.status_code != 200:
        print(f"❌ Erreur lors de la récupération: {response.status_code}")
        print(response.text)
        return False
    
    workflow = response.json()
    if "data" in workflow:
        workflow = workflow["data"]
    
    version_id = workflow.get("versionId")
    print(f"✅ Workflow récupéré, versionId: {version_id}")
    
    # Activer le workflow avec le versionId
    print("🔄 Activation du workflow...")
    activate_url = f"{N8N_URL}/rest/workflows/{WORKFLOW_ID}/activate"
    activate_data = {
        "versionId": version_id
    }
    
    response = session.post(activate_url, json=activate_data)
    
    if response.status_code in [200, 201, 204]:
        print("✅ Workflow activé avec succès!")
        return True
    else:
        print(f"❌ Erreur lors de l'activation: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Activation du workflow n8n Module A")
    print("=" * 60)
    print()
    
    success = activate_workflow()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Le workflow est maintenant actif!")
        print("   Il s'exécutera tous les jours à 03:00")
    else:
        print("❌ L'activation a échoué")
    print("=" * 60)

