"""
Tests unitaires pour le moteur de règles nutritionnelles

Contrat réel de `NutritionEngine.analyze(dish_data, health_profile)` :
  dish_data      = {'name': str, 'ingredients': [{'name': str}],
                    'nutritional_summary': {...}}
  health_profile = {'diseases': [str], 'allergens': [str], 'weight': float}

Les maladies et allergènes sont des libellés (`DiseaseType.*.value`, clés de
`allergen_keywords`), pas des dicts.
"""
import pytest

from api.core.nutrition_engine import NutritionEngine
from api.models.analyze import AlertLevel, DiseaseType


def dish(name="Plat test", ingredients=None, **nutrition):
    """Construit un dish_data au format attendu par le moteur."""
    summary = {
        'energy_kcal': 250,
        'protein_g': 15,
        'fat_g': 8,
        'carbohydrate_g': 30,
        'fiber_g': 5,
        'sodium_mg': 400,
        'potassium_mg': 600,
        'glycemic_index': 55,
    }
    summary.update(nutrition)
    return {
        'name': name,
        'ingredients': [{'name': i} for i in (ingredients or [])],
        'nutritional_summary': summary,
    }


def profile(diseases=None, allergens=None, weight=70):
    return {
        'diseases': diseases or [],
        'allergens': allergens or [],
        'weight': weight,
    }


@pytest.fixture
def engine():
    return NutritionEngine()


class TestStructureDuResultat:
    """Le moteur retourne toujours la même structure"""

    def test_cles_attendues(self, engine):
        result = engine.analyze(dish(), profile())

        for key in ('name', 'score', 'alert_level', 'allergen_alerts',
                    'disease_alerts', 'recommendations', 'alternatives',
                    'nutritional_summary', 'detailed_breakdown'):
            assert key in result

    def test_score_dans_les_bornes(self, engine):
        result = engine.analyze(dish(), profile(diseases=[DiseaseType.DIABETES.value]))
        assert 0 <= result['score'] <= 100

    def test_detail_des_trois_composantes(self, engine):
        result = engine.analyze(dish(), profile())
        breakdown = result['detailed_breakdown']

        assert set(breakdown) == {'allergen_score', 'disease_score', 'nutrition_score'}

    def test_profil_sain_reste_safe(self, engine):
        result = engine.analyze(dish(), profile())

        assert result['alert_level'] == AlertLevel.SAFE
        assert result['allergen_alerts'] == []
        assert result['disease_alerts'] == []


class TestNiveauxDAlerte:
    """Seuils de `_get_alert_level` : 75 / 50 / 25"""

    @pytest.mark.parametrize('score,expected', [
        (100, AlertLevel.SAFE),
        (75, AlertLevel.SAFE),
        (74, AlertLevel.CAUTION),
        (50, AlertLevel.CAUTION),
        (49, AlertLevel.DANGER),
        (25, AlertLevel.DANGER),
        (24, AlertLevel.CRITICAL),
        (0, AlertLevel.CRITICAL),
    ])
    def test_seuils(self, engine, score, expected):
        assert engine._get_alert_level(score) == expected

    def test_coherence_score_niveau(self, engine):
        result = engine.analyze(
            dish(name="Plat lourd", glycemic_index=85, carbohydrate_g=80),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )
        assert result['alert_level'] == engine._get_alert_level(result['score'])


class TestDiabete:
    def test_ig_eleve_declenche_alerte_danger(self, engine):
        result = engine.analyze(
            dish(glycemic_index=85),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )

        alerts = result['disease_alerts']
        assert any(a['level'] == AlertLevel.DANGER.value for a in alerts)
        assert any('IG' in a['message'] for a in alerts)

    def test_ig_bas_ne_penalise_pas(self, engine):
        result = engine.analyze(
            dish(glycemic_index=40, carbohydrate_g=25, fiber_g=6),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )

        assert result['detailed_breakdown']['disease_score'] == 100
        assert result['disease_alerts'] == []

    def test_glucides_excessifs(self, engine):
        result = engine.analyze(
            dish(carbohydrate_g=80, glycemic_index=40, fiber_g=6),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )

        assert any('Glucides excessifs' in a['message'] for a in result['disease_alerts'])

    def test_fibres_insuffisantes_generent_une_recommandation(self, engine):
        result = engine.analyze(
            dish(fiber_g=1, glycemic_index=40, carbohydrate_g=25),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )

        assert any('fibres' in r.lower() for r in result['recommendations'])

    def test_mot_cle_interdit_dans_le_nom(self, engine):
        result = engine.analyze(
            dish(name="Riz blanc sauté", glycemic_index=40, carbohydrate_g=25, fiber_g=6),
            profile(diseases=[DiseaseType.DIABETES.value]),
        )

        assert any('riz blanc' in a['message'] for a in result['disease_alerts'])


class TestHypertension:
    def test_sodium_excessif(self, engine):
        result = engine.analyze(
            dish(sodium_mg=1200),
            profile(diseases=[DiseaseType.HYPERTENSION.value]),
        )

        alerts = result['disease_alerts']
        assert any('Sodium excessif' in a['message'] for a in alerts)
        assert any(a['level'] == AlertLevel.DANGER.value for a in alerts)

    def test_sodium_modere_declenche_caution(self, engine):
        # entre 75 % et 100 % du plafond par repas (667 mg)
        result = engine.analyze(
            dish(sodium_mg=600),
            profile(diseases=[DiseaseType.HYPERTENSION.value]),
        )

        assert any(a['level'] == AlertLevel.CAUTION.value
                   for a in result['disease_alerts'])

    def test_sodium_bas_sans_alerte(self, engine):
        result = engine.analyze(
            dish(sodium_mg=200),
            profile(diseases=[DiseaseType.HYPERTENSION.value]),
        )

        assert result['disease_alerts'] == []
        assert result['detailed_breakdown']['disease_score'] == 100


class TestInsuffisanceRenale:
    """Régression : ces règles étaient inertes (mauvais argument transmis)"""

    def test_potassium_excessif_detecte(self, engine):
        result = engine.analyze(
            dish(potassium_mg=1500),
            profile(diseases=[DiseaseType.KIDNEY_DISEASE.value]),
        )

        assert any('Potassium excessif' in a['message']
                   for a in result['disease_alerts'])
        assert result['detailed_breakdown']['disease_score'] < 100

    def test_potassium_normal_sans_alerte(self, engine):
        result = engine.analyze(
            dish(potassium_mg=400, sodium_mg=300),
            profile(diseases=[DiseaseType.KIDNEY_DISEASE.value]),
        )

        assert result['disease_alerts'] == []


class TestMaladieHepatique:
    """Régression : ces règles étaient inertes (mauvais argument transmis)"""

    def test_sodium_excessif_detecte(self, engine):
        result = engine.analyze(
            dish(sodium_mg=900, protein_g=5),
            profile(diseases=[DiseaseType.LIVER_DISEASE.value]),
        )

        assert any('Sodium excessif' in a['message']
                   for a in result['disease_alerts'])

    def test_proteines_excessives_recommandation(self, engine):
        # plafond = poids * 1.0 / 3 repas ; 40 g > 70/3
        result = engine.analyze(
            dish(sodium_mg=200, protein_g=40),
            profile(diseases=[DiseaseType.LIVER_DISEASE.value], weight=70),
        )

        assert any('Protéines' in r for r in result['recommendations'])


class TestAllergenes:
    def test_detection_via_ingredient(self, engine):
        result = engine.analyze(
            dish(ingredients=["pâte d'arachide", "riz"]),
            profile(allergens=['Arachides']),
        )

        assert len(result['allergen_alerts']) == 1
        alert = result['allergen_alerts'][0]
        assert alert['name'] == 'Arachides'
        assert alert['level'] == AlertLevel.CRITICAL.value

    def test_detection_via_nom_du_plat(self, engine):
        result = engine.analyze(
            dish(name="Salade de crevettes"),
            profile(allergens=['Crustacés']),
        )

        assert [a['name'] for a in result['allergen_alerts']] == ['Crustacés']

    def test_allergene_met_la_composante_a_zero(self, engine):
        result = engine.analyze(
            dish(ingredients=["arachide"]),
            profile(allergens=['Arachides']),
        )

        assert result['detailed_breakdown']['allergen_score'] == 0
        # la composante allergène pèse 40 % : le score plafonne donc à 60
        assert result['score'] <= 60

    def test_sans_allergene_au_profil_aucune_alerte(self, engine):
        result = engine.analyze(
            dish(ingredients=["arachide"]),
            profile(allergens=[]),
        )

        assert result['allergen_alerts'] == []
        assert result['detailed_breakdown']['allergen_score'] == 100

    def test_allergene_absent_du_plat(self, engine):
        result = engine.analyze(
            dish(ingredients=["riz", "tomate"]),
            profile(allergens=['Arachides']),
        )

        assert result['allergen_alerts'] == []


class TestMaladiesMultiples:
    def test_score_est_la_moyenne_des_maladies(self, engine):
        data = dish(glycemic_index=85, sodium_mg=1200)
        combined = engine.analyze(
            data,
            profile(diseases=[DiseaseType.DIABETES.value,
                              DiseaseType.HYPERTENSION.value]),
        )

        diabetes_only = engine.analyze(
            data, profile(diseases=[DiseaseType.DIABETES.value]))
        hypertension_only = engine.analyze(
            data, profile(diseases=[DiseaseType.HYPERTENSION.value]))

        expected = (diabetes_only['detailed_breakdown']['disease_score']
                    + hypertension_only['detailed_breakdown']['disease_score']) / 2

        assert combined['detailed_breakdown']['disease_score'] == pytest.approx(expected)

    def test_les_deux_maladies_sont_signalees(self, engine):
        result = engine.analyze(
            dish(glycemic_index=85, sodium_mg=1200),
            profile(diseases=[DiseaseType.DIABETES.value,
                              DiseaseType.HYPERTENSION.value]),
        )

        names = {a['name'] for a in result['disease_alerts']}
        assert {'Diabète', 'Hypertension'} <= names


class TestEquilibreNutritionnel:
    def test_donnees_absentes_donnent_un_score_neutre(self, engine):
        result = engine.analyze(
            {'name': 'Inconnu', 'ingredients': [], 'nutritional_summary': {}},
            profile(),
        )

        assert result['detailed_breakdown']['nutrition_score'] == 50.0

    def test_exces_de_lipides_penalise(self, engine):
        result = engine.analyze(
            dish(protein_g=5, fat_g=40, carbohydrate_g=10),
            profile(),
        )

        assert result['detailed_breakdown']['nutrition_score'] < 100
        assert any('grasses' in r.lower() for r in result['recommendations'])
