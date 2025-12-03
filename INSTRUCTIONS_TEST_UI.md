# 🔧 Instructions pour Tester l'UI

## Problème Actuel

Le container utilise encore l'ancien code HTML. Un rebuild complet est en cours.

## Vérifications à Faire

### 1. Vérifier que le Container est à Jour

Après le rebuild, vérifier dans le container :
```bash
docker compose exec app grep -A 5 'filter-decision' /app/app/templates/dashboard.html
```

Le filtre devrait avoir :
```html
<select id="filter-decision">
    <option value="Tous" selected>Tous</option>
    ...
</select>
```

### 2. Test dans le Navigateur

1. **Ouvrir** : `https://marcus.w3lg.fr/ui`
2. **Ouvrir la console** (F12)
3. **Vérifier les logs** :
   - "Dashboard chargé"
   - "Chargement des winners: /api/v1/dashboard/winners?limit=500"
   - "Winners reçus: {...}"

4. **Vérifier l'onglet Network** :
   - Requête GET vers `/api/v1/dashboard/winners`
   - Status : 200
   - Réponse : `{"success":true, "items":[...], "total_count":10}`

5. **Vérifier le tableau** :
   - Section "Produits Qualifiés (Winners)"
   - Tableau devrait afficher 10 produits
   - Filtre "Tous" devrait être sélectionné

### 3. Si Rien ne S'Affiche Toujours

Vérifier :
- ✅ Les données sont en base (10 produits, 10 scores)
- ✅ L'endpoint retourne des données : `curl 'http://localhost:8000/api/v1/dashboard/winners?decision=Tous&limit=10'`
- ✅ Le JavaScript n'a pas d'erreurs dans la console
- ✅ Le tableau est bien présent dans le DOM : `document.getElementById('winners-table')`

### 4. Test Direct de l'Endpoint

```bash
curl -s 'http://localhost:8000/api/v1/dashboard/winners?decision=Tous&limit=10' | jq '.total_count'
```

Devrait retourner : `10`

