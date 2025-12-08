# Tests

Ce répertoire contient les tests unitaires et d'intégration pour le projet NutriSénégal.

## Structure

- `test_nutrition_engine.py` - Tests du moteur de règles nutritionnelles
- `test_api.py` - Tests des endpoints de l'API
- `test_menu_parser.py` - Tests du parser NLP
- `conftest.py` - Configuration pytest

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
pytest tests/test_api.py::TestHealthProfilesAPI -v
```

### Tests par marqueur
```bash
pytest -m unit  # Tests unitaires uniquement
pytest -m integration  # Tests d'intégration uniquement
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
