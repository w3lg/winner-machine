# Workflows n8n - Winner Machine

Documentation pour les workflows n8n de Winner Machine v1.

## 📋 Workflows disponibles

### Module A : Discover Products (Cron)

**Fichier** : `n8n/workflows/wm_module_a_discover_cron.json`

**Description** : Lance automatiquement le job de découverte de produits tous les jours à 03:00.

**Fonctionnalités** :
- Déclenchement quotidien via Cron (03:00)
- Appel HTTP vers l'endpoint de découverte
- Vérification du succès/échec
- Logging des résultats

## 🚀 Importation du workflow

### 1. Accéder à n8n

- **Local** : http://localhost:5678
- **Production** : https://n8n.w3lg.fr

### 2. Importer le workflow

1. Cliquer sur **"Workflows"** dans le menu
2. Cliquer sur **"Import from File"** ou le bouton **"+"** → **"Import from File"**
3. Sélectionner le fichier `n8n/workflows/wm_module_a_discover_cron.json`
4. Cliquer sur **"Import"**

### 3. Configurer l'URL du backend

Le workflow utilise par défaut `http://app:8000` (communication interne Docker).

**Pour utiliser l'URL externe** (si backend exposé via nginx) :

1. Ouvrir le workflow importé
2. Cliquer sur le nœud **"HTTP Request - Discover Job"**
3. Modifier l'URL :
   - **Option 1** : `https://marcus.w3lg.fr/api/v1/jobs/discover/run`
   - **Option 2** : Garder `http://app:8000/api/v1/jobs/discover/run` (si n8n dans le même docker-compose)
4. Sauvegarder

### 4. Ajuster le schedule Cron (optionnel)

Par défaut, le workflow s'exécute tous les jours à 03:00.

Pour modifier :

1. Cliquer sur le nœud **"Cron"**
2. Modifier l'expression cron :
   - `0 3 * * *` = Tous les jours à 03:00
   - `0 */6 * * *` = Toutes les 6 heures
   - `0 0 * * 0` = Tous les dimanches à minuit
3. Sauvegarder

### 5. Activer le workflow

1. Cliquer sur le toggle **"Active"** en haut à droite
2. Le workflow est maintenant actif et s'exécutera selon le schedule

## 🔧 Structure du workflow

### Nœuds

1. **Cron** : Déclenchement automatique quotidien
2. **HTTP Request** : Appel vers l'endpoint de découverte
3. **IF** : Vérification du succès
4. **Log Success/Error** : Note pour le suivi

### Exécution

Le workflow :
1. Se déclenche automatiquement selon le cron
2. Appelle `POST /api/v1/jobs/discover/run`
3. Vérifie si `success === true`
4. Log le résultat (succès ou erreur)

## 📊 Monitoring

### Voir les exécutions

1. Dans n8n, aller dans **"Executions"**
2. Filtrer par workflow "WM Module A - Discover Products"
3. Voir les détails de chaque exécution

### Vérifier les résultats

Dans chaque exécution, vous pouvez voir :
- Le statut HTTP
- La réponse JSON avec les statistiques
- Les erreurs éventuelles

## 🔄 Mise à jour du workflow

Si vous modifiez le workflow dans n8n :

1. Cliquer sur **"..."** → **"Download"**
2. Sauvegarder le fichier JSON dans `n8n/workflows/`
3. Commit dans Git pour versionner

## 📝 Notes importantes

- Le workflow utilise `http://app:8000` car n8n et l'app sont dans le même docker-compose
- Si vous exposez le backend via nginx, vous pouvez utiliser l'URL HTTPS externe
- Le timeout est configuré à 5 minutes (300000ms)
- Les erreurs sont loggées mais n'interrompent pas le workflow

## 🆘 Dépannage

### Le workflow ne se déclenche pas

- Vérifier que le workflow est **actif**
- Vérifier la timezone de n8n (devrait être Europe/Paris)
- Vérifier l'expression cron

### Erreur de connexion au backend

- Vérifier que le service `app` est démarré : `docker-compose ps app`
- Vérifier les logs : `docker-compose logs app`
- Tester manuellement : `curl http://localhost:8000/health`

### Timeout

- Augmenter le timeout dans le nœud HTTP Request
- Vérifier que le job ne prend pas trop de temps

---

*Documentation créée le : 02/12/2025*

