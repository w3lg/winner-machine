# 🔧 Créer le workflow n8n Module A

## Problème

L'import du fichier JSON dans n8n ne fonctionne pas car n8n nécessite un format spécifique avec des métadonnées propres à l'instance.

## ✅ Solution : Créer le workflow via l'API n8n

J'ai préparé un script Python qui va créer le workflow automatiquement. **Cependant, j'ai besoin du token d'API n8n** que vous mentionnez.

### Option 1 : Utiliser le script Python (recommandé)

1. **Donnez-moi le token d'API n8n** (ou confirmez que les identifiants sont admin / J6gzzs42bDYkjKZiIXMl)

2. J'exécuterai le script qui :
   - Se connecte à n8n
   - Crée le workflow automatiquement
   - L'active

### Option 2 : Créer manuellement dans n8n (plus simple)

Si vous préférez créer le workflow vous-même, voici les étapes rapides :

1. **Accédez à n8n** : `https://n8n.w3lg.fr`

2. **Créez un nouveau workflow** :
   - Menu : **Workflows** → **New Workflow**

3. **Ajoutez le Schedule Trigger** :
   - Cherchez **"Schedule Trigger"** dans la barre de recherche
   - Cliquez dessus pour configurer :
     - Mode : **Cron**
     - Expression : `0 3 * * *` (tous les jours à 03:00)

4. **Ajoutez le HTTP Request** :
   - Cherchez **"HTTP Request"**
   - Cliquez dessus pour configurer :
     - Method : **POST**
     - URL : `http://app:8000/api/v1/jobs/discover/run`

5. **Connectez les nodes** (glisser-déposer)

6. **Sauvegardez** : Nommez-le "WM Module A - Discover Products"

7. **Activez** le workflow (toggle en haut à droite)

---

## 📝 Token d'API n8n

**Pouvez-vous me confirmer :**
- Le token d'API n8n (si différent des identifiants de base)
- Ou si je dois utiliser les identifiants : admin / J6gzzs42bDYkjKZiIXMl

Une fois que j'ai cette information, je peux créer le workflow automatiquement ! 🚀

