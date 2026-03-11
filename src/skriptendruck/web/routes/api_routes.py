"""REST-API Routen für AJAX-Aktionen (Aufträge starten, löschen, Excel-Export)."""
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import select

from ..auth import get_current_user
from ...config import get_logger, settings
from ...database.models import OrderRecord, BillingRecord
from ...database.service import DatabaseService
def _get_excel_service():
    """Lazy-Import des ExcelExportService (vermeidet pypdf-Dependency beim Startup)."""
    from skriptendruck.services.excel_service import ExcelExportService
    return ExcelExportService()

logger = get_logger("web.routes.api")

router = APIRouter(tags=["api"])


def _get_db() -> DatabaseService:
    """Gibt eine DatabaseService-Instanz zurück."""
    db_path = settings.database_path
    if not db_path.is_absolute():
        db_path = settings.base_path / db_path
    return DatabaseService(db_path=db_path)


def _require_auth(request: Request) -> tuple:
    """Prüft Authentifizierung für API-Calls. Returns (user, error_response)."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse(
            status_code=401,
            content={"error": "Nicht authentifiziert"},
        )
    return user, None


@router.post("/orders/{order_id}/start")
async def start_order(request: Request, order_id: int):
    """Gibt einen Auftrag frei / markiert ihn als 'validated'."""
    user, error = _require_auth(request)
    if error:
        return error
    
    try:
        db = _get_db()
        with db.SessionLocal() as session:
            stmt = select(OrderRecord).where(OrderRecord.order_id == order_id)
            order = session.scalar(stmt)
            
            if not order:
                return JSONResponse(status_code=404, content={"error": "Auftrag nicht gefunden"})
            
            if order.status not in ("pending", "validated"):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Auftrag kann im Status '{order.status}' nicht gestartet werden"},
                )
            
            order.status = "validated"
            order.operator = user["username"]
            order.processed_at = datetime.now()
            session.commit()
            
            logger.info(f"Auftrag #{order_id} von {user['username']} freigegeben")
            return JSONResponse(content={"success": True, "message": f"Auftrag #{order_id} freigegeben"})
    
    except Exception as e:
        logger.error(f"Fehler beim Freigeben von Auftrag #{order_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/orders/{order_id}")
async def delete_order(request: Request, order_id: int):
    """Löscht einen Auftrag."""
    user, error = _require_auth(request)
    if error:
        return error
    
    try:
        db = _get_db()
        with db.SessionLocal() as session:
            stmt = select(OrderRecord).where(OrderRecord.order_id == order_id)
            order = session.scalar(stmt)
            
            if not order:
                return JSONResponse(status_code=404, content={"error": "Auftrag nicht gefunden"})
            
            session.delete(order)
            session.commit()
            
            logger.info(f"Auftrag #{order_id} von {user['username']} gelöscht")
            return JSONResponse(content={"success": True, "message": f"Auftrag #{order_id} gelöscht"})
    
    except Exception as e:
        logger.error(f"Fehler beim Löschen von Auftrag #{order_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/export/orders")
async def export_orders_excel(request: Request):
    """Exportiert alle Aufträge als Excel-Datei."""
    user, error = _require_auth(request)
    if error:
        return error
    
    try:
        db = _get_db()
        with db.SessionLocal() as session:
            stmt = select(OrderRecord).order_by(OrderRecord.created_at.desc())
            orders = list(session.scalars(stmt))
            
            if not orders:
                return JSONResponse(status_code=404, content={"error": "Keine Aufträge vorhanden"})
            
            # Excel-Export
            excel_service = _get_excel_service()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Versuche das konfigurierte Export-Verzeichnis, Fallback auf temp
            try:
                export_dir = settings.get_excel_export_directory()
            except Exception:
                export_dir = Path(tempfile.mkdtemp())
            
            output_path = export_dir / f"Auftragsliste_{timestamp}.xlsx"
            
            success = excel_service.export_orders_list(orders, output_path)
            
            if success and output_path.exists():
                logger.info(f"Excel-Export erstellt: {output_path} (von {user['username']})")
                return FileResponse(
                    path=str(output_path),
                    filename=output_path.name,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                return JSONResponse(status_code=500, content={"error": "Excel-Export fehlgeschlagen"})
    
    except Exception as e:
        logger.error(f"Fehler beim Excel-Export: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/export/billing")
async def export_billing_excel(request: Request):
    """Exportiert alle Abrechnungen als Excel-Datei."""
    user, error = _require_auth(request)
    if error:
        return error
    
    try:
        db = _get_db()
        with db.SessionLocal() as session:
            stmt = select(BillingRecord).order_by(BillingRecord.billing_date.desc())
            billings = list(session.scalars(stmt))
            
            if not billings:
                return JSONResponse(status_code=404, content={"error": "Keine Abrechnungen vorhanden"})
            
            excel_service = _get_excel_service()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                export_dir = settings.get_excel_export_directory()
            except Exception:
                export_dir = Path(tempfile.mkdtemp())
            
            output_path = export_dir / f"Abrechnungsliste_{timestamp}.xlsx"
            
            success = excel_service.export_billing_list(billings, output_path)
            
            if success and output_path.exists():
                logger.info(f"Abrechnungs-Export erstellt: {output_path} (von {user['username']})")
                return FileResponse(
                    path=str(output_path),
                    filename=output_path.name,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                return JSONResponse(status_code=500, content={"error": "Excel-Export fehlgeschlagen"})
    
    except Exception as e:
        logger.error(f"Fehler beim Abrechnungs-Export: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/statistics")
async def get_statistics(request: Request):
    """Gibt Statistiken als JSON zurück."""
    user, error = _require_auth(request)
    if error:
        return error
    
    try:
        db = _get_db()
        stats = db.get_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Statistiken: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
