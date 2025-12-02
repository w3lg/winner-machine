# 🔧 Solution : Problème d'accès à n8n.w3lg.fr - Pare-feu Cloud

## 🔍 Diagnostic

Le serveur fonctionne correctement :
- ✅ nginx écoute sur les ports 80 et 443
- ✅ n8n fonctionne et répond en local
- ✅ Certificats SSL valides
- ✅ Configuration nginx correcte

**Le problème** : Les ports **80** et **443** sont probablement **bloqués par le pare-feu cloud de l'hébergeur**.

---

## ✅ SOLUTION : Ouvrir les ports dans le pare-feu Cloud

L'IP `135.181.253.60` semble être une IP Hetzner Cloud. Vous devez ouvrir les ports dans le **Cloud Firewall** de votre hébergeur.

### Pour Hetzner Cloud :

1. **Connectez-vous à votre compte Hetzner Cloud Console** :
   - Allez sur : https://console.hetzner.cloud/

2. **Accédez aux Firewalls** :
   - Menu : `Networking` → `Firewalls`
   - Ou directement : https://console.hetzner.cloud/projects/YOUR_PROJECT_ID/firewalls

3. **Trouvez le Firewall attaché à votre serveur** :
   - Cliquez sur le firewall qui protège votre serveur `marcus` (IP: 135.181.253.60)

4. **Ajoutez les règles suivantes** :

   **Règle 1 : Port 80 (HTTP)**
   - **Direction** : Inbound
   - **Port** : 80
   - **Protocol** : TCP
   - **Source IPs** : 0.0.0.0/0 (tout le monde, ou votre IP spécifique)
   - **Description** : Allow HTTP

   **Règle 2 : Port 443 (HTTPS)**
   - **Direction** : Inbound
   - **Port** : 443
   - **Protocol** : TCP
   - **Source IPs** : 0.0.0.0/0 (tout le monde, ou votre IP spécifique)
   - **Description** : Allow HTTPS

5. **Sauvegardez** et attendez quelques secondes pour la propagation

---

### Pour d'autres hébergeurs :

#### OVH Cloud :
1. Accédez au **Network Security** dans votre projet
2. Ouvrez les ports 80 et 443 dans le **Firewall**

#### DigitalOcean :
1. Allez dans **Networking** → **Firewalls**
2. Ajoutez les règles pour les ports 80 et 443

#### AWS EC2 :
1. Allez dans **EC2** → **Security Groups**
2. Ajoutez les règles **Inbound** pour TCP 80 et 443

#### Scaleway :
1. Allez dans **Network** → **Security Groups**
2. Ajoutez les règles pour les ports 80 et 443

---

## 🔍 Vérification

Après avoir ouvert les ports, vérifiez depuis votre machine :

```bash
# Test depuis Windows (PowerShell)
Test-NetConnection -ComputerName n8n.w3lg.fr -Port 443
Test-NetConnection -ComputerName n8n.w3lg.fr -Port 80

# Ou avec telnet
telnet n8n.w3lg.fr 443
telnet n8n.w3lg.fr 80
```

Vous pouvez aussi tester depuis un site en ligne :
- https://www.yougetsignal.com/tools/open-ports/
- Entrez l'IP : `135.181.253.60`
- Testez les ports : `80` et `443`

---

## 📝 Notes importantes

1. **Sécurité** : Si vous voulez restreindre l'accès, vous pouvez limiter les **Source IPs** à votre IP spécifique au lieu de `0.0.0.0/0`

2. **Port 22 (SSH)** : Normalement déjà ouvert, sinon ajoutez-le aussi :
   - Direction : Inbound
   - Port : 22
   - Protocol : TCP

3. **Attente** : Les changements de pare-feu peuvent prendre quelques secondes à quelques minutes pour se propager

---

## ✅ Une fois les ports ouverts

1. Attendez 1-2 minutes
2. Testez depuis votre navigateur : `https://n8n.w3lg.fr`
3. Testez depuis votre smartphone : `https://n8n.w3lg.fr`

Cela devrait maintenant fonctionner ! 🎉

---

*Document créé le : 02/12/2025*

