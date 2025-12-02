# 🔧 Solution : Erreur d'import du workflow n8n

## ❌ Problème identifié

L'erreur "The file does not contain valid JSON data" peut venir de :
1. Format JSON incompatible avec votre version de n8n
2. Métadonnées manquantes dans le workflow
3. Structure des nodes incompatible

## ✅ Solution recommandée : Créer le workflow dans n8n

**La meilleure approche** est de créer le workflow directement dans l'interface n8n plutôt que d'importer un JSON :

### 📝 Étapes simples (2 minutes)

1. **Ouvrez n8n** : `https://n8n.w3lg.fr`

2. **Créez un nouveau workflow** :
   - Menu : **Workflows** → **New Workflow**

3. **Ajoutez le Schedule Trigger** :
   - Cherchez **"Schedule Trigger"** dans la barre de recherche
   - Glissez-le sur le canvas
   - Cliquez dessus pour configurer :
     - **Trigger Interval** : Daily
     - **Hour** : 3
     - **Minute** : 0
     - Ou utilisez **Cron Expression** : `0 3 * * *`

4. **Ajoutez le HTTP Request** :
   - Cherchez **"HTTP Request"**
   - Glissez-le après le trigger
   - Configurez :
     - **Method** : POST
     - **URL** : `http://app:8000/api/v1/jobs/discover/run`
     - **Authentication** : None

5. **Connectez les nodes** :
   - Cliquez sur la sortie du Schedule Trigger
   - Glissez vers l'entrée du HTTP Request

6. **Sauvegardez** :
   - Nom : **"WM Module A - Discover Products"**
   - Cliquez sur **Save** (en haut à droite)

7. **Activez** :
   - Cliquez sur le toggle **Active** (en haut à droite)

### 🎯 Workflow créé !

Le workflow :
- ✅ Se déclenche tous les jours à 03:00
- ✅ Appelle l'endpoint de découverte
- ✅ Est actif et prêt à fonctionner

## 📋 Alternative : Exporter depuis n8n

Si vous créez le workflow dans n8n, vous pouvez ensuite l'exporter :

1. Ouvrez le workflow créé
2. Cliquez sur **"..."** (menu) → **"Download"**
3. Le fichier JSON exporté sera au bon format
4. Remplacez `n8n/workflows/wm_module_a_discover_cron.json` par ce fichier

Cela garantira que le format est compatible avec votre version de n8n !

---

*Document créé le : 02/12/2025*

