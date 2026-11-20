# 🛡️ SportGuard AI

Plateforme d'**analyse de performance sportive** et de **prévention des blessures** : suivi de la charge d'entraînement, estimation d'un score de risque par machine learning, et analyse du mouvement par caméra (squat) avec MediaPipe.

> Projet personnel à but pédagogique. Les données du modèle sont **synthétiques** et l'application n'est pas un outil médical.

<!--
## Captures d'écran
![Dashboard](docs/dashboard.png)
![Analyse du squat](docs/squat.png)
-->

## Fonctionnalités

- **Suivi des séances** : durée, intensité (1 à 10) et type d'entraînement. Charge de la séance = durée × intensité.
- **Bien-être quotidien** : sommeil, fatigue, stress, courbatures (un seul relevé par athlète et par jour).
- **Charge d'entraînement** : charge aiguë (7 jours), charge chronique (moyenne hebdomadaire sur 28 jours) et **ACWR** (rapport aigu/chronique).
- **Score de risque de blessure** : modèle de régression logistique alimenté par la charge et le bien-être, enregistré dans l'historique.
- **Analyse du squat par webcam** : détection du squelette (MediaPipe), angle du genou en temps réel, comptage des répétitions et score de profondeur.
- **Dashboard Angular** : cartes de synthèse, graphiques (Chart.js), formulaires de saisie et tableau des analyses de mouvement.

## Architecture

```
Caméra (MediaPipe) ─┐
                    ├─▶ API FastAPI ─▶ PostgreSQL
Angular (front) ────┘        │
                             └─▶ Modèle ML (scikit-learn)
```

| Couche | Technologies |
|---|---|
| Interface | Angular 21, Chart.js (et un dashboard Streamlit alternatif) |
| API | Python 3.11, FastAPI, SQLAlchemy, bcrypt |
| Base de données | PostgreSQL |
| Machine learning | pandas, numpy, scikit-learn |
| Vision | MediaPipe (PoseLandmarker), OpenCV |

## Structure du projet

```
sportguard-ai/
├── app/                  # API FastAPI
│   ├── main.py           # routes
│   ├── database.py       # connexion PostgreSQL
│   ├── models.py         # tables SQLAlchemy
│   ├── schemas.py        # validation des données (Pydantic)
│   ├── create_tables.py  # création des tables
│   └── services/         # logique métier (charge/ACWR, modèle ML)
├── ml/                   # génération des données et entraînement
├── vision/               # analyse du squat (MediaPipe)
├── frontend/             # application Angular
└── dashboard/            # dashboard Streamlit (alternatif)
```

## Installation

### Prérequis

Python 3.11, PostgreSQL, Node.js 22 (npm 11 recommandé) et une webcam pour l'analyse du squat.

### 1. Base de données

```sql
CREATE USER sg_user WITH PASSWORD 'ton_mot_de_passe';
CREATE DATABASE sportguard OWNER sg_user;
```

Crée un fichier `.env` à la racine :

```
DATABASE_URL=postgresql+psycopg2://sg_user:ton_mot_de_passe@localhost:5432/sportguard
```

### 2. Back-end

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m app.create_tables
```

### 3. Modèle de risque

```bash
python ml/generate_data.py     # génère ml/synthetic_data.csv
python ml/train.py             # entraîne et sauvegarde ml/model.pkl
```

### 4. Lancement

```bash
uvicorn app.main:app --reload  # API sur http://127.0.0.1:8000 (docs : /docs)
```

Dans un second terminal :

```bash
cd frontend
npm install
ng serve                       # interface sur http://localhost:4200
```

### 5. Analyse du squat (optionnel)

```bash
python vision/squat_tracker.py
```

Place-toi de profil, jambe entière visible. Le modèle MediaPipe se télécharge automatiquement au premier lancement. Touche `q` pour terminer : le résultat est envoyé à l'API.

## Endpoints principaux

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | Vérifier que l'API tourne |
| GET / POST | `/athletes` | Lister / créer des athlètes |
| POST | `/sessions` | Enregistrer une séance |
| POST | `/wellness` | Enregistrer le bien-être du jour |
| GET | `/athletes/{id}/workload` | Charge aiguë, chronique et ACWR |
| GET | `/athletes/{id}/risk` | Calculer et enregistrer le score de risque |
| GET | `/athletes/{id}/load-history` | Charge quotidienne (graphique) |
| GET | `/athletes/{id}/risk-history` | Historique du score de risque |
| POST | `/movements` | Enregistrer une analyse de mouvement |
| GET | `/athletes/{id}/movements` | Lister les analyses de mouvement |

## Limites actuelles

- **Données synthétiques** : le modèle est entraîné sur des données simulées (AUC d'environ 0,82). Ce résultat valide la chaîne de traitement, pas la performance réelle sur de vrais athlètes.
- **Le score n'est pas une probabilité calibrée** : le modèle est entraîné avec des classes pondérées, il faut le lire comme un score relatif (faible, moyen, élevé). Les seuils sont arbitraires.
- **Score de squat** : il mesure uniquement la profondeur (angle du genou). L'angle du dos et l'alignement des genoux ne sont pas encore analysés.
- **Pas d'authentification** : les mots de passe sont hachés en base, mais l'API n'a pas encore de connexion ni de gestion des rôles.
- La table des blessures existe, mais elle n'a pas encore d'endpoint ni d'écran.

## Pistes d'amélioration

- Authentification (JWT) et rôles athlète / coach
- Création d'athlète et saisie des blessures depuis l'interface
- Analyse posturale plus riche (angle du dos, valgus du genou) et d'autres exercices
- Entraînement sur des données réelles et calibration du modèle
- Docker et déploiement

## Auteur

**Bahria Med Amine** · Projet SportGuard AI
LINKEDIN : https://www.linkedin.com/in/mohamed-amine-bahria-86ab25247/