"""Service für Preisberechnung und Bindungsgrößen."""
import json
from pathlib import Path
from typing import List, Optional

from ..config import get_logger, settings
from ..models import BindingSize, BindingType, ColorMode, PriceCalculation

logger = get_logger("pricing_service")


class PricingService:
    """Service für Preisberechnung und Bindungsgrößen."""
    
    def __init__(self) -> None:
        """Initialisiert den PricingService."""
        self._binding_sizes: List[BindingSize] = []
        self._load_binding_sizes()
    
    def calculate_price(
        self,
        pages: int,
        color_mode: ColorMode,
        binding_type: BindingType,
    ) -> PriceCalculation:
        """
        Berechnet den Preis für einen Druckauftrag.
        
        Args:
            pages: Anzahl Seiten
            color_mode: Farbmodus
            binding_type: Bindungstyp
            
        Returns:
            PriceCalculation-Objekt
        """
        # Seitenpreis ermitteln
        price_per_page = (
            settings.price_color if color_mode == ColorMode.COLOR
            else settings.price_sw
        )
        
        # Bindungstyp und -größe anpassen
        actual_binding_type = binding_type
        binding_price = 0.0
        binding_size_mm = None
        
        if binding_type in (BindingType.SMALL, BindingType.LARGE):
            # Richtige Bindungsgröße basierend auf Seitenzahl finden
            binding_size = self.get_binding_size_for_pages(pages)
            
            if binding_size:
                actual_binding_type = binding_size.binding_type
                binding_size_mm = binding_size.size_mm
                
                if binding_size.binding_type == BindingType.SMALL:
                    binding_price = settings.price_binding_small
                elif binding_size.binding_type == BindingType.LARGE:
                    binding_price = settings.price_binding_large
            else:
                # Zu viele Seiten für Bindung
                logger.warning(f"No binding size found for {pages} pages")
                actual_binding_type = BindingType.NONE
        
        elif binding_type == BindingType.FOLDER:
            binding_price = settings.price_folder
        
        return PriceCalculation(
            pages=pages,
            color_mode=color_mode,
            binding_type=actual_binding_type,
            price_per_page=price_per_page,
            binding_price=binding_price,
            binding_size_mm=binding_size_mm,
        )
    
    def get_binding_size_for_pages(self, pages: int) -> Optional[BindingSize]:
        """
        Findet die passende Bindungsgröße für eine Seitenzahl.
        
        Args:
            pages: Anzahl Seiten
            
        Returns:
            BindingSize oder None wenn keine passende Größe gefunden
        """
        for binding_size in self._binding_sizes:
            if binding_size.supports_pages(pages):
                return binding_size
        return None
    
    def validate_page_count(self, pages: int, binding_type: BindingType) -> tuple[bool, Optional[str]]:
        """
        Validiert die Seitenzahl für den gewünschten Bindungstyp.
        
        Args:
            pages: Anzahl Seiten
            binding_type: Gewünschter Bindungstyp
            
        Returns:
            Tuple (is_valid, error_message)
        """
        # Minimum prüfen
        if pages < settings.min_pages:
            return False, f"Zu wenig Seiten (min. {settings.min_pages})"
        
        # Bei Bindung: Maximum prüfen
        if binding_type in (BindingType.SMALL, BindingType.LARGE):
            if pages > settings.max_pages_large_binding:
                return False, f"Zu viele Seiten für Bindung (max. {settings.max_pages_large_binding})"
        
        return True, None
    
    def _load_binding_sizes(self) -> None:
        """Lädt die Ringbindungsgrößen aus JSON-Datei."""
        binding_file = settings.binding_sizes_path
        
        if not binding_file.exists():
            logger.warning(f"Binding sizes file not found: {binding_file}")
            # Default-Werte verwenden
            self._create_default_binding_sizes()
            return
        
        try:
            with open(binding_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._binding_sizes = [
                BindingSize(**item) for item in data.get("binding_sizes", [])
            ]
            
            # Sortieren nach min_pages
            self._binding_sizes.sort(key=lambda x: x.min_pages)
            
            logger.info(f"Loaded {len(self._binding_sizes)} binding sizes")
            
        except Exception as e:
            logger.error(f"Error loading binding sizes: {e}")
            self._create_default_binding_sizes()
    
    def _create_default_binding_sizes(self) -> None:
        """Erstellt Default-Bindungsgrößen basierend auf dem Original-Code."""
        # Einfache Aufteilung wie im Original
        self._binding_sizes = [
            BindingSize(
                min_pages=1,
                max_pages=settings.max_pages_small_binding,
                size_mm=0,  # Größe unbekannt
                binding_type=BindingType.SMALL
            ),
            BindingSize(
                min_pages=settings.max_pages_small_binding + 1,
                max_pages=settings.max_pages_large_binding,
                size_mm=0,  # Größe unbekannt
                binding_type=BindingType.LARGE
            ),
        ]
        logger.info("Using default binding sizes")
    
    def export_default_binding_sizes_json(self, output_path: Path) -> None:
        """
        Exportiert eine Beispiel-JSON-Datei für Ringbindungsgrößen.
        
        Args:
            output_path: Pfad zur Ausgabedatei
        """
        # Beispiel-Daten erstellen
        example_data = {
            "binding_sizes": [
                {"min_pages": 1, "max_pages": 80, "size_mm": 8, "binding_type": "small"},
                {"min_pages": 81, "max_pages": 120, "size_mm": 10, "binding_type": "small"},
                {"min_pages": 121, "max_pages": 160, "size_mm": 12, "binding_type": "small"},
                {"min_pages": 161, "max_pages": 200, "size_mm": 14, "binding_type": "small"},
                {"min_pages": 201, "max_pages": 240, "size_mm": 16, "binding_type": "small"},
                {"min_pages": 241, "max_pages": 280, "size_mm": 19, "binding_type": "small"},
                {"min_pages": 281, "max_pages": 320, "size_mm": 22, "binding_type": "small"},
                {"min_pages": 321, "max_pages": 400, "size_mm": 25, "binding_type": "large"},
                {"min_pages": 401, "max_pages": 480, "size_mm": 28, "binding_type": "large"},
                {"min_pages": 481, "max_pages": 600, "size_mm": 32, "binding_type": "large"},
            ],
            "_comment": "Ringbindungsgrößen-Tabelle. Werte sind Beispiele und müssen angepasst werden."
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(example_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported example binding sizes to {output_path}")
