"""Service zum Parsen von Dateinamen."""
import re
from typing import Optional, Tuple

from ..config import get_logger
from ..models import BindingType, ColorMode

logger = get_logger("filename_parser")


class FilenameParser:
    """Parst Dateinamen nach dem Schema: username_colormode_bindingtype_number.pdf"""
    
    # Variationen für Schwarz-Weiß
    SW_PATTERNS = [
        "sw", "schwarzweiß", "schwarzweiss", "schwarz-weiß", "schwarz-weiss",
        "schwarz - weiss", "s_and_w", "schwarz-weis", "schwarz weiß",
        "schwarz weiss", "schwarz weis", "schwarz - weiß",
        "schwartzweiß", "schwartzweiss", "schwartz-weiß", "schwartz-weiss",
        "schwarz - weis", "schwartz-weis", "schwartz weiß", "schwartz weiss",
        "schwartz weis", "schwartz - weis"
    ]
    
    # Variationen für Farbe
    COLOR_PATTERNS = ["farbig", "farbe", "color"]
    
    # Variationen für "mit Bindung"
    WITH_BINDING_PATTERNS = [
        "mb", "mit bindung", "mitbindung", "mit_bindung", "m.bindung",
        "binden", "mit_bdg", "gerringt", "mit bidung", "mitbidung",
        "mit_bidung", "m.bidung", "mitbund", "mit bund", "mit_brindung",
        "bindung", "gebunden"
    ]
    
    # Variationen für "ohne Bindung"
    WITHOUT_BINDING_PATTERNS = [
        "ob", "ohne bindung", "ohnebindung", "ohne_bindung", "ungebunden",
        "o.bindung", "ohne bidung", "ohnebidung", "ohne_bidung", "o.bidung"
    ]
    
    # Variationen für "Schnellhefter"
    FOLDER_PATTERNS = ["sh", "schnellhefter"]
    
    # Nicknamen-Mapping (kann erweitert werden)
    NICKNAME_MAP = {
        "alex": "alexander",
        "chris": "christian",
        "max": "maximilian",
        "maxi": "maximilian",  # oder maximiliane
        "mike": "michael",
        "domi": "dominik",
        "matze": "matthias",
        "isa": "isabel",
        "isi": "isabel",
        "kati": "katharina",
    }
    
    def __init__(self) -> None:
        """Initialisiert den Parser."""
        # Compile regex patterns für Performance
        self._rz_pattern = re.compile(r"^([a-z]{3}\d{5})", re.IGNORECASE)
        self._number_pattern = re.compile(r"_(\d{3})\.pdf$", re.IGNORECASE)
    
    def parse(self, filename: str) -> Tuple[
        Optional[str],  # username/rz-kennung
        Optional[str],  # parsed_name
        Optional[ColorMode],  # color_mode
        Optional[BindingType],  # binding_type
        Optional[int],  # sequence_number
    ]:
        """
        Parst einen Dateinamen.
        
        Args:
            filename: Dateiname (z.B. "mus43225_sw_mb_001.pdf")
            
        Returns:
            Tuple mit (username, name, color_mode, binding_type, sequence_number)
        """
        logger.debug(f"Parsing filename: {filename}")
        
        # Dateiname normalisieren
        normalized = filename.lower().replace(".pdf", "")
        parts = normalized.split("_")
        
        username = None
        parsed_name = None
        color_mode = None
        binding_type = None
        sequence_number = None
        
        # 1. Username/RZ-Kennung extrahieren
        username = self._extract_username(parts[0] if parts else "")
        
        # 2. Name extrahieren (falls vorhanden statt RZ-Kennung)
        if not username and parts:
            parsed_name = self._extract_name(parts[0])
        
        # 3. Restliche Teile analysieren
        rest_parts = "_".join(parts[1:]) if len(parts) > 1 else ""
        
        # 4. Color Mode bestimmen
        color_mode = self._extract_color_mode(rest_parts)
        
        # 5. Binding Type bestimmen
        binding_type = self._extract_binding_type(rest_parts)
        
        # 6. Laufnummer extrahieren
        sequence_number = self._extract_sequence_number(filename)
        
        logger.debug(
            f"Parsed result: username={username}, name={parsed_name}, "
            f"color={color_mode}, binding={binding_type}, seq={sequence_number}"
        )
        
        return username, parsed_name, color_mode, binding_type, sequence_number
    
    def _extract_username(self, first_part: str) -> Optional[str]:
        """
        Extrahiert RZ-Kennung (Format: abc12345).
        
        Args:
            first_part: Erster Teil des Dateinamens
            
        Returns:
            RZ-Kennung oder None
        """
        match = self._rz_pattern.match(first_part)
        if match:
            return match.group(1).lower()
        return None
    
    def _extract_name(self, first_part: str) -> Optional[str]:
        """
        Extrahiert einen Namen aus dem ersten Teil.
        
        Args:
            first_part: Erster Teil des Dateinamens
            
        Returns:
            Name oder None
        """
        # Entfernt Zahlen und Sonderzeichen
        name = re.sub(r"[^a-zäöüß]", "", first_part.lower())
        
        # Nickname-Mapping anwenden
        if name in self.NICKNAME_MAP:
            name = self.NICKNAME_MAP[name]
        
        return name if len(name) > 2 else None
    
    def _extract_color_mode(self, text: str) -> Optional[ColorMode]:
        """
        Bestimmt den Farbmodus aus dem Text.
        
        Args:
            text: Text zum Durchsuchen
            
        Returns:
            ColorMode oder None
        """
        text_lower = text.lower()
        
        # Schwarz-Weiß prüfen
        for pattern in self.SW_PATTERNS:
            if pattern in text_lower:
                return ColorMode.BLACK_WHITE
        
        # Farbe prüfen
        for pattern in self.COLOR_PATTERNS:
            if pattern in text_lower:
                return ColorMode.COLOR
        
        # Default: Schwarz-Weiß
        return ColorMode.BLACK_WHITE
    
    def _extract_binding_type(self, text: str) -> Optional[BindingType]:
        """
        Bestimmt den Bindungstyp aus dem Text.
        
        Args:
            text: Text zum Durchsuchen
            
        Returns:
            BindingType oder None
        """
        text_lower = text.lower()
        
        # Schnellhefter prüfen (hat Priorität)
        for pattern in self.FOLDER_PATTERNS:
            if pattern in text_lower:
                return BindingType.FOLDER
        
        # Mit Bindung prüfen
        for pattern in self.WITH_BINDING_PATTERNS:
            if pattern in text_lower:
                # Größe wird später durch Seitenzahl bestimmt
                return BindingType.SMALL  # Default, wird später angepasst
        
        # Ohne Bindung prüfen
        for pattern in self.WITHOUT_BINDING_PATTERNS:
            if pattern in text_lower:
                return BindingType.NONE
        
        # Default: Mit Bindung (wie im Original)
        return BindingType.SMALL
    
    def _extract_sequence_number(self, filename: str) -> Optional[int]:
        """
        Extrahiert die laufende Nummer (Format: _001.pdf).
        
        Args:
            filename: Vollständiger Dateiname
            
        Returns:
            Laufnummer oder None
        """
        match = self._number_pattern.search(filename)
        if match:
            return int(match.group(1))
        return None
