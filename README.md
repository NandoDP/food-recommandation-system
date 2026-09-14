# 🍽️ NutriSénégal - Système de Recommandation Alimentaire Intelligent

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📊 Projet Data Science - Nutrition Personnalisée & Recommandations Alimentaires

Système intelligent de recommandation alimentaire basé sur l'apprentissage automatique et un moteur de règles métier, conçu pour fournir des recommandations nutritionnelles personnalisées adaptées aux profils de santé individuels.

---

## 🎯 Objectifs du Projet

Ce projet démontre l'application de techniques de **Data Science** et **Machine Learning** pour :

1. **Analyse Nutritionnelle Prédictive** : Évaluation automatique de la compatibilité des plats avec les conditions médicales
2. **Système de Recommandation** : Moteur de règles métier sophistiqué pour suggérer des alternatives alimentaires
3. **Traitement du Langage Naturel (NLP)** : Parsing intelligent de menus en français avec spaCy
4. **API REST Scalable** : Architecture microservices avec FastAPI et PostgreSQL
5. **Interface Conversationnelle** : Bot Telegram pour interaction utilisateur naturelle

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────┐
│                     TELEGRAM BOT INTERFACE                   │
│              (Interface Conversationnelle)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI REST API                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Analyze     │  │ Recommend    │  │  Health      │      │
│  │  Endpoints   │  │ Engine       │  │  Profiles    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                         │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Nutrition      │  │  Menu Parser    │  │  Rules       │ │
│  │ Engine         │  │  (spaCy NLP)    │  │  Engine      │ │
│  │ (ML Rules)     │  └─────────────────┘  └──────────────┘ │
│  └────────────────┘                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  POSTGRESQL DATABASE                         │
│  - Users & Health Profiles                                   │
│  - Dishes & Ingredients                                      │
│  - Nutritional Data (FAO)                                    │
│  - Diseases & Allergens                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Composants Data Science

### 1. **Moteur de Règles Nutritionnelles** (`api/core/nutrition_engine.py`)

Implémente un système expert basé sur des règles métier pour évaluer la compatibilité alimentaire :

```python
# Exemple de règles implémentées :
- Gestion du diabète (index glycémique, sucres)
- Hypertension (sodium, potassium)
- Maladies rénales (protéines, potassium)
- Allergènes et intolérances
- Recommandations nutritionnelles personnalisées
```

**Métriques clés** :
- Score de santé (0-100)
- Niveau d'alerte (SAFE, WARNING, DANGER)
- Recommandations d'ajustement

### 2. **Parser de Menus NLP** (`api/core/menu_parser.py`)

Utilise **spaCy** pour l'extraction d'entités nommées et la reconnaissance de plats :

```python
Technologies : spaCy, rapidfuzz
Fonctionnalités :
  - Tokenization et lemmatisation
  - Fuzzy matching pour correspondance de plats
  - Extraction de quantités et unités
  - Support du français (plats d'Afrique de l'Ouest)
```

### 3. **Calculateur Nutritionnel** (`api/core/nutrition_calculator.py`)

Calculs agrégés des valeurs nutritionnelles par portion :

- Calories (kcal)
- Macronutriments (protéines, glucides, lipides)
- Micronutriments (sodium, potassium, fibres)
- Index glycémique pondéré

### 4. **Système de Recommandation** (`api/routes/analyze.py`)

Algorithme de filtrage collaboratif et basé sur le contenu :

```python
Entrées :
  - Profil santé utilisateur
  - Historique alimentaire
  - Contraintes médicales

Sorties :
  - Top N plats recommandés
  - Alternatives personnalisées
  - Raisons de recommandation
  - Highlights nutritionnels
```

---

## 📊 Données & Modèles

### Sources de Données

1. **Base FAO** : Valeurs nutritionnelles standardisées
2. **Plats Locaux** : Cuisine d'Afrique de l'Ouest (Sénégal)
3. **Références Médicales** : Recommandations OMS pour pathologies

### Modèles de Données

- **11 tables relationnelles** (PostgreSQL)
- **Relations Many-to-Many** pour ingrédients et maladies
- **JSON fields** pour données nutritionnelles flexibles

Voir [`ER_Diagram.md`](ER_Diagram.md) et [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) pour détails.

---

## 🚀 Installation & Configuration

### Prérequis

```bash
Python 3.12+
PostgreSQL 14+
Telegram Bot Token (pour interface bot)
```

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/NandoDP/food-recommandation-system.git
cd food-recommandation-system

# 2. Créer environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Télécharger modèle spaCy français
pip install https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0-py3-none-any.whl

# 5. Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials
```

### Configuration Base de Données

```bash
# 1. Créer la base PostgreSQL
createdb nutrisenegal_db

# 2. Exécuter les migrations
alembic upgrade head

# 3. Charger les données initiales (optionnel)
python fao_data_processor.py
python extract_dishes.py
```

### Variables d'Environnement

Créer un fichier `.env` :

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nutrisenegal_db

# API
SECRET_KEY=your-secret-key-here
API_BASE_URL=http://localhost:8000

# Telegram Bot
TELEGRAM_TOKEN=your-telegram-bot-token
```

---

## 🎮 Utilisation

### 1. Lancer l'API Backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Accéder à la documentation interactive : http://localhost:8000/docs

### 2. Lancer le Bot Telegram

```bash
python telegram_bot/bot.py
```

### 3. Exemples d'API Calls

```python
import requests

# Analyser un plat
response = requests.post("http://localhost:8000/analyze-dish", json={
    "dish_id": "thieboudienne_001",
    "user_id": "12345"
})

# Obtenir recommandations
response = requests.get("http://localhost:8000/recommendations/12345?limit=5")

# Analyser un menu texte
response = requests.post("http://localhost:8000/analyze-menu", json={
    "menu_text": "Thiéboudienne avec légumes et poisson",
    "user_id": "12345"
})
```

---

## 📓 Notebooks de Démonstration

Voir le dossier `notebooks/` pour des analyses détaillées :

1. **01_data_exploration.ipynb** : Exploration des données nutritionnelles
2. **02_recommendation_engine.ipynb** : Analyse du moteur de recommandation
3. **03_health_impact_analysis.ipynb** : Impact des choix alimentaires sur la santé
4. **04_nlp_menu_parsing.ipynb** : Démonstration du parser NLP

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=api --cov-report=html

# Tests spécifiques
pytest tests/test_nutrition_engine.py -v
```

---

## 📈 Fonctionnalités Clés

### ✅ Pour les Utilisateurs

- 🔍 **Analyse de plats** : Compatibilité instantanée avec profil santé
- 🎯 **Recommandations personnalisées** : Suggestions basées sur conditions médicales
- 🔄 **Alternatives intelligentes** : Substituts alimentaires adaptés
- 📊 **Détails nutritionnels** : Informations complètes par plat
- ⚠️ **Alertes santé** : Avertissements sur ingrédients problématiques

### 🔬 Pour les Data Scientists

- 📊 **Pipeline ETL** : Traitement données FAO → PostgreSQL
- 🤖 **Moteur de règles** : Système expert configurable
- 🧠 **NLP** : Parsing de texte libre en français
- 📈 **Métriques** : Score de santé, alertes, recommandations
- 🔍 **API exploratoire** : Endpoints pour analyse de données

---

## 🏆 Cas d'Usage

### 1. Gestion du Diabète Type 2

Le système recommande des plats à faible index glycémique et alerte sur les sucres :

```
✅ Mafé aux légumes (IG: 45, Score: 85/100)
⚠️ Riz au gras (IG: 70, Score: 45/100) → Alternative suggérée
```

### 2. Hypertension Artérielle

Filtrage par teneur en sodium, recommandation d'aliments riches en potassium :

```
✅ Thiéboudienne (Na: 280mg, K: 850mg, Score: 78/100)
❌ Yassa poulet salé (Na: 1200mg) → Modification suggérée
```

### 3. Allergies & Intolérances

Détection automatique d'allergènes et suggestions d'alternatives :

```
❌ Mafé cacahuète (Contient: Arachides)
✅ Alternative: Mafé au sésame (Sans arachides, Score: 82/100)
```

---

## 🗂️ Structure du Projet

```
nutrisenegal/
├── api/                          # Backend FastAPI
│   ├── core/                     # Logique métier
│   │   ├── nutrition_engine.py   # Moteur de règles
│   │   ├── menu_parser.py        # Parser NLP
│   │   └── nutrition_calculator.py
│   ├── models/                   # Modèles SQLAlchemy
│   ├── routes/                   # Endpoints API
│   │   ├── analyze.py            # Analyse & recommandations
│   │   ├── health_profiles.py    # Gestion profils
│   │   └── users.py
│   ├── schemas/                  # Schémas Pydantic
│   └── main.py                   # Point d'entrée API
│
├── telegram_bot/                 # Bot Telegram
│   ├── services/                 # Services métier
│   │   ├── health_api.py         # Client API
│   │   ├── action_handles.py     # Handlers
│   │   └── formatters.py         # Formatage messages
│   └── bot.py                    # Point d'entrée bot
│
├── notebooks/                    # Jupyter notebooks
├── tests/                        # Tests unitaires
├── data/                         # Données (non versionné)
├── requirements.txt              # Dépendances Python
├── .env.example                  # Template configuration
├── script.sql                    # Schéma SQL
└── README.md                     # Cette documentation
```

---

## 🔧 Technologies Utilisées

### Backend
- **FastAPI** : Framework API moderne et performant
- **SQLAlchemy** : ORM pour PostgreSQL
- **Pydantic** : Validation de données
- **Alembic** : Migrations de base de données

### Data Science & ML
- **spaCy** : Traitement du langage naturel
- **NumPy/Pandas** : Manipulation de données
- **RapidFuzz** : Fuzzy string matching
- **Matplotlib/Seaborn** : Visualisations

### Interface
- **python-telegram-bot** : SDK Telegram
- **Uvicorn** : Serveur ASGI

---

## 📚 Documentation Additionnelle

<!-- - [`docs.md`](docs.md) : Documentation technique détaillée -->
- [`ER_Diagram.md`](ER_Diagram.md) : Schéma entité-relation
- [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) : Dictionnaire de données
- [`checklist_projet_nutrition.md`](checklist_projet_nutrition.md) : Checklist projet

---

<!-- ## 🤝 Contribution

Les contributions sont bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

--- -->

## 📝 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👤 Auteur

**Votre Nom**
- Portfolio: [datascienceportfol.io/maododp](https://www.datascienceportfol.io/maododp)
- LinkedIn: [linkedin.com/in/maodo-diop](https://linkedin.com/in/maodo-diop)
- GitHub: [@NandoDP](https://github.com/NandoDP)

<!-- ---

## 🙏 Remerciements

- **FAO** pour les données nutritionnelles
- **OMS** pour les recommandations médicales
- Communauté **spaCy** pour les outils NLP
- **FastAPI** et **PostgreSQL** communities

---

## 📊 Statistiques du Projet

- **Langues** : Python (95%), SQL (5%)
- **Lignes de code** : ~5000+
- **Tables DB** : 11
- **Endpoints API** : 15+
- **Plats supportés** : 50+ (cuisine sénégalaise)
- **Tests** : 30+ tests unitaires

--- -->

## 🔮 Roadmap

- [ ] Ajout de plus de cuisines (Maghreb, Afrique centrale)
- [ ] Intégration modèle ML pour prédictions caloriques
- [ ] Dashboard analytique avec Streamlit
- [ ] Support multilingue (Wolof, Anglais)
- [ ] Containerisation avec Docker
- [ ] CI/CD avec GitHub Actions

---

**⭐ Si ce projet vous intéresse, n'hésitez pas à lui donner une étoile !**
