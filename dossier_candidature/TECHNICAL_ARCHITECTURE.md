# SecureAlert - Architecture Technique

## 🏗 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         CITOYEN                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Web App    │ or │  Mobile App  │ or │  SMS/USSD    │       │
│  │  (Streamlit) │    │  (Flutter)   │    │   (Phase 3)  │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
└─────────┼───────────────────┼───────────────────┼─────────────────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   HTTPS/WSS       │
                    │   TLS 1.3         │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                        CLOUD / SERVEUR                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    API Gateway                           │ │
│  │              (FastAPI / Node.js)                       │ │
│  └──────────────────────┬─────────────────────────────────┘ │
│                         │                                   │
│  ┌──────────────┐  ┌─────▼─────┐  ┌──────────────┐         │
│  │   Service    │  │  Service  │  │   Service    │         │
│  │   Auth       │  │   Alerts  │  │   Routes     │         │
│  │   (JWT)      │  │  (CRUD)   │  │  (OSRM)      │         │
│  └──────┬───────┘  └─────┬─────┘  └──────┬───────┘         │
│         │                │               │                  │
│  ┌──────▼────────────────▼───────────────▼───────┐         │
│  │           PostgreSQL + PostGIS                 │         │
│  │         (Données géospatiales)               │         │
│  └───────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                        POLICE / CIC                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Web Portal │    │   Mobile   │    │  Dashboard   │       │
│  │   (React)    │    │   Tablet   │    │   (Tableau)  │       │
│  │   Real-time  │    │   App      │    │   Analytics  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔧 Stack Technique Actuel (Prototype POESAM)

### Frontend Citoyen
| Technologie | Usage |
|-------------|-------|
| **Streamlit** | Framework Python pour UI web rapide |
| **HTML5 Geolocation API** | Capture GPS du navigateur |
| **Folium** | Cartes interactives OpenStreetMap |
| **Leaflet.js** | Rendu cartographique côté client |

### Frontend Police
| Technologie | Usage |
|-------------|-------|
| **Streamlit** | Interface admin sécurisée |
| **Folium + MarkerCluster** | Carte temps réel multi-alertes |
| **Pandas** | Manipulation des données alertes |
| **Plotly** | Graphiques analytics |

### Backend / Données
| Technologie | Usage |
|-------------|-------|
| **Python 3.12** | Langage principal |
| **SQLite** | Base de données prototype (local) |
| **Bcrypt** | Hash des mots de passe |
| **JSON** | Format d'échange données routes |

---

## 🚀 Stack Technique Production (Phase 2)

### Mobile (Citoyen)
```
Flutter / React Native
├── Background location services
├── Push notifications (Firebase)
├── Offline mode (SQLite local + sync)
├── Biometric auth (empreinte/Face ID)
└── Crashlytics / Analytics
```

### Backend API
```
FastAPI (Python) / Node.js + Express
├── JWT Authentication
├── Rate limiting (100 req/min citoyen, 1000 req/min police)
├── Input validation (Pydantic)
├── WebSockets (Socket.io) pour temps réel
├── Background tasks (Celery + Redis)
└── API versioning (/v1/, /v2/)
```

### Base de données
```
PostgreSQL 15+ + PostGIS extension
├── Tables: alerts, users, police_stations, logs
├── Index GiST sur coordonnées GPS
├── Partitionnement par date (alerts_2026_01)
├── Backup quotidien automatisé
└── Réplication master-slave
```

### Infrastructure Cloud
```
Orange Cloud / AWS / Azure
├── Docker + Kubernetes (orchestration)
├── CDN pour assets statiques
├── Load balancer (Nginx)
├── Monitoring: Prometheus + Grafana
├── Logs: ELK Stack
└── CI/CD: GitHub Actions → Docker Hub → K8s
```

---

## 📐 Modèles de Données

### Table `alerts`
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(20) CHECK (alert_type IN ('danger','medical','fire','suspicious','other')),
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    accuracy DECIMAL(6,2),
    description TEXT,
    phone VARCHAR(20),
    device_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    route_data JSONB,
    
    -- Spatial index for fast geo queries
    CONSTRAINT valid_lat CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT valid_lon CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created ON alerts(created_at);
CREATE INDEX idx_alerts_location ON alerts USING GIST (
    ll_to_earth(latitude, longitude)
);
```

### Table `police_users`
```sql
CREATE TABLE police_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    badge_number VARCHAR(50) UNIQUE,
    role VARCHAR(20) DEFAULT 'officer',
    station VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'officer', 'dispatcher'))
);
```

### Table `alert_logs` (Audit)
```sql
CREATE TABLE alert_logs (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(100),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);
```

---

## 🔒 Sécurité

### Architecture de sécurité

| Couche | Mesure |
|--------|--------|
| **Transport** | TLS 1.3, certificats SSL, HSTS |
| **Authentification** | Bcrypt (coût 12), JWT expirant, 2FA pour admins |
| **Autorisation** | RBAC (Role-Based Access Control): admin/officer/dispatcher |
| **Données** | Chiffrement AES-256 au repos, anonymisation citoyens |
| **API** | Rate limiting, CORS restrictif, validation strict inputs |
| **Audit** | Log immuable de toutes les actions (alert_logs) |

### Flux d'authentification
```
Police Officer
     │
     ▼
POST /auth/login (username + password)
     │
     ▼
Bcrypt verify → JWT token (24h)
     │
     ▼
Authorization: Bearer <token>
     │
     ▼
Middleware verify JWT + rôle
     │
     ▼
Accès aux endpoints /police/*
```

---

## ⚡ Performance & Scalabilité

### Objectifs SLI (Service Level Indicators)

| Métrique | Objectif |
|----------|----------|
| Latence alerte (citoyen → serveur) | < 2 secondes |
| Latence affichage carte (police) | < 5 secondes |
| Disponibilité système | 99.9% |
| Précision GPS | ±10-50m |
| Concurrent users (police) | 500+ |
| Alertes / minute | 1000+ |

### Stratégies de scalabilité
1. **Caching**: Redis pour sessions et données fréquentes
2. **Database**: Partitionnement mensuel des alertes
3. **CDN**: Assets statiques sur CloudFlare / Orange CDN
4. **Load balancing**: Round-robin sur 3+ instances API
5. **Database pooling**: PgBouncer pour connexions PostgreSQL

---

## 🧪 Testing & Qualité

### Tests automatisés
```
tests/
├── unit/           # Tests unitaires (pytest)
│   ├── test_auth.py
│   ├── test_alerts.py
│   └── test_geo.py
├── integration/    # Tests API (requests + testcontainers)
│   ├── test_api_alerts.py
│   └── test_api_auth.py
├── e2e/            # Tests bout-en-bout (Selenium/Playwright)
│   └── test_emergency_flow.py
└── performance/    # Tests charge (Locust)
    └── test_load.py
```

### CI/CD Pipeline
```yaml
name: CI/CD
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=modules tests/
      - run: flake8 modules/
      - run: bandit -r modules/  # Security scan
  
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - run: docker build -t securealert .
      - run: docker push registry.securealert.io/app:latest
      - run: kubectl rollout restart deployment/securealert
```

---

## 📡 API Endpoints (Production)

### Public API (Citoyen)
```
POST /api/v1/alerts
  Body: { type, lat, lon, accuracy?, description?, phone?, device_id? }
  Response: { alert_id, status, estimated_response_time }

GET /api/v1/alerts/{id}/status
  Response: { status, created_at, resolved_at? }
```

### Private API (Police - Auth Required)
```
GET /api/v1/police/alerts?status=active&bbox=x1,y1,x2,y2
  Response: [ { id, type, lat, lon, status, created_at } ]

PATCH /api/v1/police/alerts/{id}
  Body: { status: 'in_progress', officer_id }

POST /api/v1/police/alerts/{id}/route
  Body: { points: [[lat,lon], ...] }

GET /api/v1/police/stats
  Response: { active_count, avg_response_time, alerts_today }
```

---

## 🗺 Feuille de Route Technique

### Q2 2026 (Prototype POESAM)
- [x] MVP Streamlit avec authentification
- [x] Carte Folium avec alertes clignotantes
- [x] Base SQLite + modèles
- [ ] Tests unitaires basiques

### Q3-Q4 2026 (Pilote)
- [ ] Migration FastAPI + PostgreSQL
- [ ] App Flutter (iOS/Android)
- [ ] WebSockets temps réel
- [ ] Tests sécurité (pentest)

### 2027 (Scale)
- [ ] Kubernetes + auto-scaling
- [ ] Machine Learning (prédiction zones à risque)
- [ ] Intégration systèmes CIC nationaux
- [ ] Certifications sécurité (ISO 27001)

---

*Architecture Technique - SecureAlert v1.0*
