#!/usr/bin/env python3
"""
Script pour tester le workflow pipeline A→B→C en l'exécutant manuellement
"""
import requests

# Configuration
N8N_URL = "https://n8n.w3lg.fr"
N8N_EMAIL = "w3lgcom@gmail.com"
N8N_PASSWORD = "no26CG73Lg@"
WORKFLOW_ID = "wlaYVQkkS52IZcIg"

def test_workflow():
    """Teste le workflow en l'exécutant manuellement"""
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
    
    # Récupérer le workflow pour obtenir versionId
    print(f"📖 Récupération du workflow {WORKFLOW_ID}...")
    get_url = f"{N8N_URL}/rest/workflows/{WORKFLOW_ID}"
    response = session.get(get_url)
    
    if response.status_code != 200:
        print(f"❌ Erreur lors de la récupération: {response.status_code}")
        return False
    
    workflow = response.json()
    if "data" in workflow:
        workflow = workflow["data"]
    
    version_id = workflow.get("versionId")
    workflow_name = workflow.get("name")
    
    print(f"✅ Workflow récupéré: {workflow_name}")
    print(f"   Version ID: {version_id}")
    
    # Exécuter le workflow manuellement
    print("\n🚀 Exécution manuelle du workflow...")
    execute_url = f"{N8N_URL}/rest/workflows/{WORKFLOW_ID}/execute"
    execute_data = {}
    
    response = session.post(execute_url, json=execute_data)
    
    if response.status_code in [200, 201]:
        print("✅ Workflow exécuté avec succès!")
        result = response.json()
        print(f"   Résultat: {result}")
        return True
    else:
        print(f"❌ Erreur lors de l'exécution: {response.status_code}")
        print(f"   Réponse: {response.text[:500]}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Test du workflow pipeline A→B→C")
    print("=" * 60)
    print()
    
    test_workflow()
    
    print()
    print("=" * 60)
    print("Vérifiez les exécutions dans n8n pour voir les détails")
    print("=" * 60)

