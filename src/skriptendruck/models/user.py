"""Datenmodelle für Benutzer."""
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """Repräsentiert einen Benutzer."""
    
    username: str = Field(..., description="RZ-Kennung, z.B. 'mus43225'")
    first_name: str = Field(..., description="Vorname")
    last_name: str = Field(..., description="Nachname")
    faculty: str = Field(..., description="Fakultät, z.B. 'M' für Maschinenbau")
    is_blocked: bool = Field(default=False, description="Benutzer auf Blacklist")
    email: Optional[str] = Field(default=None, description="E-Mail Adresse (optional)")
    
    @property
    def full_name(self) -> str:
        """Gibt den vollständigen Namen zurück."""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self) -> str:
        return f"{self.full_name} ({self.username})"
    
    class Config:
        frozen = False  # Allow modification for blacklist status
