# ✅ Instructions finales : Créer le workflow n8n Module A

## 🎯 Méthode la plus simple : Création manuelle (5 minutes)

L'automatisation via navigateur n'a pas fonctionné. La création manuelle est plus fiable.

### 📋 Étapes rapides

1. **Connectez-vous à n8n** :
   - Ouvrez : `https://n8n.w3lg.fr`
   - Identifiant : `admin`
   - Mot de passe : (celui configuré dans votre `.env`)

2. **Créez un nouveau workflow** :
   - Menu → **Workflows**
   - Cliquez sur **"+"** ou **"New Workflow"**

3. **Ajoutez le Schedule Trigger** :
   - Cherchez **"Schedule Trigger"**
   - Configurez-le :
     - Mode : **Cron**
     - Expression : `0 3 * * *` (tous les jours à 03:00)

4. **Ajoutez le HTTP Request** :
   - Cherchez **"HTTP Request"**
   - Configurez-le :
     - Method : **POST**
     - URL : `http://app:8000/api/v1/jobs/discover/run`

5. **Connectez les nodes** (glisser-déposer)

6. **Nommez** : "WM Module A - Discover Products"

7. **Activez** le workflow (toggle en haut à droite)

### ✅ Résultat

Le workflow s'exécutera automatiquement tous les jours à 03:00 et appellera l'endpoint de découverte.

---

## 🔄 Alternative : Si vous préférez que je le fasse

Si vous voulez absolument que je crée le workflow automatiquement, j'aurais besoin :
- Les identifiants exacts de connexion à n8n
- Ou confirmer si les identifiants sont bien `admin` / `J6gzzs42bDYkjKZiIXMl`

---

*Instructions créées le : 02/12/2025*

