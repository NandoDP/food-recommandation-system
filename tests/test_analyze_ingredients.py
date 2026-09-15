"""Tests de la route /api/analyze-ingredients et de son résolveur.

Cette route reçoit des ingrédients déjà extraits et normalisés par le LLM
(WF3 nlu-router) : elle ne fait aucune analyse de texte libre, contrairement à
/analyze-menu qui garde spaCy et reste le repli hors ligne.
"""
import pytest

from api.core.ingredient_resolver import normaliser, resoudre
from api.core.nutrition_calculator import _convert_to_grams


class TestNormalisation:
    """La normalisation est partagée avec WestAfricanMenuParser : les deux
    chemins d'analyse doivent rapprocher les noms de la même façon."""

    @pytest.mark.parametrize('entree, attendu', [
        ('Thiéboudienne', 'thieboudienne'),
        ('  RIZ   blanc  ', 'riz blanc'),
        ("pâte d'arachide", 'pate d arachide'),
        ('', ''),
    ])
    def test_normalise(self, entree, attendu):
        assert normaliser(entree) == attendu

    def test_parser_delegue_la_meme_normalisation(self, seeded_db):
        from api.core.menu_parser import WestAfricanMenuParser

        parser = WestAfricanMenuParser(seeded_db)
        assert parser._normalize('Thiéboudienne') == normaliser('Thiéboudienne')


class TestResolveur:

    def test_nom_exact(self, seeded_db):
        items, non_resolus = resoudre([{'name': 'riz blanc'}], seeded_db)

        assert non_resolus == []
        assert [i['ingredient_id'] for i in items] == ['i1']
        assert items[0]['confidence'] == 1.0

    def test_accents_et_casse_ignores(self, seeded_db):
        items, non_resolus = resoudre([{'name': 'RIZ BLANC'}], seeded_db)

        assert non_resolus == []
        assert items[0]['ingredient_id'] == 'i1'

    def test_accents_seuls_restent_une_correspondance_exacte(self, seeded_db):
        # La normalisation retire les diacritiques : ce n'est pas de l'approchant
        items, _ = resoudre([{'name': "pate d'arachide"}], seeded_db)

        assert items[0]['ingredient_id'] == 'i2'
        assert items[0]['confidence'] == 1.0

    def test_faute_de_frappe_acceptee_avec_confiance_moindre(self, seeded_db):
        items, non_resolus = resoudre([{'name': "pate d'arachid"}], seeded_db)

        assert non_resolus == []
        assert items[0]['ingredient_id'] == 'i2'
        assert items[0]['confidence'] < 1.0

    def test_inconnu_signale_plutot_qu_ignore(self, seeded_db):
        items, non_resolus = resoudre(
            [{'name': 'riz blanc'}, {'name': 'zzzzzz'}], seeded_db)

        assert non_resolus == ['zzzzzz']
        assert len(items) == 1

    def test_meme_ingredient_cite_deux_fois_ne_compte_qu_une(self, seeded_db):
        items, _ = resoudre(
            [{'name': 'riz blanc'}, {'name': 'Riz blanc'}], seeded_db)

        assert len(items) == 1

    def test_quantite_et_unite_conservees(self, seeded_db):
        items, _ = resoudre(
            [{'name': 'riz blanc', 'quantity': 200, 'unit': 'g'}], seeded_db)

        assert items[0]['quantity'] == 200
        assert items[0]['unit'] == 'g'

    def test_unite_absente_vaut_unite(self, seeded_db):
        items, _ = resoudre([{'name': 'riz blanc'}], seeded_db)

        assert items[0]['unit'] == 'unité'


class TestConversionUnites:
    """Une unité de mesure absente de la table tombait dans le fallback
    « x 100 » : 30 ml d'huile pesaient 3 kg et le plat affichait 4200 kcal."""

    class _Aliment:
        local_name = 'Huile végétale'

    @pytest.mark.parametrize('quantite, unite, attendu', [
        (30, 'ml', 30),
        (30, 'millilitre', 30),
        (1, 'l', 1000),
        (25, 'cl', 250),
        (2, 'kg', 2000),
        (500, 'mg', 0.5),
        (200, 'g', 200),
    ])
    def test_unites_de_mesure(self, quantite, unite, attendu):
        assert _convert_to_grams(quantite, unite, self._Aliment()) == attendu

    def test_unite_de_decompte_reste_une_estimation(self):
        # "2 oignons" : le fallback reste volontaire pour les objets comptés
        assert _convert_to_grams(2, 'oignon', self._Aliment()) == 200


class TestRouteAnalyzeIngredients:

    def test_analyse_nominale(self, client, seeded_db):
        response = client.post('/api/analyze-ingredients', json={
            'dish_name': 'Riz simple',
            'ingredients': [{'name': 'riz blanc', 'quantity': 200, 'unit': 'g'}],
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Riz simple'
        assert 0 <= data['score'] <= 100
        assert data['matched_ingredients'] == ['riz blanc']
        assert data['unmatched_ingredients'] == []

    def test_ingredients_inconnus_remontes(self, client, seeded_db):
        response = client.post('/api/analyze-ingredients', json={
            'ingredients': [
                {'name': 'riz blanc'},
                {'name': 'ingrédient imaginaire'},
            ],
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 200
        assert response.json()['unmatched_ingredients'] == ['ingrédient imaginaire']

    def test_aucun_ingredient_reconnu_refuse(self, client, seeded_db):
        response = client.post('/api/analyze-ingredients', json={
            'ingredients': [{'name': 'zzzzzz'}],
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 422
        assert 'zzzzzz' in response.json()['detail']

    def test_liste_vide_refusee(self, client, seeded_db):
        response = client.post('/api/analyze-ingredients',
                               json={'ingredients': []})

        assert response.status_code == 422

    def test_nom_de_plat_optionnel(self, client, seeded_db):
        response = client.post('/api/analyze-ingredients', json={
            'ingredients': [{'name': 'riz blanc'}],
            'health_profile': {'diseases': [], 'allergens': [], 'weight': 70},
        })

        assert response.status_code == 200
        assert response.json()['name'] == 'Plat décrit'

    def test_profil_utilisateur_pris_en_compte(self, client, seeded_db):
        """Un allergène du profil doit ressortir en alerte."""
        response = client.post('/api/analyze-ingredients', json={
            'ingredients': [{'name': "pâte d'arachide", 'quantity': 100, 'unit': 'g'}],
            'health_profile': {'diseases': [], 'allergens': ['Arachide'], 'weight': 70},
        })

        assert response.status_code == 200
        alertes = response.json()['allergen_alerts']
        assert any('arachide' in a['name'].lower() for a in alertes)
