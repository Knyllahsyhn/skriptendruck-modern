"""Service für Excel-Export von Auftrags- und Abrechnungslisten."""
from datetime import datetime
from pathlib import Path
from typing import List

import xlsxwriter
from xlsxwriter.format import Format
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from ..config import get_logger
from ..database.models import BillingRecord, OrderRecord

logger = get_logger("excel_export")


class ExcelExportService:
    """Service für Excel-Export."""
    
    def export_orders_list(
        self,
        orders: List[OrderRecord],
        output_path: Path,
    ) -> bool:
        """
        Exportiert eine Auftragsliste nach Excel.
        
        Args:
            orders: Liste von OrderRecords
            output_path: Pfad zur Excel-Datei
            
        Returns:
            True bei Erfolg
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            workbook = xlsxwriter.Workbook(str(output_path))
            worksheet = workbook.add_worksheet("Aufträge")
            
            # Formate definieren
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
            })
            
            date_format = workbook.add_format({'num_format': 'dd.mm.yyyy hh:mm'})
            price_format = workbook.add_format({'num_format': '#,##0.00 €'})
            
            # Header
            headers = [
                'Auftrags-ID', 'Datum', 'Dateiname', 'RZ-Kennung', 'Vorname', 'Nachname',
                'Fakultät', 'Seiten', 'Farbmodus', 'Bindung', 'Bindungsgröße (mm)',
                'Seitenpreis', 'Bindungspreis', 'Gesamtpreis', 'Nach Anzahlung',
                'Status', 'Bearbeiter'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Daten
            for row, order in enumerate(orders, start=1):
                worksheet.write(row, 0, order.order_id)
                worksheet.write_datetime(row, 1, order.created_at, date_format)
                worksheet.write(row, 2, order.filename)
                worksheet.write(row, 3, order.username or '')
                worksheet.write(row, 4, order.first_name or '')
                worksheet.write(row, 5, order.last_name or '')
                worksheet.write(row, 6, order.faculty or '')
                worksheet.write(row, 7, order.page_count or 0)
                worksheet.write(row, 8, self._format_color_mode(order.color_mode))
                worksheet.write(row, 9, self._format_binding_type(order.binding_type))
                worksheet.write(row, 10, order.binding_size_mm or '')
                worksheet.write(row, 11, order.pages_price or 0, price_format)
                worksheet.write(row, 12, order.binding_price or 0, price_format)
                worksheet.write(row, 13, order.total_price or 0, price_format)
                worksheet.write(row, 14, order.price_after_deposit or 0, price_format)
                worksheet.write(row, 15, self._format_status(order.status))
                worksheet.write(row, 16, order.operator or '')
            
            # Spaltenbreiten anpassen
            worksheet.set_column('A:A', 12)  # Auftrags-ID
            worksheet.set_column('B:B', 18)  # Datum
            worksheet.set_column('C:C', 30)  # Dateiname
            worksheet.set_column('D:G', 15)  # Benutzerdaten
            worksheet.set_column('H:H', 8)   # Seiten
            worksheet.set_column('I:J', 12)  # Farbmodus/Bindung
            worksheet.set_column('K:K', 18)  # Bindungsgröße
            worksheet.set_column('L:O', 15)  # Preise
            worksheet.set_column('P:P', 20)  # Status
            worksheet.set_column('Q:Q', 15)  # Bearbeiter
            
            # Autofilter
            worksheet.autofilter(0, 0, len(orders), len(headers) - 1)
            
            workbook.close()
            
            logger.info(f"Auftragsliste exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Excel-Export: {e}")
            return False
    
    def export_billing_list(
        self,
        billings: List[BillingRecord],
        output_path: Path,
    ) -> bool:
        """
        Exportiert eine Abrechnungsliste nach Excel.
        
        Args:
            billings: Liste von BillingRecords
            output_path: Pfad zur Excel-Datei
            
        Returns:
            True bei Erfolg
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            workbook = xlsxwriter.Workbook(str(output_path))
            worksheet = workbook.add_worksheet("Abrechnungen")
            
            # Formate definieren
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#70AD47',
                'font_color': 'white',
                'border': 1,
            })
            
            date_format = workbook.add_format({'num_format': 'dd.mm.yyyy hh:mm'})
            price_format = workbook.add_format({'num_format': '#,##0.00 €'})
            
            paid_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            unpaid_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            
            # Header
            headers = [
                'Abr.-ID', 'Auftrags-ID', 'Datum', 'RZ-Kennung', 'Name',
                'Gesamtbetrag', 'Anzahlung', 'Restbetrag', 'Bezahlt', 'Bezahlt am', 'Notizen'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Daten
            for row, billing in enumerate(billings, start=1):
                worksheet.write(row, 0, billing.id)
                worksheet.write(row, 1, billing.order_id)
                worksheet.write_datetime(row, 2, billing.billing_date, date_format)
                worksheet.write(row, 3, billing.username)
                worksheet.write(row, 4, billing.full_name)
                worksheet.write(row, 5, billing.total_amount, price_format)
                worksheet.write(row, 6, billing.paid_deposit, price_format)
                worksheet.write(row, 7, billing.remaining_amount, price_format)
                
                # Bezahlt-Status mit Formatierung
                paid_text = 'Ja' if billing.is_paid else 'Nein'
                cell_format = paid_format if billing.is_paid else unpaid_format
                worksheet.write(row, 8, paid_text, cell_format)
                
                if billing.paid_at:
                    worksheet.write_datetime(row, 9, billing.paid_at, date_format)
                else:
                    worksheet.write(row, 9, '')
                
                worksheet.write(row, 10, billing.notes or '')
            
            # Spaltenbreiten anpassen
            worksheet.set_column('A:B', 12)  # IDs
            worksheet.set_column('C:C', 18)  # Datum
            worksheet.set_column('D:E', 20)  # Benutzerdaten
            worksheet.set_column('F:H', 15)  # Beträge
            worksheet.set_column('I:I', 10)  # Bezahlt
            worksheet.set_column('J:J', 18)  # Bezahlt am
            worksheet.set_column('K:K', 30)  # Notizen
            
            # Autofilter
            worksheet.autofilter(0, 0, len(billings), len(headers) - 1)
            
            # Summen am Ende
            last_row = len(billings) + 2
            worksheet.write(last_row, 4, 'Summen:', header_format)
            worksheet.write_formula(
                last_row, 5,
                f'=SUM(F2:F{len(billings)+1})',
                price_format
            )
            worksheet.write_formula(
                last_row, 6,
                f'=SUM(G2:G{len(billings)+1})',
                price_format
            )
            worksheet.write_formula(
                last_row, 7,
                f'=SUM(H2:H{len(billings)+1})',
                price_format
            )
            
            workbook.close()
            
            logger.info(f"Abrechnungsliste exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Excel-Export: {e}")
            return False
    
    def _format_color_mode(self, color_mode: str | None) -> str:
        """Formatiert Farbmodus für Excel."""
        if not color_mode:
            return ''
        return 'Farbe' if color_mode == 'color' else 'Schwarz-Weiß'
    
    def _format_binding_type(self, binding_type: str | None) -> str:
        """Formatiert Bindungstyp für Excel."""
        if not binding_type:
            return ''
        
        mapping = {
            'none': 'Ohne Bindung',
            'small': 'Ringbindung (klein)',
            'large': 'Ringbindung (groß)',
            'folder': 'Schnellhefter',
        }
        return mapping.get(binding_type, binding_type)
    
    def _format_status(self, status: str) -> str:
        """Formatiert Status für Excel."""
        mapping = {
            'pending': 'Ausstehend',
            'validated': 'Validiert',
            'processed': 'Verarbeitet',
            'error_user_not_found': 'Fehler: Benutzer nicht gefunden',
            'error_user_blocked': 'Fehler: Benutzer blockiert',
            'error_too_few_pages': 'Fehler: Zu wenig Seiten',
            'error_too_many_pages': 'Fehler: Zu viele Seiten',
            'error_password_protected': 'Fehler: Passwortgeschützt',
            'error_invalid_filename': 'Fehler: Ungültiger Dateiname',
            'error_unknown': 'Fehler: Unbekannt',
        }
        return mapping.get(status, status)
