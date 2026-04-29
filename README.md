# 🛡️ SecureAlert - Sécurité Civique en Temps Réel

**SecureAlert** est une solution technologique de protection civique qui connecte instantanément les citoyens en insécurité avec les forces de l'ordre via géolocalisation GPS précise et suivi d'itinéraires en temps réel.

> 🏆 **Projet candidat au POESAM 2026** - Prix Orange de l'Entrepreneur Social en Afrique et au Moyen-Orient

---

## 🎯 Objectif Social

Dans de nombreuses régions d'Afrique et du Moyen-Orient, l'insécurité urbaine et les violences ciblées nécessitent des outils de réponse rapide. SecureAlert vise à :

- **Réduire le temps de réponse** des forces de l'ordre grâce à la géolocalisation instantanée
- **Protéger les citoyens vulnérables** (femmes, enfants, personnes âgées) via un bouton d'alerte discret
- **Optimiser les ressources policières** par une cartographie temps réel des incidents
- **Renforcer la confiance** entre population et forces de sécurité

---

## 🏗 Architecture

### Technologies utilisées
- **Frontend**: Streamlit (Python) - Prototypage rapide & déploiement cloud
- **Cartographie**: Folium + Leaflet (OpenStreetMap)
- **Base de données**: SQLite (prototype) → PostgreSQL/PostGIS (production)
- **Sécurité**: Bcrypt pour l'authentification, chiffrement des données sensibles
- **Géolocalisation**: API Geolocation HTML5 + haute précision GPS mobile

### Structure du projet
```
app/
├── streamlit_app.py          # Page d'accueil
├── pages/
│   ├── 1_🚨_Client.py        # Portail citoyen (alerte)
│   └── 2_👮_Police.py        # Portail police (carte temps réel)
├── modules/
│   ├── database.py           # SQLite + modèles
│   ├── auth.py               # Authentification sécurisée
│   ├── geo.py                # Utilitaires GPS
│   └── alerts.py             # Gestion des alertes
└── .streamlit/config.toml    # Configuration
```

---

## 🚀 Déploiement Streamlit Cloud (Gratuit)

### Prérequis
- Compte GitHub
- Compte [Streamlit Cloud](https://streamlit.io/cloud)

### Étapes

1. **Créer un dépôt GitHub** avec ces fichiers à la racine:
   - `streamlit_app.py` (point d'entrée à la racine, ou modifier le chemin)
   - `requirements.txt`
   - Dossier `pages/`
   - Dossier `modules/`

2. **Connecter à Streamlit Cloud**:
   - Aller sur [share.streamlit.io](https://share.streamlit.io)
   - "New app" → Sélectionner le dépôt
   - Fichier principal: `app/streamlit_app.py`
   - Branch: `main`

3. **Configuration avancée**:
   - Dans Settings → Secrets, ajouter si besoin:
   ```toml
   [auth]
   secret_key = "votre-cle-secrete"
   ```

4. **Lancer l'application**:
   - L'URL sera du type: `https://votre-app.streamlit.app`

---

## 📱 Migration Mobile (Phase 2)

### Stack mobile prévue
- **Flutter** ou **React Native** pour l'app citoyenne
- **Notifications push** via Firebase Cloud Messaging
- **Background location** pour traçage même en arrière-plan
- **Offline mode**: stockage local des alertes avec sync automatique

### Stack backend production
- **Serveur**: AWS / Azure / Orange Cloud
- **API**: FastAPI (Python) ou Node.js
- **Base de données**: PostgreSQL + PostGIS pour requêtes géospatiales
- **Temps réel**: WebSockets ou Socket.io pour mises à jour instantanées
- **Sécurité**: TLS 1.3, JWT tokens, rate limiting

---

## 👥 Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|------|-------------|--------------|
| Admin | `admin` | `Police2026!` |
| Agent | `officer1` | `Officer2026!` |

---

## 🔒 Sécurité & Confidentialité

- 🔐 **Authentification**: Hash bcrypt avec salt
- 🛡️ **Session**: Gestion par state Streamlit
- 📍 **Localisation**: Précision GPS configurable, données chiffrées en transit
- 🗑️ **RGPD**: Suppression automatique des données après 30 jours (résolues)
- 🔍 **Audit**: Journal complet de toutes les actions

---

## 🌍 Impact & Vision

**Objectifs de développement durable (ODD)**:
- **ODD 11**: Villes et communautés durables (sécurité urbaine)
- **ODD 16**: Paix, justice et institutions efficaces
- **ODD 5**: Égalité des genres (protection des femmes en danger)

**KPIs visés**:
- Réduction de 40% du temps de réponse policière
- Couverture de 500+ quartiers dans 12 villes pilotes
- 10,000+ citoyens protégés dans la première année

---

## 📧 Contact

**Projet POESAM 2026**
- Plateforme: [poesam.orange.com](https://poesam.orange.com)
- Email: [poesam@orange.com](mailto:poesam@orange.com)
- Date limite: **10 Mai 2026**

---

*Développé avec ❤️ pour la sécurité de nos communautés.*
