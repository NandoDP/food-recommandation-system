"""
Tests unitaires pour le parser de menus

`WestAfricanMenuParser` prend une session SQLAlchemy et charge les ingrédients
au démarrage : les tests utilisent la base SQLite de `conftest.py`. La méthode
publique est `parse_menu_text`, qui renvoie une liste de dicts
`{ingredient_id, quantity, unit, raw_text, confidence}`.
"""
import pytest

from api.core.menu_parser import WestAfricanMenuParser
from api.schemas.analyze import Ingredient


@pytest.fixture
def parser(db_session):
    """Parser alimenté par quelques ingrédients sénégalais."""
    db_session.add_all([
        Ingredient(id="p1", name="riz"),
        Ingredient(id="p2", name="poisson"),
        Ingredient(id="p3", name="arachide"),
        Ingredient(id="p4", name="tomate"),
    ])
    db_session.commit()
    return WestAfricanMenuParser(db_session)


@pytest.fixture
def empty_parser(db_session):
    """Parser sur une base sans aucun ingrédient (base fraîche)."""
    return WestAfricanMenuParser(db_session)


class TestParsingNominal:
    def test_ingredient_simple_reconnu(self, parser):
        result = parser.parse_menu_text("riz")

        assert [r['ingredient_id'] for r in result] == ["p1"]
        assert result[0]['confidence'] == 1.0

    def test_plusieurs_ingredients(self, parser):
        result = parser.parse_menu_text("riz au poisson et tomate")

        assert {r['ingredient_id'] for r in result} >= {"p1", "p2", "p4"}

    def test_resultat_toujours_une_liste_de_dicts(self, parser):
        result = parser.parse_menu_text("riz")

        assert isinstance(result, list)
        for item in result:
            assert set(item) == {'ingredient_id', 'quantity', 'unit',
                                 'raw_text', 'confidence'}

    def test_ingredient_inconnu_ignore(self, parser):
        result = parser.parse_menu_text("pizza quatre fromages")

        assert all(r['ingredient_id'] in {"p1", "p2", "p3", "p4"} for r in result)


class TestQuantites:
    def test_extraction_grammes(self, parser):
        result = parser.parse_menu_text("200g de riz")

        riz = next(r for r in result if r['ingredient_id'] == "p1")
        assert riz['quantity'] == 200.0
        assert riz['unit'] == "g"

    def test_unite_par_defaut_sans_quantite(self, parser):
        result = parser.parse_menu_text("riz")

        assert result[0]['quantity'] is None
        assert result[0]['unit'] == "unité"

    def test_quantite_en_lettres(self, parser):
        result = parser.parse_menu_text("deux verres de riz")

        riz = next(r for r in result if r['ingredient_id'] == "p1")
        assert riz['quantity'] == 2.0


class TestCasLimites:
    def test_texte_vide(self, parser):
        assert parser.parse_menu_text("") == []

    def test_texte_uniquement_espaces(self, parser):
        assert parser.parse_menu_text("   \n  ") == []

    def test_caracteres_speciaux(self, parser):
        result = parser.parse_menu_text("Thiéboudienne (poisson), riz & tomate")

        assert {r['ingredient_id'] for r in result} >= {"p2", "p4"}

    def test_ingredient_accentue_reconnu(self, parser, db_session):
        """Régression : les motifs normalisés étaient comparés au texte brut,
        donc aucun ingrédient accentué ne pouvait correspondre."""
        db_session.add(Ingredient(id="p5", name="pâte d'arachide"))
        db_session.commit()
        accented = WestAfricanMenuParser(db_session)

        result = accented.parse_menu_text("Mafé à la pâte d'arachide")

        assert "p5" in {r['ingredient_id'] for r in result}

    def test_base_sans_ingredient_ne_leve_pas(self, empty_parser):
        """Régression : `extractOne` renvoyait None sur un index vide."""
        assert empty_parser.parse_menu_text("riz au poisson") == []

    def test_ingredient_sans_aliases_ne_leve_pas(self, parser):
        """Régression : `get_aliases()` n'existe pas sur le modèle Ingredient."""
        assert parser.parse_menu_text("riz") != []


class TestNormalisation:
    def test_accents_et_casse_ignores(self, parser):
        assert parser._normalize("RIZ Blanc") == "riz blanc"

    def test_diacritiques_retires_sans_couper_le_mot(self, parser):
        """Régression : NFKD laissait un diacritique que la regex de
        ponctuation transformait en espace ("thie boudienne")."""
        assert parser._normalize("Thiéboudienne") == "thieboudienne"
        assert parser._normalize("légume") == "legume"
        assert parser._normalize("pâte") == "pate"

    def test_ponctuation_remplacee_par_espace(self, parser):
        assert parser._normalize("riz, poisson") == "riz poisson"

    def test_texte_vide_normalise(self, parser):
        assert parser._normalize("") == ""
        assert parser._normalize(None) == ""


class TestAliases:
    def test_aliases_via_attribut_liste(self, parser):
        ing = Ingredient(id="x", name="cube maggi")
        ing.aliases = ["jumbo", "bouillon cube"]

        assert parser._get_aliases(ing) == ["jumbo", "bouillon cube"]

    def test_aliases_via_colonne_json(self, parser):
        ing = Ingredient(id="x", name="cube maggi")
        ing.aliases = '["jumbo", "bouillon cube"]'

        assert parser._get_aliases(ing) == ["jumbo", "bouillon cube"]

    def test_aliases_absents(self, parser):
        assert parser._get_aliases(Ingredient(id="x", name="riz")) == []

    def test_json_invalide_ignore(self, parser):
        ing = Ingredient(id="x", name="riz")
        ing.aliases = "pas du json"

        assert parser._get_aliases(ing) == []
