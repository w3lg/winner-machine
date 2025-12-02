#!/usr/bin/env python3
"""
Script pour créer le workflow n8n Module A via l'API n8n
Utilise l'authentification par email/password ou token JWT
"""
import json
import requests
import sys

# Configuration
N8N_URL = "https://n8n.w3lg.fr"
N8N_EMAIL = "w3lgcom@gmail.com"
N8N_PASSWORD = "no26CG73Lg@"
N8N_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNzcxMDQyNS0wMTEzLTQwN2MtOTE1NS04N2VkZjhlZDc0NDYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzY0NjcwNjIxfQ.1VsehKysdbG8KQQ-WcvP-Q8dddJ6iU2dYtI6YQLYRkA"

def create_workflow():
    """Crée le workflow n8n Module A"""
    session = requests.Session()
    session.verify = False  # Désactiver la vérification SSL
    
    # 1. Se connecter pour obtenir un cookie de session
    print("🔐 Connexion à n8n...")
    login_url = f"{N8N_URL}/rest/login"
    login_data = {
        "emailOrLdapLoginId": N8N_EMAIL,
        "password": N8N_PASSWORD
    }
    
    try:
        response = session.post(login_url, json=login_data)
        if response.status_code == 200:
            print("✅ Connecté à n8n avec email/password")
        else:
            print(f"⚠️  Connexion email/password échouée ({response.status_code}), utilisation du token...")
    except Exception as e:
        print(f"⚠️  Erreur de connexion: {e}, utilisation du token...")
    
    # 2. Lire le workflow JSON
    print("📖 Lecture du fichier workflow...")
    try:
        with open("n8n/workflows/wm_module_a_discover_cron.json", "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return False
    
    print("✅ Fichier workflow lu")
    
    # 3. Préparer le workflow pour n8n (format simplifié pour l'API)
    workflow_payload = {
        "name": workflow_data.get("name", "WM Module A - Discover Products (Cron)"),
        "nodes": workflow_data.get("nodes", []),
        "connections": workflow_data.get("connections", {}),
        "settings": workflow_data.get("settings", {}),
        "staticData": workflow_data.get("staticData"),
        "pinData": workflow_data.get("pinData", {}),
        "tags": workflow_data.get("tags", []),
        "active": False
    }
    
    # Nettoyer les champs null ou vides qui pourraient poser problème
    if workflow_payload["staticData"] is None:
        workflow_payload["staticData"] = {}
    if workflow_payload["pinData"] is None:
        workflow_payload["pinData"] = {}
    
    # 4. Créer le workflow via l'API REST
    print("🚀 Création du workflow via l'API n8n...")
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_TOKEN
    }
    
    create_url = f"{N8N_URL}/rest/workflows"
    
    try:
        # Utiliser la session (avec cookies) ou le token
        if session.cookies:
            response = session.post(create_url, json=workflow_payload, headers={"Content-Type": "application/json"})
        else:
            response = requests.post(create_url, json=workflow_payload, headers=headers, verify=False)
        
        if response.status_code in [200, 201]:
            print("✅ Workflow créé avec succès!")
            workflow_info = response.json()
            
            # L'API peut retourner le workflow dans data ou directement
            if "data" in workflow_info:
                workflow = workflow_info["data"]
            else:
                workflow = workflow_info
            
            workflow_id = workflow.get("id")
            workflow_name = workflow.get("name")
            
            print(f"   ID: {workflow_id}")
            print(f"   Nom: {workflow_name}")
            
            # 5. Activer le workflow
            if workflow_id:
                print("🔄 Activation du workflow...")
                activate_url = f"{N8N_URL}/rest/workflows/{workflow_id}/activate"
                
                if session.cookies:
                    activate_response = session.post(activate_url)
                else:
                    activate_response = requests.post(activate_url, headers=headers, verify=False)
                
                if activate_response.status_code in [200, 201, 204]:
                    print("✅ Workflow activé avec succès!")
                    return True
                else:
                    print(f"⚠️  Workflow créé mais activation échouée: {activate_response.status_code}")
                    print(f"   Réponse: {activate_response.text}")
                    print(f"   Vous pouvez l'activer manuellement dans n8n (ID: {workflow_id})")
                    return True
            else:
                print("⚠️  Workflow créé mais impossible de récupérer l'ID")
                return True
        else:
            print(f"❌ Erreur lors de la création: {response.status_code}")
            print(f"   Réponse: {response.text[:500]}")
            
            # Essayer avec un format encore plus simple
            print("\n🔄 Tentative avec un format de workflow minimal...")
            minimal_payload = {
                "name": "WM Module A - Discover Products",
                "nodes": workflow_data.get("nodes", []),
                "connections": workflow_data.get("connections", {}),
                "active": False
            }
            
            if session.cookies:
                response2 = session.post(create_url, json=minimal_payload, headers={"Content-Type": "application/json"})
            else:
                response2 = requests.post(create_url, json=minimal_payload, headers=headers, verify=False)
            
            if response2.status_code in [200, 201]:
                print("✅ Workflow créé avec format minimal!")
                workflow_info = response2.json()
                if "data" in workflow_info:
                    workflow = workflow_info["data"]
                else:
                    workflow = workflow_info
                workflow_id = workflow.get("id")
                print(f"   ID: {workflow_id}")
                
                if workflow_id:
                    activate_url = f"{N8N_URL}/rest/workflows/{workflow_id}/activate"
                    if session.cookies:
                        activate_response = session.post(activate_url)
                    else:
                        activate_response = requests.post(activate_url, headers=headers, verify=False)
                    if activate_response.status_code in [200, 201, 204]:
                        print("✅ Workflow activé!")
                    else:
                        print(f"⚠️  Activation échouée, activez manuellement (ID: {workflow_id})")
                return True
            else:
                print(f"❌ Échec également avec format minimal: {response2.status_code}")
                print(f"   Réponse: {response2.text[:500]}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Création du workflow n8n Module A - Discover Products")
    print("=" * 60)
    print()
    
    success = create_workflow()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Le workflow a été créé avec succès!")
        print("   Vous pouvez le vérifier dans n8n : https://n8n.w3lg.fr")
    else:
        print("❌ La création du workflow a échoué")
        print("   Veuillez vérifier les logs ci-dessus")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
