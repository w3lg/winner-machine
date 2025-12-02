# 🔄 Pipeline Daily A→B→C - Winner Machine

## 📋 Vue d'ensemble

Le pipeline quotidien automatise l'exécution complète des modules A, B et C :
1. **Module A** : Découverte de produits depuis Keepa
2. **Module B** : Sourcing des options d'approvisionnement
3. **Module C** : Scoring et évaluation de rentabilité

## 🚀 Workflow n8n

### Informations du workflow

- **Nom** : `WM Pipeline Daily - Discover → Source → Score`
- **ID** : `wlaYVQkkS52IZcIg`
- **Statut** : ✅ **ACTIF**
- **URL n8n** : https://n8n.w3lg.fr

### Planification

- **Cron** : `15 3 * * *`
- **Fréquence** : Tous les jours à **03:15** (heure serveur)
- **Fuseau horaire** : Europe/Paris

### Structure du workflow

```
Schedule Trigger (Cron: 15 3 * * *)
    ↓
HTTP Request - Discover Job
    ↓ (si succès)
HTTP Request - Sourcing Job
    ↓ (si succès)
HTTP Request - Scoring Job
```

### Nodes détaillés

#### 1. Schedule Trigger
- **Type** : Cron
- **Expression** : `15 3 * * *`
- **Description** : Déclenche le workflow tous les jours à 03:15

#### 2. HTTP Request - Discover Job
- **Méthode** : POST
- **URL** : `http://app:8000/api/v1/jobs/discover/run`
- **Timeout** : 5 minutes (300000ms)
- **Description** : Lance le job de découverte de produits (Module A)

#### 3. HTTP Request - Sourcing Job
- **Méthode** : POST
- **URL** : `http://app:8000/api/v1/jobs/sourcing/run`
- **Timeout** : 5 minutes (300000ms)
- **Description** : Lance le job de sourcing (Module B)
- **Condition** : S'exécute uniquement si Discover a réussi

#### 4. HTTP Request - Scoring Job
- **Méthode** : POST
- **URL** : `http://app:8000/api/v1/jobs/scoring/run`
- **Timeout** : 5 minutes (300000ms)
- **Description** : Lance le job de scoring (Module C)
- **Condition** : S'exécute uniquement si Sourcing a réussi

## 📊 Endpoints appelés

### Module A : Discover
- **URL** : `http://app:8000/api/v1/jobs/discover/run`
- **Action** : Récupère les produits depuis Keepa et les stocke en base
- **Résultat** : Produits candidats avec `status="new"`

### Module B : Sourcing
- **URL** : `http://app:8000/api/v1/jobs/sourcing/run`
- **Action** : Trouve des options de sourcing pour les produits candidats
- **Résultat** : Options de sourcing créées en base

### Module C : Scoring
- **URL** : `http://app:8000/api/v1/jobs/scoring/run`
- **Action** : Calcule les scores de rentabilité pour chaque couple (produit, option)
- **Résultat** : Scores créés, statuts produits mis à jour (selected/scored/rejected)

## 🔍 Monitoring et exécutions

### Voir les exécutions dans n8n

1. **Accéder à n8n** : https://n8n.w3lg.fr
2. **Menu** : **Executions**
3. **Filtrer** : Sélectionner le workflow "WM Pipeline Daily - Discover → Source → Score"
4. **Détails** : Cliquer sur une exécution pour voir les détails de chaque node

### Vérifier les résultats

Chaque exécution affiche :
- ✅ Succès/échec de chaque étape
- 📊 Réponses JSON des endpoints (stats, etc.)
- ⏱️ Temps d'exécution
- 📝 Logs détaillés

### Tester manuellement

Pour tester le workflow sans attendre 03:15 :
1. Ouvrir le workflow dans n8n
2. Cliquer sur **"Execute Workflow"** (icône play)
3. Observer l'exécution en temps réel

## 🔄 Ancien workflow Module A

### Statut

- **Nom** : `WM Module A - Discover Products (Cron)`
- **ID** : `IgEn1CU6IUTbK09M`
- **Statut** : ❌ **DÉSACTIVÉ**
- **Raison** : Remplacé par le pipeline complet A→B→C

### Utilisation

L'ancien workflow reste disponible pour :
- Tests manuels du Module A uniquement
- Débogage spécifique au Module A
- Exécution ponctuelle si nécessaire

## 📝 Logique d'exécution

### Enchaînement conditionnel

Le workflow s'arrête automatiquement si une étape échoue :
- Si **Discover** échoue → le workflow s'arrête, Sourcing et Scoring ne s'exécutent pas
- Si **Sourcing** échoue → le workflow s'arrête, Scoring ne s'exécute pas
- Si **Scoring** échoue → le workflow s'arrête, mais Discover et Sourcing ont été exécutés

### Gestion des erreurs

- Les erreurs sont automatiquement loggées dans n8n
- Chaque node affiche son statut (succès/échec) dans les exécutions
- Les erreurs HTTP sont capturées et affichées avec les détails

## 🎯 Résultat attendu chaque jour

Après chaque exécution réussie du pipeline :
1. ✅ Nouveaux produits candidats découverts (Module A)
2. ✅ Options de sourcing trouvées pour ces produits (Module B)
3. ✅ Scores calculés et décisions prises (Module C)
4. ✅ Produits marqués comme `selected`, `scored`, ou `rejected`

## 🔧 Configuration et maintenance

### Modifier la planification

Pour changer l'heure d'exécution :
1. Ouvrir le workflow dans n8n
2. Modifier le node "Schedule Trigger"
3. Changer l'expression cron (ex: `0 4 * * *` pour 04:00)
4. Sauvegarder

### Modifier les URLs

Si les URLs des endpoints changent :
1. Ouvrir le workflow dans n8n
2. Modifier chaque node HTTP Request
3. Mettre à jour l'URL
4. Sauvegarder

### Désactiver temporairement

Pour arrêter temporairement le pipeline :
1. Ouvrir le workflow dans n8n
2. Désactiver le toggle **"Active"** en haut à droite
3. Le cron ne se déclenchera plus jusqu'à réactivation

---

*Document créé le : 02/12/2025*
*Workflow créé et activé le : 02/12/2025*

