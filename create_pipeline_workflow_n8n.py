#!/usr/bin/env python3
"""
Script pour créer le workflow n8n pipeline A→B→C
"""
import json
import requests
import sys

# Configuration
N8N_URL = "https://n8n.w3lg.fr"
N8N_EMAIL = "w3lgcom@gmail.com"
N8N_PASSWORD = "no26CG73Lg@"
OLD_WORKFLOW_ID = "IgEn1CU6IUTbK09M"  # ID du workflow Module A seul

def create_pipeline_workflow():
    """Crée le workflow n8n pipeline A→B→C"""
    session = requests.Session()
    session.verify = False
    
    # 1. Se connecter
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
    
    # 2. Lire le workflow JSON
    print("📖 Lecture du fichier workflow pipeline...")
    try:
        with open("n8n/workflows/wm_pipeline_daily_abc.json", "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return False
    
    print("✅ Fichier workflow lu")
    
    # 3. Préparer le workflow pour n8n
    workflow_payload = {
        "name": workflow_data.get("name", "WM Pipeline Daily - Discover → Source → Score"),
        "nodes": workflow_data.get("nodes", []),
        "connections": workflow_data.get("connections", {}),
        "settings": workflow_data.get("settings", {}),
        "staticData": workflow_data.get("staticData") or {},
        "pinData": workflow_data.get("pinData", {}),
        "tags": workflow_data.get("tags", []),
        "active": False
    }
    
    # 4. Créer le workflow
    print("🚀 Création du workflow pipeline...")
    create_url = f"{N8N_URL}/rest/workflows"
    response = session.post(create_url, json=workflow_payload, headers={"Content-Type": "application/json"})
    
    if response.status_code in [200, 201]:
        workflow_info = response.json()
        if "data" in workflow_info:
            workflow = workflow_info["data"]
        else:
            workflow = workflow_info
        
        workflow_id = workflow.get("id")
        workflow_name = workflow.get("name")
        version_id = workflow.get("versionId")
        
        print(f"✅ Workflow créé: {workflow_name}")
        print(f"   ID: {workflow_id}")
        
        # 5. Activer le workflow
        if workflow_id and version_id:
            print("🔄 Activation du workflow...")
            activate_url = f"{N8N_URL}/rest/workflows/{workflow_id}/activate"
            activate_data = {"versionId": version_id}
            activate_response = session.post(activate_url, json=activate_data)
            
            if activate_response.status_code in [200, 201, 204]:
                print("✅ Workflow activé avec succès!")
            else:
                print(f"⚠️  Activation échouée: {activate_response.status_code}")
                print(f"   Réponse: {activate_response.text}")
        
        # 6. Désactiver l'ancien workflow Module A
        print("\n🔧 Désactivation de l'ancien workflow Module A...")
        old_workflow_url = f"{N8N_URL}/rest/workflows/{OLD_WORKFLOW_ID}"
        
        # Récupérer l'ancien workflow pour obtenir versionId
        get_response = session.get(old_workflow_url)
        if get_response.status_code == 200:
            old_workflow = get_response.json()
            if "data" in old_workflow:
                old_workflow = old_workflow["data"]
            
            old_version_id = old_workflow.get("versionId")
            
            if old_version_id:
                deactivate_url = f"{N8N_URL}/rest/workflows/{OLD_WORKFLOW_ID}/deactivate"
                deactivate_data = {"versionId": old_version_id}
                deactivate_response = session.post(deactivate_url, json=deactivate_data)
                
                if deactivate_response.status_code in [200, 201, 204]:
                    print(f"✅ Ancien workflow '{old_workflow.get('name')}' désactivé")
                else:
                    print(f"⚠️  Désactivation échouée: {deactivate_response.status_code}")
            else:
                print("⚠️  Impossible de récupérer versionId de l'ancien workflow")
        else:
            print(f"⚠️  Impossible de récupérer l'ancien workflow: {get_response.status_code}")
        
        return workflow_id, workflow_name
    else:
        print(f"❌ Erreur lors de la création: {response.status_code}")
        print(f"   Réponse: {response.text[:500]}")
        return None, None

if __name__ == "__main__":
    print("=" * 60)
    print("Création du workflow n8n Pipeline A→B→C")
    print("=" * 60)
    print()
    
    workflow_id, workflow_name = create_pipeline_workflow()
    
    print()
    print("=" * 60)
    if workflow_id:
        print("✅ Le workflow pipeline a été créé avec succès!")
        print(f"   Nom: {workflow_name}")
        print(f"   ID: {workflow_id}")
        print(f"   Statut: ACTIF")
        print(f"   Planification: Tous les jours à 03:15 (cron: 15 3 * * *)")
    else:
        print("❌ La création du workflow a échoué")
    print("=" * 60)

