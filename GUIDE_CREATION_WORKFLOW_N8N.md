# 📝 Guide : Créer le workflow n8n Module A manuellement

## ⚡ Méthode rapide (5 minutes)

### 1. Accéder à n8n

Ouvrez votre navigateur et allez sur : **https://n8n.w3lg.fr**

### 2. Se connecter

- **Email/Username** : `admin`
- **Password** : (le mot de passe configuré dans `.env`)

### 3. Créer un nouveau workflow

1. Cliquez sur **"Workflows"** dans le menu de gauche
2. Cliquez sur le bouton **"+"** ou **"New Workflow"** en haut à droite

### 4. Ajouter le Schedule Trigger

1. Dans la barre de recherche en haut, tapez : **"Schedule Trigger"**
2. Cliquez sur **"Schedule Trigger"** dans les résultats
3. Le node apparaît sur le canvas
4. **Cliquez sur le node** pour le configurer :
   - Dans **"Trigger Interval"**, choisissez **"Every Day"**
   - **Hour** : `3`
   - **Minute** : `0`
   - Ou utilisez **"Custom Cron Expression"** : `0 3 * * *`
5. Cliquez sur **"Save"** (en bas du panneau de configuration)

### 5. Ajouter le HTTP Request

1. Cherchez **"HTTP Request"** dans la barre de recherche
2. Cliquez sur **"HTTP Request"**
3. Le node apparaît à côté du Schedule Trigger
4. **Cliquez sur le node HTTP Request** pour le configurer :
   - **Method** : `POST`
   - **URL** : `http://app:8000/api/v1/jobs/discover/run`
   - **Authentication** : `None`
   - Dans **"Options"** → **"Timeout"** : `300000` (5 minutes)
5. Cliquez sur **"Save"**

### 6. Connecter les nodes

1. Cliquez sur le **point de sortie** (petit cercle) à droite du Schedule Trigger
2. Glissez vers le **point d'entrée** (petit cercle) à gauche du HTTP Request
3. Une flèche apparaît entre les deux nodes

### 7. Nommer et sauvegarder

1. En haut à gauche, cliquez sur **"Untitled"** ou le nom du workflow
2. Renommez-le : **"WM Module A - Discover Products"**
3. Cliquez sur **"Save"** (icône disquette en haut à droite)

### 8. Activer le workflow

1. En haut à droite, trouvez le toggle **"Active"**
2. Cliquez dessus pour l'activer (il devient vert/bleu)
3. Le workflow est maintenant actif et s'exécutera tous les jours à 03:00 !

## ✅ Vérification

Pour tester immédiatement :

1. Cliquez sur le bouton **"Execute Workflow"** (icône play) en haut
2. Vérifiez les résultats dans l'onglet **"Executions"**

## 🔧 Configuration de l'URL (si nécessaire)

Si `http://app:8000` ne fonctionne pas (erreur de connexion), vous pouvez utiliser l'URL publique :

1. Cliquez sur le node **HTTP Request**
2. Changez l'URL pour : `https://marcus.w3lg.fr/api/v1/jobs/discover/run`
3. Sauvegardez

---

## 📊 Structure finale du workflow

```
Schedule Trigger (Cron: 0 3 * * *)
    ↓
HTTP Request (POST http://app:8000/api/v1/jobs/discover/run)
```

C'est tout ! Le workflow est maintenant prêt et actif. 🎉

---

*Guide créé le : 02/12/2025*

