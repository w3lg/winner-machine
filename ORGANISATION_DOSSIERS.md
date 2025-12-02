# Organisation des dossiers - Winner Machine v1

## 📁 Structure finale

```
H:\Mon Drive\Marcus\
├── docs\                          # ✅ PROJET WINNER MACHINE (à versionner)
│   ├── README_project_overview.md
│   ├── architecture_v1.md
│   ├── linear_epics.md
│   └── RESUME_DOCUMENTATION.md
│
├── _local_config\                 # ❌ CONFIG LOCALE (JAMAIS versionner)
│   ├── README.md                  # Documentation de ce dossier
│   │
│   ├── credentials\               # Tokens et credentials
│   │   ├── w3lg-github-credentials.txt
│   │   ├── w3lg-linear-token.txt
│   │   └── w3lg-config.env
│   │
│   ├── ssh_keys\                  # Clés SSH
│   │   ├── ssh_key                # ⚠️ CLÉ PRIVÉE (SECRÈTE)
│   │   ├── ssh_key.pub            # Clé publique
│   │   └── SSH_old\               # Anciennes clés
│   │
│   ├── scripts\                   # Scripts utilitaires
│   │   ├── w3lg-use-github.ps1
│   │   ├── w3lg-use-linear.ps1
│   │   ├── w3lg-load-all.ps1
│   │   ├── w3lg-liste-tout.ps1
│   │   ├── test_ssh_connection.bat
│   │   └── test_ssh_connection.sh
│   │
│   ├── docs\                      # Docs de configuration
│   │   ├── CONFIGURATION_GITHUB.md
│   │   ├── CONNEXION_REUSSIE.md
│   │   ├── DEPLOIEMENT_SSH.md
│   │   ├── LISTE_GITHUB_LINEAR.md
│   │   └── ...
│   │
│   └── backups\                   # Sauvegardes
│       └── git_config_global_backup.txt
│
├── .gitignore                     # ✅ Ignore _local_config/
└── ORGANISATION_DOSSIERS.md       # ✅ Ce fichier
```

---

## ✅ Fichiers du projet Winner Machine (à versionner)

Tous dans `docs/` :
- `README_project_overview.md`
- `architecture_v1.md`
- `linear_epics.md`
- `RESUME_DOCUMENTATION.md`

---

## ❌ Fichiers de configuration locale (JAMAIS versionner)

Tous dans `_local_config/` :
- **Credentials** : tokens GitHub, Linear
- **Clés SSH** : clés privées/publiques
- **Scripts** : scripts utilitaires PowerShell
- **Documentation config** : docs de configuration SSH/GitHub/Linear
- **Backups** : sauvegardes de config Git

**⚠️ Tout le dossier `_local_config/` est ignoré par Git** (voir `.gitignore`)

---

## 🚀 Utilisation

### Pour utiliser les scripts de configuration

Depuis la racine du projet :

```powershell
# Charger GitHub
. .\_local_config\scripts\w3lg-use-github.ps1

# Charger Linear
. .\_local_config\scripts\w3lg-use-linear.ps1

# Charger tout
. .\_local_config\scripts\w3lg-load-all.ps1
```

### Pour consulter la documentation du projet

```bash
# Vue d'ensemble
cat docs/README_project_overview.md

# Architecture technique
cat docs/architecture_v1.md

# Plan de développement
cat docs/linear_epics.md
```

---

## 🔐 Sécurité

- ✅ Le dossier `_local_config/` est dans `.gitignore`
- ✅ Aucun token ou clé privée ne sera jamais commité
- ✅ Les scripts sont préconfigurés pour utiliser les bons chemins
- ⚠️ Ne jamais partager le contenu de `_local_config/`

---

## 📝 Notes

- Les scripts dans `_local_config/scripts/` sont automatiquement configurés pour pointer vers `_local_config/credentials/`
- Si vous déplacez `_local_config/`, vérifiez que les scripts fonctionnent toujours
- La documentation du projet Winner Machine reste dans `docs/` et sera versionnée

---

*Organisation effectuée le : 02/12/2025*

