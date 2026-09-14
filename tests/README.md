# Tests

Ce répertoire contient les tests unitaires et d'intégration pour le projet NutriSénégal.

## Structure

- `test_nutrition_engine.py` - Tests du moteur de règles nutritionnelles
- `test_api.py` - Tests des endpoints de l'API
- `test_menu_parser.py` - Tests du parser NLP
- `test_alternatives_filter.py` - Non-régression du filtre allergènes de `/alternatives`
- `conftest.py` - Fixtures partagées (base SQLite en mémoire, client FastAPI)

## Base de test

Aucun test ne touche PostgreSQL. `conftest.py` monte une base SQLite en mémoire
(recréée à chaque test) et surcharge la dépendance de session de chaque module
de routes, qui instancie son propre `Database()`.

Fixtures disponibles :

| Fixture | Rôle |
|---------|------|
| `engine` | Moteur SQLite en mémoire (portée fonction) |
| `db_session` | Session SQLAlchemy isolée |
| `seeded_db` | 2 plats, leurs ingrédients et 1 utilisateur |
| `client` | `TestClient` FastAPI branché sur la base de test |

Rappel : tous les routers sont montés sous `/api` (voir `api/router.py`).

## Exécution des tests

### Tous les tests
```bash
pytest
```

### Avec couverture de code
```bash
pytest --cov=api --cov-report=html
```

### Tests spécifiques
```bash
pytest tests/test_nutrition_engine.py -v
pytest tests/test_api.py::TestHealthProfiles -v
```

### Tests ciblés
Aucun marqueur n'est défini pour l'instant : cibler un fichier ou une classe.

```bash
pytest tests/test_api.py::TestAlternatives -v
```

## Couverture de code

Après avoir exécuté les tests avec couverture, ouvrez `htmlcov/index.html` dans un navigateur pour voir le rapport détaillé.

## Bonnes pratiques

1. **Isolation** : Chaque test doit être indépendant
2. **Fixtures** : Utiliser des fixtures pour les données de test réutilisables
3. **Nommage** : Noms de tests descriptifs (test_should_do_something_when_condition)
4. **Assertions** : Une assertion principale par test
5. **Mock** : Mocker les dépendances externes (DB, API)

## Ajout de nouveaux tests

1. Créer un fichier `test_*.py` dans ce répertoire
2. Importer pytest et les modules à tester
3. Créer des classes de test avec préfixe `Test`
4. Définir des méthodes de test avec préfixe `test_`
5. Utiliser des fixtures pour les données communes

Exemple :
```python
import pytest

class TestMyFeature:
    @pytest.fixture
    def sample_data(self):
        return {"key": "value"}
    
    def test_something(self, sample_data):
        result = my_function(sample_data)
        assert result == expected_value
```
