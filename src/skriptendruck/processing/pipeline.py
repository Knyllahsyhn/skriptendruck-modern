"""Verarbeitungs-Pipeline für Druckaufträge."""
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from ..config import get_logger, settings
from ..database.service import DatabaseService
from ..models import BindingType, ColorMode, Order, OrderStatus
from ..services import FilenameParser, PdfService, PricingService, UserService
from ..services.file_organizer import FileOrganizer

logger = get_logger("pipeline")


class OrderPipeline:
    """Pipeline zur Verarbeitung von Druckaufträgen."""
    
    def __init__(
        self,
        db_service: Optional[DatabaseService] = None,
        file_organizer: Optional[FileOrganizer] = None,
    ) -> None:
        """Initialisiert die Pipeline."""
        self.filename_parser = FilenameParser()
        self.user_service = UserService()
        self.pdf_service = PdfService()
        self.pricing_service = PricingService()
        
        self.db_service = db_service or DatabaseService()
        self.file_organizer = file_organizer or FileOrganizer()
        
        self._next_order_id = self._get_next_order_id()
    
    def _get_next_order_id(self) -> int:
        try:
            stats = self.db_service.get_statistics()
            return stats.get("total_orders", 0) + 1
        except Exception:
            return 1
    
    def discover_orders(self, orders_dir: Path) -> List[Order]:
        if not orders_dir.exists():
            logger.error(f"Auftragsverzeichnis nicht gefunden: {orders_dir}")
            return []
        
        orders = []
        pdf_files = list(orders_dir.glob("*.pdf"))
        logger.info(f"Gefunden: {len(pdf_files)} PDF-Dateien")
        
        for pdf_path in pdf_files:
            try:
                order = Order(
                    order_id=self._next_order_id,
                    filename=pdf_path.name,
                    filepath=pdf_path,
                    file_size_bytes=pdf_path.stat().st_size,
                    operator=os.getenv("USER", os.getenv("USERNAME", "unknown")),
                )
                self._next_order_id += 1
                orders.append(order)
            except Exception as e:
                logger.error(f"Fehler beim Erstellen des Orders für {pdf_path}: {e}")
        
        return orders
    
    def process_orders(
        self,
        orders: List[Order],
        save_to_db: bool = True,
        organize_files: bool = True,
    ) -> List[Order]:
        # Temporäres Arbeitsverzeichnis für Deckblätter und Merge
        work_dir = Path(tempfile.mkdtemp(prefix="skriptendruck_"))
        logger.info(f"Arbeitsverzeichnis: {work_dir}")
        
        if settings.parallel_processing and len(orders) > 1:
            processed = self._process_parallel(orders, work_dir)
        else:
            processed = self._process_sequential(orders, work_dir)
        
        # Dateien in Ordnerstruktur organisieren
        logger.warning(
            f"=== ORGANIZE CHECK: organize_files={organize_files}, "
            f"processed={len(processed)} orders ==="
        )
        if organize_files:
            logger.warning("=== STARTE ORGANIZE ===")
            self._organize_files(processed)
            logger.warning("=== ORGANIZE FERTIG ===")
        else:
            logger.warning("=== ORGANIZE ÜBERSPRUNGEN (no_organize flag) ===")
        
        # In Datenbank speichern
        if save_to_db:
            self._save_to_database(processed)

        # Temp-Verzeichnis aufräumen
        self._cleanup_work_dir(work_dir)

        return processed

    def _organize_files(self, processed: List[Order]) -> None:
        """Organisiert verarbeitete Dateien in die Ordnerstruktur."""
        successful = [o for o in processed if o.status == OrderStatus.PROCESSED]
        errors = [o for o in processed if o.is_error]
        logger.info(
            f"Organisiere {len(processed)} Aufträge "
            f"({len(successful)} erfolgreich, {len(errors)} fehlerhaft)"
        )

        # Prüfe ob merged PDFs vorhanden sind
        for order in successful:
            if order.merged_pdf_path:
                exists = order.merged_pdf_path.exists()
                logger.info(
                    f"  Order #{order.order_id}: merged_pdf={order.merged_pdf_path.name} "
                    f"(exists={exists})"
                )
                if not exists:
                    logger.error(
                        f"  FEHLER: merged PDF nicht gefunden: {order.merged_pdf_path}"
                    )
            else:
                logger.warning(f"  Order #{order.order_id}: KEIN merged_pdf_path gesetzt!")

        try:
            self.file_organizer.organize_batch(processed)
            logger.info("Dateien erfolgreich in Ordnerstruktur organisiert")

            # Ergebnis prüfen
            for order in successful:
                if order.merged_pdf_path and order.merged_pdf_path.exists():
                    logger.info(f"  ✓ Order #{order.order_id} → {order.merged_pdf_path}")
                elif order.merged_pdf_path:
                    logger.error(
                        f"  ✗ Order #{order.order_id}: Datei fehlt nach organize: "
                        f"{order.merged_pdf_path}"
                    )
        except Exception as e:
            logger.error(f"Fehler beim Organisieren der Dateien: {e}")
            # Fallback: versuche wenigstens die merged PDFs zu retten
            self._fallback_copy_results(successful)

    def _fallback_copy_results(self, successful: List[Order]) -> None:
        """Fallback: kopiert merged PDFs direkt nach Druckfertig wenn organize fehlschlägt."""
        logger.warning("Fallback: Kopiere merged PDFs direkt nach 02_Druckfertig")
        for order in successful:
            if order.merged_pdf_path and order.merged_pdf_path.exists():
                try:
                    target_dir = self.file_organizer.get_print_dir(
                        order.color_mode or ColorMode.BLACK_WHITE
                    )
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / order.merged_pdf_path.name
                    shutil.copy2(str(order.merged_pdf_path), str(target))
                    logger.info(f"  Fallback: {order.filename} → {target}")
                    order.merged_pdf_path = target
                except Exception as e2:
                    logger.error(f"  Fallback fehlgeschlagen für {order.filename}: {e2}")

    def _save_to_database(self, processed: List[Order]) -> None:
        """Speichert Aufträge in der Datenbank."""
        try:
            self.db_service.save_orders_batch(processed)
            for order in processed:
                if order.status == OrderStatus.PROCESSED:
                    self.db_service.create_billing_record(order)
            logger.info(f"{len(processed)} Aufträge in Datenbank gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern in Datenbank: {e}")

    def _cleanup_work_dir(self, work_dir: Path) -> None:
        """Räumt das temporäre Arbeitsverzeichnis auf."""
        try:
            remaining = list(work_dir.iterdir())
            if remaining:
                names = [f.name for f in remaining[:5]]
                logger.info(
                    f"Temp aufräumen: {len(remaining)} Dateien "
                    f"({', '.join(names)}{'...' if len(remaining) > 5 else ''})"
                )
            shutil.rmtree(str(work_dir), ignore_errors=True)
        except Exception as e:
            logger.warning(f"Temp-Verzeichnis konnte nicht gelöscht werden: {e}")

    def _process_sequential(self, orders: List[Order], output_dir: Path) -> List[Order]:
        logger.info(f"Verarbeite {len(orders)} Aufträge sequenziell")
        processed = []
        for order in orders:
            self.process_single_order(order, output_dir)
            processed.append(order)
        return processed

    def _process_parallel(self, orders: List[Order], output_dir: Path) -> List[Order]:
        logger.info(f"Verarbeite {len(orders)} Aufträge parallel (max {settings.max_workers} Worker)")
        processed = []
        with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
            futures = {
                executor.submit(self.process_single_order, order, output_dir): order
                for order in orders
            }
            for future in as_completed(futures):
                order = futures[future]
                try:
                    future.result()
                    processed.append(order)
                except Exception as e:
                    logger.error(f"Fehler bei Order {order.order_id}: {e}")
                    order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
                    processed.append(order)
        return processed
    
    def process_single_order(self, order: Order, output_dir: Path) -> None:
        logger.info(f"Verarbeite Order #{order.order_id}: {order.filename}")
        
        self._parse_filename(order)
        if order.is_valid:
            self._validate_user(order)
        if order.is_valid:
            self._analyze_pdf(order)
        if order.is_valid:
            self._calculate_price(order)
        if order.is_valid:
            self._create_coversheet(order, output_dir)
        if order.is_valid:
            self._merge_documents(order, output_dir)
        
        if order.is_valid:
            order.status = OrderStatus.PROCESSED
            logger.info(f"Order #{order.order_id} erfolgreich verarbeitet")
        else:
            logger.warning(f"Order #{order.order_id} mit Fehler: {order.status.value}")
    
    def _parse_filename(self, order: Order) -> None:
        try:
            username, name, color, binding, seq = self.filename_parser.parse(order.filename)
            order.parsed_username = username
            order.parsed_name = name
            order.color_mode = color
            order.binding_type = binding
            order.sequence_number = seq
            if not username and not name:
                order.set_error(OrderStatus.ERROR_INVALID_FILENAME, "Konnte Benutzername/Name nicht extrahieren")
        except Exception as e:
            logger.error(f"Fehler beim Parsen des Dateinamens: {e}")
            order.set_error(OrderStatus.ERROR_INVALID_FILENAME, str(e))
    
    def _validate_user(self, order: Order) -> None:
        try:
            user = None
            if order.parsed_username:
                user = self.user_service.get_user(order.parsed_username)
            if not user and order.parsed_name:
                logger.warning(f"User nicht gefunden: {order.parsed_name}")
            if not user:
                order.set_error(
                    OrderStatus.ERROR_USER_NOT_FOUND,
                    f"Benutzer nicht gefunden: {order.parsed_username or order.parsed_name}"
                )
                return
            if user.is_blocked:
                order.set_error(OrderStatus.ERROR_USER_BLOCKED, f"Benutzer ist blockiert: {user.username}")
                return
            order.user = user
            order.status = OrderStatus.VALIDATED
            logger.info(f"Benutzer validiert: {user}")
        except Exception as e:
            logger.error(f"Fehler bei Benutzervalidierung: {e}")
            order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
    
    def _analyze_pdf(self, order: Order) -> None:
        try:
            page_count, is_protected = self.pdf_service.get_page_count(order.filepath)
            if is_protected:
                order.set_error(OrderStatus.ERROR_PASSWORD_PROTECTED, "PDF ist passwortgeschützt")
                return
            if page_count is None:
                order.set_error(OrderStatus.ERROR_UNKNOWN, "Konnte Seitenzahl nicht ermitteln")
                return
            order.page_count = page_count
            order.is_password_protected = is_protected
            is_valid, error_msg = self.pricing_service.validate_page_count(
                page_count, order.binding_type or BindingType.NONE
            )
            if not is_valid:
                if "wenig" in error_msg.lower():
                    order.set_error(OrderStatus.ERROR_TOO_FEW_PAGES, error_msg)
                else:
                    order.set_error(OrderStatus.ERROR_TOO_MANY_PAGES, error_msg)
        except Exception as e:
            logger.error(f"Fehler bei PDF-Analyse: {e}")
            order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
    
    def _calculate_price(self, order: Order) -> None:
        try:
            if not order.page_count or not order.color_mode or not order.binding_type:
                raise ValueError("Fehlende Informationen für Preisberechnung")
            price_calc = self.pricing_service.calculate_price(
                pages=order.page_count,
                color_mode=order.color_mode,
                binding_type=order.binding_type,
            )
            order.price_calculation = price_calc
            logger.info(f"Preis berechnet: {price_calc.total_price_formatted}")
        except Exception as e:
            logger.error(f"Fehler bei Preisberechnung: {e}")
            order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
    
    def _create_coversheet(self, order: Order, output_dir: Path) -> None:
        try:
            coversheet_path = output_dir / f"{order.order_id:04d}_coversheet.pdf"
            if self.pdf_service.create_coversheet(order, coversheet_path):
                order.coversheet_path = coversheet_path
            else:
                order.set_error(OrderStatus.ERROR_UNKNOWN, "Deckblatt konnte nicht erstellt werden")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Deckblatts: {e}")
            order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
    
    def _merge_documents(self, order: Order, output_dir: Path) -> None:
        try:
            if not order.coversheet_path:
                raise ValueError("Kein Deckblatt vorhanden")
            merged_path = output_dir / f"{order.order_id:04d}_{order.filename}"
            if self.pdf_service.merge_pdfs(
                coversheet_path=order.coversheet_path,
                document_path=order.filepath,
                output_path=merged_path,
                    add_empty_page=True,
            ):
                order.merged_pdf_path = merged_path
            else:
                order.set_error(OrderStatus.ERROR_UNKNOWN, "PDFs konnten nicht zusammengefügt werden")
        except Exception as e:
            logger.error(f"Fehler beim Zusammenfügen der PDFs: {e}")
            order.set_error(OrderStatus.ERROR_UNKNOWN, str(e))
