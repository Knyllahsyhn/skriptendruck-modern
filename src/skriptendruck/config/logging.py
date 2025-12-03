"""Logging-Konfiguration für das Skriptendruckprogramm."""
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    use_rich: bool = True,
) -> logging.Logger:
    """
    Konfiguriert das Logging mit optionaler Datei-Ausgabe und Rich-Formatierung.
    
    Args:
        level: Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optionaler Pfad zur Log-Datei
        use_rich: Rich Handler für schöne Console-Ausgabe verwenden
        
    Returns:
        Konfigurierter Logger
    """
    # Root Logger konfigurieren
    logger = logging.getLogger("skriptendruck")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Formatter
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console Handler
    if use_rich:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=False,
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(file_formatter)
    
    console_handler.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Immer alle Details in Datei
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Gibt einen Logger für ein spezifisches Modul zurück."""
    return logging.getLogger(f"skriptendruck.{name}")
