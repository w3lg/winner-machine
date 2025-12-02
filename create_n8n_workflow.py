#!/usr/bin/env python3
"""
Script pour créer le workflow n8n Module A via l'API n8n
"""
import json
import requests
import sys

# Configuration
N8N_URL = "https://n8n.w3lg.fr"
N8N_USER = "admin"
N8N_PASSWORD = "J6gzzs42bDYkjKZiIXMl"  # À remplacer par le vrai token si différent

def create_workflow():
    """Crée le workflow n8n Module A"""
    session = requests.Session()
    session.verify = False  # Désactiver la vérification SSL pour les certificats auto-signés
    
    # 1. Se connecter pour obtenir un cookie de session
    print("🔐 Connexion à n8n...")
    login_url = f"{N8N_URL}/rest/login"
    login_data = {
        "emailOrLdapLoginId": N8N_USER,
        "password": N8N_PASSWORD
    }
    
    response = session.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"❌ Erreur de connexion: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Connecté à n8n")
    
    # 2. Lire le workflow JSON
    print("📖 Lecture du fichier workflow...")
    try:
        with open("n8n/workflows/wm_module_a_discover_cron.json", "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return False
    
    print("✅ Fichier workflow lu")
    
    # 3. Créer le workflow via l'API
    print("🚀 Création du workflow...")
    create_url = f"{N8N_URL}/rest/workflows"
    response = session.post(create_url, json=workflow_data)
    
    if response.status_code in [200, 201]:
        print("✅ Workflow créé avec succès!")
        workflow_info = response.json()
        print(f"   ID: {workflow_info.get('id')}")
        print(f"   Nom: {workflow_info.get('name')}")
        return True
    else:
        print(f"❌ Erreur lors de la création: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    create_workflow()

