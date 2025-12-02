# 🔧 Solution immédiate : Accès à n8n.w3lg.fr

## 🔍 Problème identifié

Votre DNS local (bbox.lan) ne résout pas encore `n8n.w3lg.fr`, mais :
- ✅ Le DNS public (Google, Cloudflare) résout correctement
- ✅ Le serveur fonctionne parfaitement
- ✅ n8n est accessible depuis le serveur

## ✅ SOLUTION IMMÉDIATE : Modifier le fichier hosts Windows

Cette solution permet d'accéder immédiatement à n8n sans changer votre configuration DNS.

### Étapes :

1. **Ouvrez le Bloc-notes en tant qu'Administrateur** :
   - Cliquez sur le menu Démarrer
   - Tapez "Bloc-notes"
   - Clic droit → "Exécuter en tant qu'administrateur"

2. **Ouvrez le fichier hosts** :
   - Menu Fichier → Ouvrir
   - Naviguez vers : `C:\Windows\System32\drivers\etc\`
   - Changez le filtre de "Documents texte" à "Tous les fichiers"
   - Ouvrez le fichier `hosts`

3. **Ajoutez cette ligne à la fin du fichier** :
   ```
   135.181.253.60    n8n.w3lg.fr
   ```

4. **Sauvegardez** (Ctrl+S) et fermez

5. **Videz le cache DNS** :
   ```powershell
   ipconfig /flushdns
   ```

6. **Rafraîchissez votre navigateur** et allez sur : `https://n8n.w3lg.fr`

---

## 🔄 Alternative : Changer temporairement le DNS Windows

### Méthode graphique :

1. Ouvrez `Paramètres` → `Réseau et Internet`
2. Cliquez sur votre connexion (WiFi ou Ethernet)
3. Cliquez sur "Modifier les options de la carte réseau"
4. Clic droit sur votre connexion → `Propriétés`
5. Sélectionnez `Protocole Internet version 4 (TCP/IPv4)` → `Propriétés`
6. Cochez `Utiliser les adresses de serveur DNS suivantes` :
   - **Serveur DNS préféré** : `8.8.8.8`
   - **Serveur DNS alternatif** : `1.1.1.1`
7. Cliquez sur `OK` partout
8. Rafraîchissez votre navigateur

### Méthode ligne de commande (PowerShell en Admin) :

```powershell
# Trouver le nom de votre interface réseau
Get-NetAdapter | Select Name, InterfaceDescription

# Remplacer "Ethernet" par le nom de votre interface
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8,1.1.1.1

# Vider le cache DNS
ipconfig /flushdns
```

---

## ⏰ Solution automatique : Attendre la propagation DNS

La propagation DNS peut prendre **5-30 minutes** pour votre DNS local.

**Pour vérifier si c'est résolu :**
```powershell
nslookup n8n.w3lg.fr
```

Quand vous verrez `Address: 135.181.253.60`, c'est bon ! 🎉

---

## ✅ Vérification

Une fois l'une des solutions appliquée, vérifiez :

```powershell
# Vérifier la résolution DNS
nslookup n8n.w3lg.fr

# Devrait retourner : Address: 135.181.253.60

# Tester dans le navigateur
# https://n8n.w3lg.fr
```

---

## 📝 Note importante

Si vous avez utilisé la solution du fichier `hosts`, **pensez à supprimer la ligne** une fois que le DNS local sera propagé (après 24h maximum).

---

*Document créé le : 02/12/2025*

