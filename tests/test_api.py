"""
Tests des endpoints de l'API

Tous les routers sont montés sous le préfixe `/api` (voir `api/router.py`) :
les chemins nus (`/dishes`, `/users/register`) renvoient 404.

Le client est branché sur la base SQLite de `conftest.py` : aucun accès au
PostgreSQL de développement.
"""
import pytest


class TestInfrastructure:
    """Endpoints hors router, toujours disponibles"""

    def test_racine(self, client):
        response = client.get('/')

        assert response.status_code == 200
        assert response.json()['status'] == 'operational'

    def test_healthcheck(self, client):
        response = client.get('/health')

        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

    def test_schema_openapi(self, client):
        response = client.get('/openapi.json')

        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert '/api/dishes' in data['paths']

    def test_docs_accessibles(self, client):
        assert client.get('/docs').status_code == 200


class TestPrefixeApi:
    """Le préfixe /api n'est pas optionnel"""

    @pytest.mark.parametrize('path', ['/dishes', '/users/register',
                                      '/health-profiles/diseases'])
    def test_chemin_sans_prefixe_renvoie_404(self, client, path):
        assert client.get(path).status_code == 404


class TestUsers:
    def test_inscription(self, client):
        response = client.post('/api/users/register', json={
            'id': 'u-new',
            'first_name': 'Awa',
            'last_name': 'Diop',
            'gender': 'F',
            'weight': 65,
        })

        assert response.status_code == 200
        assert response.json()['user_id'] == 'u-new'

    def test_inscription_en_double_refusee(self, client, seeded_db):
        payload = {'id': 'u1', 'first_name': 'Test',
                   'last_name': 'User', 'gender': 'F'}

        response = client.post('/api/users/register', json=payload)

        assert response.status_code == 400

    def test_champs_obligatoires_manquants(self, client):
        response = client.post('/api/users/register', json={'first_name': 'Test'})

        assert response.status_code == 422

    def test_profil_utilisateur_inexistant(self, client):
        response = client.get('/api/users/inconnu/profile')

        assert response.status_code == 404


class TestDishes:
    def test_liste_des_plats(self, client, seeded_db):
        response = client.get('/api/dishes', params={'limit': 10})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert {d['name'] for d in data} == {'Thiéboudienne', 'Mafé cacahuète'}

    def test_liste_vide_sans_donnees(self, client):
        response = client.get('/api/dishes')

        assert response.status_code == 200
        assert response.json() == []

    def test_filtre_meal_type(self, client, seeded_db):
        response = client.get('/api/dishes', params={'meal_type': 'lunch'})

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_meal_type_invalide_rejete(self, client):
        response = client.get('/api/dishes', params={'meal_type': 'brunch'})

        assert response.status_code == 422

    def test_limite_negative_rejetee(self, client):
        response = client.get('/api/dishes', params={'limit': -1})

        assert response.status_code == 422

    def test_limite_trop_grande_rejetee(self, client):
        response = client.get('/api/dishes', params={'limit': 1000})

        assert response.status_code == 422

    def test_details_plat_inexistant(self, client):
        response = client.get('/api/inconnu/dish_details')

        assert response.status_code == 404


class TestRechercheDeplat:
    """`?search=` : c'est ce qui permet a WF3 de passer d'un nom de plat a un
    dish_id, donc d'atteindre /analyze-dish, /alternatives et /dish_details.
    """

    def test_nom_exact(self, client, seeded_db):
        response = client.get('/api/dishes', params={'search': 'Thiéboudienne'})

        assert response.status_code == 200
        assert [d['name'] for d in response.json()] == ['Thiéboudienne']

    def test_casse_ignoree(self, client, seeded_db):
        response = client.get('/api/dishes', params={'search': 'thiéboudienne'})

        assert [d['name'] for d in response.json()] == ['Thiéboudienne']

    def test_fragment_de_nom(self, client, seeded_db):
        response = client.get('/api/dishes', params={'search': 'mafé'})

        assert [d['name'] for d in response.json()] == ['Mafé cacahuète']

    def test_sans_accent(self, client, seeded_db):
        """Ce que tape reellement un utilisateur sur un clavier de telephone :
        ILIKE ne rattrape pas l'accent manquant, le rapprochement approchant si.
        """
        response = client.get('/api/dishes', params={'search': 'thieboudienne'})

        assert [d['name'] for d in response.json()] == ['Thiéboudienne']

    def test_faute_de_frappe(self, client, seeded_db):
        response = client.get('/api/dishes', params={'search': 'thiebboudiene'})

        assert [d['name'] for d in response.json()] == ['Thiéboudienne']

    def test_plat_inconnu_renvoie_une_liste_vide(self, client, seeded_db):
        """Pas de 404 : l'absence de correspondance est un resultat normal, que
        WF3 traduit en repli sur /analyze-ingredients."""
        response = client.get('/api/dishes', params={'search': 'pizza'})

        assert response.status_code == 200
        assert response.json() == []

    def test_renvoie_un_identifiant_exploitable(self, client, seeded_db):
        response = client.get('/api/dishes', params={'search': 'mafé'})

        assert response.json()[0]['id'] == 'd2'

    def test_combine_avec_meal_type(self, client, seeded_db):
        response = client.get('/api/dishes',
                              params={'search': 'mafé', 'meal_type': 'dinner'})

        assert response.json() == []

    def test_terme_trop_court_rejete(self, client):
        response = client.get('/api/dishes', params={'search': 'a'})

        assert response.status_code == 422


class TestAnalyse:
    def test_analyse_plat_inexistant(self, client):
        response = client.post('/api/analyze-dish', json={
            'dish_id': 'inconnu',
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 404

    def test_analyse_plat_existant(self, client, seeded_db):
        response = client.post('/api/analyze-dish', json={
            'dish_id': 'd1',
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Thiéboudienne'
        assert 0 <= data['score'] <= 100
        assert data['alert_level'] in ('safe', 'caution', 'danger', 'critical')

    def test_analyse_signale_l_allergene(self, client, seeded_db):
        """Le Mafé contient de la pâte d'arachide (ingrédient i2)."""
        response = client.post('/api/analyze-dish', json={
            'dish_id': 'd2',
            'health_profile': {'diseases': [], 'allergens': ['Arachides'],
                               'weight': 70},
        })

        assert response.status_code == 200
        alerts = response.json()['allergen_alerts']
        assert [a['name'] for a in alerts] == ['Arachides']


class TestAlternatives:
    def test_plat_inexistant(self, client):
        response = client.post('/api/alternatives/inconnu')

        assert response.status_code == 404

    def test_structure_de_la_reponse(self, client, seeded_db):
        response = client.post('/api/alternatives/d1',
                               params={'limit': 5})

        assert response.status_code == 200
        data = response.json()
        assert data['original_dish_id'] == 'd1'
        assert data['original_dish_name'] == 'Thiéboudienne'
        assert isinstance(data['alternatives'], list)

    def test_aucune_alternative_avec_allergene(self, client, seeded_db):
        """Régression : le Mafé (arachide) ne doit jamais être proposé à un
        profil allergique, même si son score dépasse celui du plat d'origine."""
        response = client.post('/api/alternatives/d1', json={
            'diseases': [], 'allergens': ['Arachides'], 'weight': 70,
        })

        assert response.status_code == 200
        proposed = {a['dish_name'] for a in response.json()['alternatives']}
        assert 'Mafé cacahuète' not in proposed


class TestRecommandations:
    def test_utilisateur_inexistant(self, client):
        response = client.get('/api/recommendations/inconnu')

        assert response.status_code == 404


class TestHealthProfiles:
    def test_liste_des_maladies(self, client):
        response = client.get('/api/health-profiles/diseases')

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_liste_des_allergenes(self, client):
        response = client.get('/api/health-profiles/allergens')

        assert response.status_code == 200
        assert isinstance(response.json(), list)
