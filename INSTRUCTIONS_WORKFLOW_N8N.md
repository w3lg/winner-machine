# ✅ Instructions pour créer le workflow n8n Module A

## 🚀 Méthode recommandée : Création manuelle dans n8n

**Durée estimée : 5 minutes**

### 📋 Étapes détaillées

1. **Ouvrez n8n** : `https://n8n.w3lg.fr`

2. **Connectez-vous** avec vos identifiants

3. **Créez un nouveau workflow** :
   - Menu → **Workflows**
   - Cliquez sur **"+"** ou **"New Workflow"**

4. **Ajoutez le Schedule Trigger** :
   - Cherchez **"Schedule Trigger"** dans la barre de recherche
   - Cliquez dessus pour l'ajouter au canvas
   - **Configurez-le** :
     - Mode : **Cron**
     - Expression : `0 3 * * *` (tous les jours à 03:00)
   - Cliquez sur **Save**

5. **Ajoutez le HTTP Request** :
   - Cherchez **"HTTP Request"**
   - Cliquez dessus pour l'ajouter
   - **Configurez-le** :
     - Method : **POST**
     - URL : `http://app:8000/api/v1/jobs/discover/run`
     - Authentication : **None**
   - Cliquez sur **Save**

6. **Connectez les nodes** :
   - Cliquez sur la sortie du Schedule Trigger
   - Glissez vers l'entrée du HTTP Request

7. **Sauvegardez** :
   - Nom : **"WM Module A - Discover Products"**
   - Cliquez sur l'icône **Save** (disquette)

8. **Activez** :
   - Cliquez sur le toggle **"Active"** en haut à droite
   - Le workflow est maintenant actif ! 🎉

### 🧪 Test immédiat

Pour tester sans attendre 03:00 :
- Cliquez sur le bouton **"Execute Workflow"** (icône play)
- Vérifiez les résultats dans **"Executions"**

---

## 🔄 Alternative : Utiliser le token d'API

Si vous avez un **token d'API n8n**, je peux créer le workflow automatiquement.

**Pour cela, j'ai besoin** :
- Le token d'API n8n (ou confirmer que les identifiants sont `admin` / `J6gzzs42bDYkjKZiIXMl`)

Une fois que vous me donnez le token, je peux exécuter le script `create_n8n_workflow.py` qui créera le workflow automatiquement.

---

*Instructions créées le : 02/12/2025*

