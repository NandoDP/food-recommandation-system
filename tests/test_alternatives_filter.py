"""
Tests de non-régression : le filtre allergènes de /alternatives

Un allergène du profil est une contre-indication absolue : une alternative qui
en contient ne doit jamais être proposée, même si son score dépasse celui du
plat d'origine.
"""
import pytest

from api.core.nutrition_engine import NutritionEngine
from api.models.analyze import AlertLevel
from api.routes.analyze import _has_blocking_alert


@pytest.fixture
def engine():
    return NutritionEngine()


@pytest.fixture
def peanut_allergic_profile():
    return {
        'allergens': ['Arachides'],
        'diseases': ['Diabète Type 2'],
        'weight': 70
    }


class TestHasBlockingAlert:
    """Tests unitaires du helper de détection d'alerte bloquante"""

    def test_empty_alerts(self):
        assert _has_blocking_alert([]) is False

    def test_none_alerts(self):
        assert _has_blocking_alert(None) is False

    def test_safe_and_caution_are_not_blocking(self):
        alerts = [
            {'name': 'X', 'level': AlertLevel.SAFE.value, 'message': ''},
            {'name': 'Y', 'level': AlertLevel.CAUTION.value, 'message': ''},
        ]
        assert _has_blocking_alert(alerts) is False

    @pytest.mark.parametrize('level', [AlertLevel.DANGER, AlertLevel.CRITICAL])
    def test_danger_and_critical_are_blocking(self, level):
        # Le moteur stocke la valeur str ; AlertLevel hérite de str, les deux
        # formes doivent être reconnues.
        assert _has_blocking_alert([{'name': 'X', 'level': level.value}]) is True
        assert _has_blocking_alert([{'name': 'X', 'level': level}]) is True


class TestAllergenNeverProposed:
    """Le scénario de régression : meilleur score mais allergène présent"""

    def test_better_scoring_alternative_with_allergen_is_rejected(
        self, engine, peanut_allergic_profile
    ):
        original = engine.analyze(
            {
                'name': 'Mafé cacahuète',
                'ingredients': [{'name': "pâte d'arachide"}, {'name': 'riz blanc'}],
                'nutritional_summary': {
                    'glycemic_index': 75, 'carbohydrate_g': 80, 'fiber_g': 2,
                    'sodium_mg': 900, 'energy_kcal': 700, 'protein_g': 20, 'fat_g': 30
                },
            },
            peanut_allergic_profile,
        )

        alternative = engine.analyze(
            {
                'name': "Salade d'arachides grillées",
                'ingredients': [{'name': 'arachide'}, {'name': 'légumes verts'}],
                'nutritional_summary': {
                    'glycemic_index': 35, 'carbohydrate_g': 30, 'fiber_g': 9,
                    'sodium_mg': 200, 'energy_kcal': 400, 'protein_g': 18, 'fat_g': 15
                },
            },
            peanut_allergic_profile,
        )

        # Le scénario n'a de sens que si l'ancien critère seul l'aurait retenue
        assert alternative['score'] > original['score']
        assert _has_blocking_alert(alternative['allergen_alerts']) is True

        retained = (
            not _has_blocking_alert(alternative['allergen_alerts'])
            and alternative['score'] > original['score']
        )
        assert retained is False

    def test_allergen_free_alternative_is_still_proposed(
        self, engine, peanut_allergic_profile
    ):
        """Le filtre ne doit pas écarter les alternatives saines"""
        original = engine.analyze(
            {
                'name': 'Mafé cacahuète',
                'ingredients': [{'name': "pâte d'arachide"}, {'name': 'riz blanc'}],
                'nutritional_summary': {
                    'glycemic_index': 75, 'carbohydrate_g': 80, 'fiber_g': 2,
                    'sodium_mg': 900, 'energy_kcal': 700, 'protein_g': 20, 'fat_g': 30
                },
            },
            peanut_allergic_profile,
        )

        alternative = engine.analyze(
            {
                'name': 'Thiébou yapp légumes',
                'ingredients': [{'name': 'légumes verts'}, {'name': 'riz complet'}],
                'nutritional_summary': {
                    'glycemic_index': 40, 'carbohydrate_g': 45, 'fiber_g': 8,
                    'sodium_mg': 300, 'energy_kcal': 500, 'protein_g': 25, 'fat_g': 12
                },
            },
            peanut_allergic_profile,
        )

        assert _has_blocking_alert(alternative['allergen_alerts']) is False
        assert alternative['score'] > original['score']
