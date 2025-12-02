# 📥 Guide : Importer le workflow n8n Module A

## ✅ Le JSON a été corrigé

Le fichier `n8n/workflows/wm_module_a_discover_cron.json` a été corrigé et validé. Il est maintenant compatible avec n8n.

## 🚀 Méthode recommandée : Créer le workflow dans n8n

Au lieu d'importer un JSON (qui peut avoir des incompatibilités de version), je recommande de **créer le workflow directement dans n8n** :

### Étapes :

1. **Accédez à n8n** : `https://n8n.w3lg.fr`

2. **Créez un nouveau workflow** :
   - Cliquez sur **"Workflows"**
   - Cliquez sur **"New Workflow"** ou **"+"**

3. **Ajoutez le node Schedule Trigger** :
   - Dans la palette de nodes, cherchez **"Schedule Trigger"**
   - Glissez-le sur le canvas
   - Configurez-le :
     - Mode : **Cron**
     - Expression : `0 3 * * *` (tous les jours à 03:00)
     - Ou utilisez l'interface graphique pour choisir "Every Day at 3:00 AM"

4. **Ajoutez le node HTTP Request** :
   - Cherchez **"HTTP Request"** dans la palette
   - Glissez-le après le Schedule Trigger
   - Configurez-le :
     - Method : **POST**
     - URL : `http://app:8000/api/v1/jobs/discover/run`
     - Authentication : **None**

5. **Connectez les nodes** :
   - Cliquez sur le point de sortie du Schedule Trigger
   - Glissez vers le point d'entrée du HTTP Request

6. **Sauvegardez** :
   - Donnez un nom : **"WM Module A - Discover Products"**
   - Cliquez sur **"Save"**

7. **Activez le workflow** :
   - Cliquez sur le toggle **"Active"** en haut à droite

## 📋 Alternative : Import manuel du JSON simplifié

Si vous voulez quand même importer le JSON, voici un workflow minimal :

1. Dans n8n, cliquez sur **"Workflows"** → **"Import from File"**
2. Sélectionnez `n8n/workflows/wm_module_a_discover_cron.json`
3. Si ça ne fonctionne toujours pas :
   - **Créez le workflow manuellement** (méthode ci-dessus)
   - Une fois créé, **exportez-le** depuis n8n pour voir le format exact
   - Remplacez `n8n/workflows/wm_module_a_discover_cron.json` par l'export

## ⚠️ Note importante

Les workflows n8n exportés contiennent souvent des **métadonnées spécifiques à l'instance** (IDs, timestamps, etc.) qui peuvent causer des problèmes lors de l'import. C'est pourquoi il est recommandé de **créer le workflow directement dans l'interface n8n**.

---

*Document créé le : 02/12/2025*

