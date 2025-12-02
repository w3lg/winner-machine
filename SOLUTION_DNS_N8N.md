# 🔧 Solution au problème DNS n8n.w3lg.fr

## 🔍 Diagnostic

**Problème identifié** : Votre serveur DNS local (bbox.lan) ne résout pas encore `n8n.w3lg.fr`.

- ✅ DNS public (Google 8.8.8.8) : Résout correctement → `135.181.253.60`
- ✅ DNS public (Cloudflare 1.1.1.1) : Résout correctement → `135.181.253.60`
- ❌ DNS local (bbox.lan) : Ne résout pas → `Non-existent domain`
- ✅ Serveur : nginx et n8n fonctionnent correctement

## ✅ Solutions

### Solution 1 : Changer temporairement votre DNS (RAPIDE)

Pour accéder immédiatement à n8n, changez temporairement votre serveur DNS :

**Windows :**
1. Ouvrez `Paramètres` → `Réseau et Internet` → `Connexions`
2. Cliquez sur votre connexion active → `Propriétés`
3. Sélectionnez `Protocole Internet version 4 (TCP/IPv4)` → `Propriétés`
4. Cochez `Utiliser les adresses de serveur DNS suivantes` :
   - DNS préféré : `8.8.8.8` (Google)
   - DNS alternatif : `1.1.1.1` (Cloudflare)
5. Cliquez sur `OK` et fermez
6. **Rafraîchissez votre navigateur** et accédez à `https://n8n.w3lg.fr`

**Alternative via ligne de commande (Admin) :**
```powershell
netsh interface ip set dns "Ethernet" static 8.8.8.8
netsh interface ip add dns "Ethernet" 1.1.1.1 index=2
ipconfig /flushdns
```

### Solution 2 : Attendre la propagation DNS (AUTOMATIQUE)

La propagation DNS peut prendre :
- **Localement** : 5-30 minutes
- **Mondialement** : Jusqu'à 48 heures (mais généralement quelques heures)

**Vérification de la propagation :**
```powershell
# Vérifier avec Google DNS (devrait déjà fonctionner)
nslookup n8n.w3lg.fr 8.8.8.8

# Vérifier avec votre DNS local (devrait se mettre à jour)
nslookup n8n.w3lg.fr

# Vider le cache DNS Windows
ipconfig /flushdns
```

### Solution 3 : Accès direct via IP (TEMPORAIRE)

Vous pouvez modifier votre fichier `hosts` Windows pour forcer la résolution :

**Windows :**
1. Ouvrez le Bloc-notes en tant qu'**Administrateur**
2. Ouvrez le fichier : `C:\Windows\System32\drivers\etc\hosts`
3. Ajoutez cette ligne à la fin :
   ```
   135.181.253.60    n8n.w3lg.fr
   ```
4. Sauvegardez le fichier
5. **Rafraîchissez votre navigateur** et accédez à `https://n8n.w3lg.fr`

⚠️ **Note** : N'oubliez pas de supprimer cette ligne une fois le DNS propagé.

### Solution 4 : Vérifier la configuration DNS côté registrar

Vérifiez que la zone DNS pour `w3lg.fr` contient bien l'enregistrement A :

```
Type: A
Nom: n8n.w3lg.fr
Valeur: 135.181.253.60
TTL: 300 (ou défaut)
```

---

## ✅ Vérification que tout fonctionne côté serveur

Le serveur fonctionne parfaitement :

```bash
# DNS résout correctement
nslookup n8n.w3lg.fr 8.8.8.8
# → 135.181.253.60 ✅

# HTTPS répond
curl -k -I https://n8n.w3lg.fr
# → HTTP/2 200 ✅

# Container n8n actif
docker compose ps n8n
# → Up ✅
```

---

## 🎯 Recommandation

**Pour accéder immédiatement** : Utilisez la **Solution 1** (changer temporairement le DNS).

**Pour une solution permanente** : Attendez la propagation DNS (**Solution 2**) ou vérifiez votre configuration DNS locale si le problème persiste après 24h.

---

*Document créé le : 02/12/2025*

