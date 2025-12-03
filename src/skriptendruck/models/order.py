"""Datenmodelle für Aufträge."""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .pricing import BindingType, ColorMode, PriceCalculation
from .user import User


class OrderStatus(str, Enum):
    """Status eines Auftrags."""
    PENDING = "pending"  # Auftrag erkannt
    VALIDATED = "validated"  # Benutzer validiert
    PROCESSED = "processed"  # PDF verarbeitet
    ERROR_USER_NOT_FOUND = "error_user_not_found"
    ERROR_USER_BLOCKED = "error_user_blocked"
    ERROR_TOO_FEW_PAGES = "error_too_few_pages"
    ERROR_TOO_MANY_PAGES = "error_too_many_pages"
    ERROR_PASSWORD_PROTECTED = "error_password_protected"
    ERROR_INVALID_FILENAME = "error_invalid_filename"
    ERROR_UNKNOWN = "error_unknown"


class Order(BaseModel):
    """Repräsentiert einen Druckauftrag."""
    
    # Datei-Informationen
    order_id: int = Field(..., description="Eindeutige Auftrags-ID")
    filename: str = Field(..., description="Dateiname")
    filepath: Path = Field(..., description="Pfad zur PDF-Datei")
    file_size_bytes: int = Field(..., description="Dateigröße in Bytes")
    
    # Geparste Dateinamen-Informationen
    parsed_username: Optional[str] = Field(default=None, description="Geparster Benutzername")
    parsed_name: Optional[str] = Field(default=None, description="Geparster Name")
    color_mode: Optional[ColorMode] = Field(default=None, description="Farbmodus")
    binding_type: Optional[BindingType] = Field(default=None, description="Bindungstyp")
    sequence_number: Optional[int] = Field(
        default=None,
        description="Laufende Nummer (bei mehreren Skripten)"
    )
    
    # Benutzer-Informationen
    user: Optional[User] = Field(default=None, description="Validierter Benutzer")
    
    # PDF-Informationen
    page_count: Optional[int] = Field(default=None, description="Anzahl Seiten im PDF")
    is_password_protected: bool = Field(default=False, description="PDF passwortgeschützt")
    
    # Preisberechnung
    price_calculation: Optional[PriceCalculation] = Field(
        default=None,
        description="Preisberechnung"
    )
    
    # Status und Metadaten
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Auftragsstatus")
    error_message: Optional[str] = Field(default=None, description="Fehlermeldung")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Erstellungszeitpunkt")
    processed_at: Optional[datetime] = Field(default=None, description="Verarbeitungszeitpunkt")
    operator: Optional[str] = Field(default=None, description="Bearbeiter")
    
    # Output Pfade
    coversheet_path: Optional[Path] = Field(default=None, description="Pfad zum Deckblatt")
    merged_pdf_path: Optional[Path] = Field(default=None, description="Pfad zum fertigen PDF")
    
    @property
    def is_valid(self) -> bool:
        """Prüft ob der Auftrag valide ist."""
        return not self.status.value.startswith("error")
    
    @property
    def is_error(self) -> bool:
        """Prüft ob der Auftrag einen Fehler hat."""
        return self.status.value.startswith("error")
    
    def set_error(self, status: OrderStatus, message: str) -> None:
        """Setzt einen Fehler-Status."""
        self.status = status
        self.error_message = message
    
    def __str__(self) -> str:
        user_str = str(self.user) if self.user else self.parsed_username or "Unbekannt"
        return f"Order #{self.order_id}: {user_str} - {self.filename} ({self.status.value})"
    
    class Config:
        arbitrary_types_allowed = True
