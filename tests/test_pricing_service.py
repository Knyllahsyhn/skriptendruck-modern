"""Tests für den PricingService."""
import pytest

from skriptendruck.models import BindingType, ColorMode
from skriptendruck.services import PricingService


class TestPricingService:
    """Tests für den PricingService."""
    
    def setup_method(self) -> None:
        """Setup für jeden Test."""
        self.service = PricingService()
    
    def test_calculate_price_black_white_no_binding(self) -> None:
        """Test: Preisberechnung Schwarz-Weiß ohne Bindung."""
        calc = self.service.calculate_price(
            pages=100,
            color_mode=ColorMode.BLACK_WHITE,
            binding_type=BindingType.NONE,
        )
        
        assert calc.pages == 100
        assert calc.pages_price == 4.0  # 100 * 0.04
        assert calc.binding_price == 0.0
        assert calc.total_price == 4.0
    
    def test_calculate_price_color_with_binding(self) -> None:
        """Test: Preisberechnung Farbe mit Bindung."""
        calc = self.service.calculate_price(
            pages=200,
            color_mode=ColorMode.COLOR,
            binding_type=BindingType.SMALL,
        )
        
        assert calc.pages == 200
        assert calc.pages_price == 20.0  # 200 * 0.10
        assert calc.binding_price == 1.0  # Kleine Bindung
        assert calc.total_price == 21.0
    
    def test_calculate_price_with_folder(self) -> None:
        """Test: Preisberechnung mit Schnellhefter."""
        calc = self.service.calculate_price(
            pages=50,
            color_mode=ColorMode.BLACK_WHITE,
            binding_type=BindingType.FOLDER,
        )
        
        assert calc.binding_price == 0.5  # Schnellhefter
        assert calc.total_price == 2.5  # 50*0.04 + 0.5
    
    def test_price_after_deposit(self) -> None:
        """Test: Preis nach Abzug der Anzahlung."""
        calc = self.service.calculate_price(
            pages=100,
            color_mode=ColorMode.BLACK_WHITE,
            binding_type=BindingType.SMALL,
        )
        
        # Total: 4.0 (Seiten) + 1.0 (Bindung) = 5.0
        # Nach Anzahlung: 5.0 - 1.0 = 4.0
        assert calc.total_price == 5.0
        assert calc.price_after_deposit == 4.0
    
    def test_validate_page_count_too_few(self) -> None:
        """Test: Validierung - zu wenig Seiten."""
        is_valid, error = self.service.validate_page_count(0, BindingType.NONE)
        
        assert not is_valid
        assert "wenig" in error.lower()
    
    def test_validate_page_count_too_many(self) -> None:
        """Test: Validierung - zu viele Seiten für Bindung."""
        is_valid, error = self.service.validate_page_count(700, BindingType.SMALL)
        
        assert not is_valid
        assert "viele" in error.lower() or "max" in error.lower()
    
    def test_validate_page_count_valid(self) -> None:
        """Test: Validierung - gültige Seitenzahl."""
        is_valid, error = self.service.validate_page_count(200, BindingType.SMALL)
        
        assert is_valid
        assert error is None
    
    def test_formatted_prices(self) -> None:
        """Test: Formatierte Preise haben deutsches Format."""
        calc = self.service.calculate_price(
            pages=100,
            color_mode=ColorMode.BLACK_WHITE,
            binding_type=BindingType.SMALL,
        )
        
        # Deutsches Format mit Komma
        assert "," in calc.total_price_formatted
        assert "€" in calc.total_price_formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
