"""Service für PDF-Verarbeitung mit pypdf."""
from pathlib import Path
from typing import Optional, Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from ..config import get_logger
from ..models import Order

logger = get_logger("pdf_service")


class PdfService:
    """Service für PDF-Verarbeitung."""
    
    def get_page_count(self, pdf_path: Path) -> Tuple[Optional[int], bool]:
        """
        Ermittelt die Seitenzahl eines PDFs.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Tuple (page_count, is_password_protected)
        """
        try:
            reader = PdfReader(pdf_path)
            
            # Passwortschutz prüfen
            if reader.is_encrypted:
                logger.warning(f"PDF ist passwortgeschützt: {pdf_path}")
                return None, True
            
            page_count = len(reader.pages)
            logger.debug(f"PDF hat {page_count} Seiten: {pdf_path}")
            return page_count, False
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen des PDFs {pdf_path}: {e}")
            return None, False
    
    def create_coversheet(
        self,
        order: Order,
        output_path: Path,
    ) -> bool:
        """
        Erstellt ein Deckblatt für einen Auftrag.
        
        Args:
            order: Auftrags-Objekt
            output_path: Pfad für das Deckblatt
            
        Returns:
            True bei Erfolg
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Canvas erstellen
            c = canvas.Canvas(str(output_path), pagesize=A4)
            width, height = A4
            
            # Schriftarten
            c.setFont("Helvetica-Bold", 18)
            
            # Titel
            c.drawString(50, height - 50, "Fachschaft - Skriptendruck")
            
            # Linie
            c.line(50, height - 60, width - 50, height - 60)
            
            # Informationen
            c.setFont("Helvetica-Bold", 12)
            y = height - 100
            line_height = 20
            
            # Auftrags-ID
            c.drawString(50, y, "Auftrags-ID:")
            c.setFont("Helvetica", 12)
            c.drawString(200, y, str(order.order_id))
            y -= line_height
            
            # Datum
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Datum:")
            c.setFont("Helvetica", 12)
            c.drawString(200, y, order.created_at.strftime("%d.%m.%Y %H:%M"))
            y -= line_height
            
            # Dateiname
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Dateiname:")
            c.setFont("Helvetica", 12)
            c.drawString(200, y, order.filename)
            y -= line_height * 2
            
            # Benutzer
            if order.user:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "RZ-Kennung:")
                c.setFont("Helvetica", 12)
                c.drawString(200, y, order.user.username)
                y -= line_height
                
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Name:")
                c.setFont("Helvetica", 12)
                c.drawString(200, y, order.user.full_name)
                y -= line_height
                
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Fakultät:")
                c.setFont("Helvetica", 12)
                c.drawString(200, y, order.user.faculty)
                y -= line_height * 2
            
            # PDF-Informationen
            if order.page_count:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Seitenzahl:")
                c.setFont("Helvetica", 12)
                c.drawString(200, y, str(order.page_count))
                y -= line_height
            
            # Preisberechnung
            if order.price_calculation:
                calc = order.price_calculation
                
                # Farbmodus
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Druck:")
                c.setFont("Helvetica", 12)
                color_text = "Farbe" if calc.color_mode.value == "color" else "Schwarz-Weiß"
                c.drawString(200, y, f"{color_text} ({calc.pages_price_formatted})")
                y -= line_height
                
                # Bindung
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Bindung:")
                c.setFont("Helvetica", 12)
                
                if calc.binding_type.value == "none":
                    binding_text = "Nein"
                elif calc.binding_type.value == "folder":
                    binding_text = f"Schnellhefter ({calc.binding_price_formatted})"
                else:
                    binding_text = f"Ja ({calc.binding_price_formatted})"
                    if calc.binding_size_mm:
                        binding_text += f" - {calc.binding_size_mm}mm"
                
                c.drawString(200, y, binding_text)
                y -= line_height * 2
                
                # Preis
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "Gesamtpreis:")
                c.drawString(200, y, calc.total_price_formatted)
                y -= line_height
                
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "Nach Abzug 1€ Anzahlung:")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(200, y, calc.price_after_deposit_formatted)
            
            # Fehlerhinweis bei ungültigem Dateinamen
            if order.status.value == "error_invalid_filename":
                y -= line_height * 2
                c.setFillColorRGB(0.8, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "ACHTUNG: Dateiname nicht korrekt!")
                y -= line_height
                c.setFont("Helvetica", 9)
                c.drawString(50, y, "Bitte nächstes Mal richtig benennen:")
                y -= line_height
                c.drawString(50, y, "RZ-Kennung_sw/farbig_mb/ob/sh_001.pdf")
            
            # Footer
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 8)
            c.drawString(50, 50, "Fachschaft Maschinenbau - Hochschule Regensburg")
            
            c.save()
            
            logger.info(f"Deckblatt erstellt: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Deckblatts: {e}")
            return False
    
    def merge_pdfs(
        self,
        coversheet_path: Path,
        document_path: Path,
        output_path: Path,
        add_empty_page: bool = False,
    ) -> bool:
        """
        Fügt Deckblatt und Dokument zusammen.
        
        Args:
            coversheet_path: Pfad zum Deckblatt
            document_path: Pfad zum Dokument
            output_path: Pfad für die Ausgabedatei
            add_empty_page: Leere Seite zwischen Deckblatt und Dokument einfügen
            
        Returns:
            True bei Erfolg
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            writer = PdfWriter()
            
            # Deckblatt hinzufügen
            coversheet_reader = PdfReader(coversheet_path)
            for page in coversheet_reader.pages:
                writer.add_page(page)
            
            # Optional: Leere Seite
            if add_empty_page:
                writer.add_blank_page(width=A4[0], height=A4[1])
            
            # Dokument hinzufügen
            document_reader = PdfReader(document_path)
            for page in document_reader.pages:
                writer.add_page(page)
            
            # Speichern
            with open(output_path, "wb") as f:
                writer.write(f)
            
            logger.info(f"PDFs zusammengefügt: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Zusammenfügen der PDFs: {e}")
            return False
