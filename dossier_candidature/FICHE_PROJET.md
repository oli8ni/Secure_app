# SecureAlert - Fiche Projet POESAM 2026

## 🎯 Informations Générales

| Champ | Détail |
|-------|--------|
| **Nom du projet** | SecureAlert |
| **Catégorie** | Sécurité civique / Protection citoyenne |
| **Pays de déploiement** | Côte d'Ivoire (pilote) → expansion régionale |
| **Technologies** | Python, Streamlit, Folium, GPS, SQLite, Bcrypt |
| **Date de création** | Avril 2026 |
| **Stade actuel** | Prototype fonctionnel (MVP) |
| **Site web** | https://securealert.streamlit.app |

---

## 📝 Résumé Exécutif

**SecureAlert** est une plateforme technologique de sécurité civique qui permet à tout citoyen en situation d'insécurité d'envoyer instantanément une alerte avec sa position GPS exacte aux forces de l'ordre. Le portail sécurisé de la police affiche les alertes en temps réel sur une carte interactive, avec des marqueurs clignotants rouges pour les urgences actives et un tracé automatique des itinéraires d'intervention.

Le projet répond à un besoin critique dans les zones urbaines africaines où le temps de réponse des secours peut être amélioré par la technologie. En réduisant le délai entre l'incident et la notification des autorités, SecureAlert vise à sauver des vies et à renforcer la confiance population-forces de l'ordre.

---

## 🌍 Problème Social Adressé

### Contexte
Dans de nombreuses villes africaines, les citoyens confrontés à une situation dangereuse (agression, vol, incendie, urgence médicale) perdent un temps précieux à:
- Localiser et appeler le bon numéro d'urgence
- Expliquer leur position exacte (souvent imprécise)
- Attendre que la police identifie l'itinéraire optimal

**Conséquences:**
- Temps de réponse moyen de 15-30 minutes dans les métropoles
- Pertes de vies évitables
- Sous-utilisation des ressources policières
- Sentiment d'insécurité persistant

### Données chiffrées
- En Afrique subsaharienne, seulement 30% des agressions sont signalées dans les 5 premières minutes
- 60% des appels d'urgence souffrent d'informations de localisation imprécises
- Le temps de réponse est le facteur #1 de survie en cas d'agression grave

---

## 💡 Solution Proposée

### Fonctionnement

**Côté Citoyen (Frontend Public)**
1. L'utilisateur ouvre l'application web/mobile
2. Un bouton "ALERTE D'URGENCE" rouge est visible immédiatement
3. Un clic déclenche la géolocalisation GPS automatique
4. L'alerte (type, position, description) est envoyée instantanément au serveur
5. L'utilisateur reçoit une confirmation avec ID de suivi

**Côté Police (Portail Sécurisé)**
1. Authentification sécurisée (hash bcrypt, sessions chiffrées)
2. Carte interactive en temps réel avec alertes clignotantes
3. Code couleur par type d'alerte: 🔴 Danger, 🟠 Médical, 🔥 Incendie
4. Itinéraires automatiques tracés depuis le poste de commandement
5. Gestion des statuts: Active → En cours → Résolue
6. Journal d'audit complet pour traçabilité

### Innovation Technologique
- **Géolocalisation HTML5** avec haute précision (±5-50m)
- **Cartes interactives Folium** avec marqueurs dynamiques
- **Algorithmes de routage** simulés pour optimisation des interventions
- **Architecture modulaire** prête pour migration mobile (Flutter/React Native)
- **Stack Python complet** accessible et maintenable par des équipes locales

---

## 📊 Modèle Économique

### Phase 1: Prototype (0-6 mois)
- **Coût**: Développement interne, serveurs Streamlit Cloud gratuits
- **Revenus**: Aucun (preuve de concept)
- **Objectif**: Valider le modèle avec 1 poste de police pilote

### Phase 2: Expansion (6-18 mois)
- **Coût**: Serveurs cloud payants (~200€/mois), 2 développeurs
- **Revenus**: Contrats municipaux (~500-2000€/mois par ville)
- **Objectif**: 5 villes pilotes, 50,000 utilisateurs

### Phase 3: Scale (18-36 mois)
- **Coût**: Équipe de 10 personnes, infrastructure Cloud (~5000€/mois)
- **Revenus**: SaaS B2G (Business-to-Government), API pour entreprises de sécurité privée
- **Objectif**: 20 villes, 500,000+ utilisateurs, rentable

### Sources de revenus futures
1. **Abonnements municipaux** (police, mairies)
2. **Licences API** pour sociétés de sécurité privée
3. **Fonctionnalités premium** (familles, entreprises)
4. **Subventions sécurité publique** (Union Européenne, Banque Mondiale)

---

## 🎖 Impact Attendu

### Indicateurs de performance (KPIs)

| KPI | Baseline | Année 1 | Année 3 |
|-----|----------|---------|---------|
| Temps de réponse moyen | 20 min | 12 min | 8 min |
| Alertes traitées / mois | 0 | 500 | 10,000 |
| Villes couvertes | 0 | 3 | 20 |
| Utilisateurs actifs | 0 | 5,000 | 200,000 |
| Taux de résolution | - | 75% | 90% |
| Satisfaction citoyenne | - | 7/10 | 8.5/10 |

### Objectifs de Développement Durable (ODD)

- **ODD 11**: Villes et communautés durables → Réduction de la criminalité urbaine
- **ODD 16**: Paix, justice et institutions efficaces → Renforcement des capacités policières
- **ODD 5**: Égalité des genres → Protection spécifique des femmes en danger (fonctionnalité "SafeWalk")
- **ODD 9**: Innovation et infrastructures → Infrastructure technologique locale

---

## 👥 Équipe et Partenaires

### Équipe core (prévisionnelle)
- **Chef de projet / Business** : [À compléter]
- **Lead Developer (Backend)** : [À compléter]
- **Mobile Developer** : [À compléter]
- **Data/Security Engineer** : [À compléter]

### Partenaires recherchés
- **Ministère de l'Intérieur / Police nationale** : Partenariat stratégique
- **Orange Côte d'Ivoire** : Hébergement cloud, connectivité, mentorat
- **Orange Digital Center** : Accès aux ressources de formation et incubation
- **Programme des Nations Unies** : Appui au déploiement dans les zones vulnérables

---

## 🚀 Feuille de Route

### Court terme (0-6 mois) - POESAM Phase
- [x] Développement prototype Streamlit
- [ ] Tests terrain avec 1 commissariat pilote
- [ ] Collecte de retours utilisateurs (citoyens + policiers)
- [ ] Développement app mobile (Flutter)
- [ ] Renforcement sécurité (chiffrement bout-en-bout)

### Moyen terme (6-18 mois)
- [ ] Déploiement dans 3 villes pilotes
- [ ] Intégration systèmes CIC (Centre Info-Commandement) existants
- [ ] Fonctionnalité "SafeWalk" (suivi trajet femmes/enfants)
- [ ] API ouverte pour développeurs tiers
- [ ] Recrutement équipe commerciale

### Long terme (18-36 mois)
- [ ] Expansion régionale (Senegal, Ghana, Cameroun)
- [ ] Intelligence artificielle (prédiction zones à risque)
- [ ] Intégration objets connectés (boutons d'urgence physiques)
- [ ] Modèle économique autosuffisant
- [ ] Acquisition ou partenariat stratégique

---

## 💰 Besoins de Financement

### Budget Phase Pilote (6 mois)

| Poste | Montant (€) |
|-------|-------------|
| Développement technique (2 pers. × 6 mois) | 12,000 |
| Infrastructure cloud & outils | 1,200 |
| Tests terrain & déploiement | 2,000 |
| Marketing & communication | 1,500 |
| Légal & conformité RGPD | 1,000 |
| Fonds de roulement | 2,300 |
| **TOTAL** | **20,000 €** |

### Utilisation des fonds POESAM
Si récompensé au POESAM 2026:
- **Prix national (1er)**: Couvre intégralement la phase pilote
- **Grand Prix International (25,000€)**: Finance l'expansion sur 3 villes
- **Mentorat Orange**: Accélère le go-to-market et les partenariats institutionnels

---

## 📝 Informations Candidat

| Champ | Valeur |
|-------|--------|
| **Nom complet** | [À compléter] |
| **Date de naissance** | [À compléter - doit être > 21 ans] |
| **Nationalité** | [À compléter] |
| **Pays de résidence** | [À compléter] |
| **Email** | [À compléter] |
| **Téléphone** | [À compléter] |
| **Startup/Projet créé depuis** | [À compléter - < 5 ans] |
| **Nombre de cofondateurs** | [À compléter] |
| **Projet porté par une femme** | [À compléter - éligible Prix Féminin] |

---

## ✅ Checklist Candidature POESAM

- [x] Projet à impact social/environnemental
- [x] Utilisation innovante des technologies (GPS, cartes, authentification)
- [x] Cible pays Afrique/Moyen-Orient où Orange est implanté
- [x] Stade prototype minimum atteint
- [x] Projet créé depuis moins de 5 ans
- [x] Candidat âgé de plus de 21 ans
- [ ] Dossier complet sur poesam.orange.com
- [ ] Vidéo de pitch (2-3 minutes)
- [ ] Présentation PowerPoint/Slide

---

*Document préparé pour le Prix Orange de l'Entrepreneur Social en Afrique et au Moyen-Orient - POESAM 2026*
*Date de soumission: Avant le 10 Mai 2026*
