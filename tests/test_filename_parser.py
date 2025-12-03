"""Tests für den FilenameParser."""
import pytest

from skriptendruck.models import BindingType, ColorMode
from skriptendruck.services import FilenameParser


class TestFilenameParser:
    """Tests für den FilenameParser."""
    
    def setup_method(self) -> None:
        """Setup für jeden Test."""
        self.parser = FilenameParser()
    
    def test_parse_complete_filename_with_rz(self) -> None:
        """Test: Vollständiger Dateiname mit RZ-Kennung."""
        filename = "mus43225_sw_mb_001.pdf"
        
        username, name, color, binding, seq = self.parser.parse(filename)
        
        assert username == "mus43225"
        assert name is None
        assert color == ColorMode.BLACK_WHITE
        assert binding == BindingType.SMALL
        assert seq == 1
    
    def test_parse_color_variations(self) -> None:
        """Test: Verschiedene Schreibweisen für Farbe."""
        filenames = [
            "mus43225_farbig_mb_001.pdf",
            "mus43225_farbe_mb_001.pdf",
            "mus43225_color_mb_001.pdf",
        ]
        
        for filename in filenames:
            _, _, color, _, _ = self.parser.parse(filename)
            assert color == ColorMode.COLOR, f"Failed for {filename}"
    
    def test_parse_binding_variations(self) -> None:
        """Test: Verschiedene Schreibweisen für Bindung."""
        # Mit Bindung
        with_binding = [
            "mus43225_sw_mb_001.pdf",
            "mus43225_sw_mitBindung_001.pdf",
            "mus43225_sw_mit_Bindung_001.pdf",
            "mus43225_sw_binden_001.pdf",
        ]
        
        for filename in with_binding:
            _, _, _, binding, _ = self.parser.parse(filename)
            assert binding == BindingType.SMALL, f"Failed for {filename}"
        
        # Ohne Bindung
        without_binding = [
            "mus43225_sw_ob_001.pdf",
            "mus43225_sw_ohneBindung_001.pdf",
            "mus43225_sw_ungebunden_001.pdf",
        ]
        
        for filename in without_binding:
            _, _, _, binding, _ = self.parser.parse(filename)
            assert binding == BindingType.NONE, f"Failed for {filename}"
        
        # Schnellhefter
        folder = ["mus43225_sw_sh_001.pdf", "mus43225_sw_Schnellhefter_001.pdf"]
        
        for filename in folder:
            _, _, _, binding, _ = self.parser.parse(filename)
            assert binding == BindingType.FOLDER, f"Failed for {filename}"
    
    def test_parse_without_sequence_number(self) -> None:
        """Test: Dateiname ohne Laufnummer."""
        filename = "mus43225_sw_mb.pdf"
        
        username, _, _, _, seq = self.parser.parse(filename)
        
        assert username == "mus43225"
        assert seq is None
    
    def test_parse_with_name_instead_of_rz(self) -> None:
        """Test: Dateiname mit Name statt RZ-Kennung."""
        filename = "mueller_sw_mb_001.pdf"
        
        username, name, color, _, _ = self.parser.parse(filename)
        
        assert username is None
        assert name == "mueller"
        assert color == ColorMode.BLACK_WHITE
    
    def test_parse_nickname_mapping(self) -> None:
        """Test: Nickname-Mapping funktioniert."""
        filename = "max_sw_mb_001.pdf"
        
        _, name, _, _, _ = self.parser.parse(filename)
        
        assert name == "maximilian"
    
    def test_extract_sequence_number(self) -> None:
        """Test: Laufnummer wird korrekt extrahiert."""
        test_cases = [
            ("mus43225_sw_mb_001.pdf", 1),
            ("mus43225_sw_mb_042.pdf", 42),
            ("mus43225_sw_mb_999.pdf", 999),
            ("mus43225_sw_mb.pdf", None),
        ]
        
        for filename, expected in test_cases:
            _, _, _, _, seq = self.parser.parse(filename)
            assert seq == expected, f"Failed for {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
