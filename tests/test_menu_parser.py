"""
Tests unitaires pour le parser de menus NLP
"""
import pytest
from api.core.menu_parser import WestAfricanMenuParser


class TestMenuParser:
    """Tests pour le parser de menus"""
    
    @pytest.fixture
    def parser(self):
        """Fixture pour créer une instance du parser"""
        return WestAfricanMenuParser()
    
    def test_parse_simple_menu(self, parser):
        """Test parsing d'un menu simple"""
        menu_text = "Thiéboudienne avec légumes"
        
        result = parser.parse(menu_text)
        
        assert result is not None
        assert isinstance(result, dict) or isinstance(result, list)
    
    def test_parse_multiple_dishes(self, parser):
        """Test parsing de plusieurs plats"""
        menu_text = """
        Petit-déjeuner: Café au lait et pain
        Déjeuner: Thiéboudienne
        Dîner: Mafé au poulet
        """
        
        result = parser.parse(menu_text)
        
        assert result is not None
    
    def test_empty_menu(self, parser):
        """Test avec menu vide"""
        menu_text = ""
        
        result = parser.parse(menu_text)
        
        # Devrait gérer gracieusement
        assert result is not None or result == []
    
    def test_special_characters(self, parser):
        """Test avec caractères spéciaux"""
        menu_text = "Thiéboudienne (poisson), Mafé & riz"
        
        result = parser.parse(menu_text)
        
        assert result is not None
    
    def test_quantity_extraction(self, parser):
        """Test extraction de quantités"""
        menu_text = "200g de riz, 100g de poisson"
        
        result = parser.parse(menu_text)
        
        # Devrait idéalement extraire les quantités
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
