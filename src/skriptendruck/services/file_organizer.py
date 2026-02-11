"""Service für Dateiverwaltung und Ordnerstruktur.

Verwaltet die Ordnerstruktur analog zum Original-MATLAB-System (moveDocs.m),
verschiebt verarbeitete PDFs in die richtigen Zielordner und erstellt
Backups der Originaldateien.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..config import get_logger, settings
from ..models import ColorMode, Order, OrderStatus

logger = get_logger("file_organizer")


class FileOrganizer:
    """
    Organisiert die Ordnerstruktur für Druckaufträge.
    
    Struktur:
        01_Auftraege/                    ← Input
        02_Druckfertig/
           sw/                           ← SW-Jobs mit Deckblatt
              gedruckt/                  ← Erledigte SW-Jobs
           farbig/                       ← Farb-Jobs mit Deckblatt
              gedruckt/                  ← Erledigte Farb-Jobs
        03_Originale/                    ← Backup mit Zeitstempel
           2026-01-16_12-38/
        04_Fehler/
           benutzer_nicht_gefunden/
           zu_viele_seiten/
           zu_wenig_seiten/
           passwortgeschuetzt/
           gesperrt/
           sonstige/
        05_Manuell/                      ← Manuelle Aufträge
    """

    DIR_INPUT = "01_Auftraege"
    DIR_PRINT = "02_Druckfertig"
    DIR_PRINT_SW = "sw"
    DIR_PRINT_COLOR = "farbig"
    DIR_PRINTED = "gedruckt"
    DIR_ORIGINALS = "03_Originale"
    DIR_ERRORS = "04_Fehler"
    DIR_MANUAL = "05_Manuell"

    ERROR_DIRS = {
        OrderStatus.ERROR_USER_NOT_FOUND: "benutzer_nicht_gefunden",
        OrderStatus.ERROR_USER_BLOCKED: "gesperrt",
        OrderStatus.ERROR_TOO_FEW_PAGES: "zu_wenig_seiten",
        OrderStatus.ERROR_TOO_MANY_PAGES: "zu_viele_seiten",
        OrderStatus.ERROR_PASSWORD_PROTECTED: "passwortgeschuetzt",
        OrderStatus.ERROR_INVALID_FILENAME: "sonstige",
        OrderStatus.ERROR_UNKNOWN: "sonstige",
    }

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self.base_path = base_path or settings.base_path
        logger.info(f"FileOrganizer base_path: {self.base_path}")

    def ensure_directory_structure(self) -> None:
        """Erstellt die komplette Ordnerstruktur."""
        directories = [
            self.get_input_dir(),
            self.get_print_dir(ColorMode.BLACK_WHITE),
            self.get_print_dir(ColorMode.BLACK_WHITE) / self.DIR_PRINTED,
            self.get_print_dir(ColorMode.COLOR),
            self.get_print_dir(ColorMode.COLOR) / self.DIR_PRINTED,
            self.get_originals_dir(),
            *(self.get_error_dir(status) for status in self.ERROR_DIRS),
            self.get_manual_dir(),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        logger.info("Ordnerstruktur verifiziert")

    def get_input_dir(self) -> Path:
        return self.base_path / self.DIR_INPUT

    def get_print_dir(self, color_mode: ColorMode) -> Path:
        subdir = self.DIR_PRINT_COLOR if color_mode == ColorMode.COLOR else self.DIR_PRINT_SW
        return self.base_path / self.DIR_PRINT / subdir

    def get_originals_dir(self) -> Path:
        return self.base_path / self.DIR_ORIGINALS

    def get_originals_batch_dir(self, timestamp: Optional[datetime] = None) -> Path:
        ts = timestamp or datetime.now()
        batch_name = ts.strftime("%Y-%m-%d_%H-%M")
        return self.get_originals_dir() / batch_name

    def get_error_dir(self, status: OrderStatus) -> Path:
        subdir = self.ERROR_DIRS.get(status, "sonstige")
        return self.base_path / self.DIR_ERRORS / subdir

    def get_manual_dir(self) -> Path:
        return self.base_path / self.DIR_MANUAL

    def move_successful_order(self, order: Order) -> Optional[Path]:
        """Verschiebt ein erfolgreich verarbeitetes PDF nach 02_Druckfertig/."""
        if not order.merged_pdf_path:
            logger.error(f"Order #{order.order_id}: merged_pdf_path ist None")
            return None

        if not order.merged_pdf_path.exists():
            logger.error(
                f"Order #{order.order_id}: merged PDF nicht gefunden: "
                f"{order.merged_pdf_path}"
            )
            return None

        try:
            color_mode = order.color_mode or ColorMode.BLACK_WHITE
            target_dir = self.get_print_dir(color_mode)
            target_dir.mkdir(parents=True, exist_ok=True)
            target_name = f"{order.order_id:04d}_{order.filename}"
            target_path = target_dir / target_name

            logger.debug(
                f"Verschiebe Order #{order.order_id}: "
                f"{order.merged_pdf_path} → {target_path}"
            )

            # Kopieren statt move - sicherer bei Cross-Device (temp → Netzlaufwerk)
            shutil.copy2(str(order.merged_pdf_path), str(target_path))

            # Prüfen ob Kopie erfolgreich
            if target_path.exists():
                # Original im temp löschen
                try:
                    order.merged_pdf_path.unlink()
                except Exception:
                    pass  # Nicht kritisch
                logger.debug(f"Order #{order.order_id} → {target_path}")
                return target_path
            else:
                logger.error(f"Order #{order.order_id}: Kopie fehlgeschlagen!")
                return None
                
        except Exception as e:
            logger.error(f"Fehler beim Verschieben von Order #{order.order_id}: {e}")
            return None

    def move_failed_order(self, order: Order) -> Optional[Path]:
        """Kopiert ein fehlerhaftes PDF nach 04_Fehler/."""
        if not order.filepath or not order.filepath.exists():
            logger.warning(f"Order #{order.order_id}: Quelldatei nicht mehr vorhanden")
            return None
        try:
            target_dir = self.get_error_dir(order.status)
            target_dir.mkdir(parents=True, exist_ok=True)
            target_name = f"{order.order_id:04d}_{order.filename}"
            target_path = target_dir / target_name
            shutil.copy2(str(order.filepath), str(target_path))
            logger.info(f"Order #{order.order_id} (Fehler) → {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Fehler beim Kopieren von Order #{order.order_id}: {e}")
            return None

    def backup_original(self, order: Order, batch_dir: Path) -> Optional[Path]:
        """Erstellt ein Backup der Originaldatei in 03_Originale/."""
        if not order.filepath or not order.filepath.exists():
            logger.warning(f"Order #{order.order_id}: Original nicht gefunden: {order.filepath}")
            return None
        try:
            batch_dir.mkdir(parents=True, exist_ok=True)
            target_path = batch_dir / order.filename
            shutil.copy2(str(order.filepath), str(target_path))
            logger.debug(f"Backup: {order.filename} → {batch_dir.name}/")
            return target_path
        except Exception as e:
            logger.error(f"Fehler beim Backup von {order.filename}: {e}")
            return None

    def cleanup_input(self, order: Order) -> bool:
        """Löscht die Originaldatei aus 01_Auftraege/."""
        if not order.filepath or not order.filepath.exists():
            return True
        try:
            order.filepath.unlink()
            logger.debug(f"Eingabedatei entfernt: {order.filename}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von {order.filename}: {e}")
            return False

    def organize_order(self, order: Order, batch_dir: Path) -> None:
        """Organisiert einen einzelnen Auftrag."""
        logger.info(
            f"Organisiere Order #{order.order_id}: status={order.status.value}, "
            f"merged_pdf={order.merged_pdf_path}"
        )

        # 1. Backup des Originals
        self.backup_original(order, batch_dir)

        # 2. Verschieben je nach Status
        if order.status == OrderStatus.PROCESSED:
            new_path = self.move_successful_order(order)
            if new_path:
                order.merged_pdf_path = new_path
                logger.debug(f"Order #{order.order_id}: erfolgreich nach {new_path}")
            else:
                logger.error(f"Order #{order.order_id}: Verschieben fehlgeschlagen!")
        elif order.is_error:
            self.move_failed_order(order)

        # 3. Original aus Auftraege löschen
        self.cleanup_input(order)

    def organize_batch(self, orders: List[Order]) -> None:
        """Organisiert eine Batch von Aufträgen in die Ordnerstruktur."""
        if not orders:
            return

        logger.debug(f"organize_batch: {len(orders)} Aufträge, base_path={self.base_path}")
        
        self.ensure_directory_structure()
        batch_dir = self.get_originals_batch_dir()
        logger.info(f"Backup-Verzeichnis: {batch_dir}")
        
        for order in orders:
            try:
                self.organize_order(order, batch_dir)
            except Exception as e:
                logger.error(f"Fehler beim Organisieren von Order #{order.order_id}: {e}")

        # Deckblatt-Einzeldateien aufräumen
        for order in orders:
            if order.coversheet_path and order.coversheet_path.exists():
                try:
                    order.coversheet_path.unlink()
                except Exception:
                    pass

        logger.debug(f"Batch organisiert: {len(orders)} Aufträge")
