"""FastAPI-Anwendung für das Skriptendruck Web-Dashboard."""
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ..config import get_logger
from .routes.auth_routes import router as auth_router
from .routes.dashboard_routes import router as dashboard_router
from .routes.api_routes import router as api_router

logger = get_logger("web.app")

# Pfade
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def create_app() -> FastAPI:
    """Erstellt und konfiguriert die FastAPI-Anwendung."""
    
    app = FastAPI(
        title="Skriptendruck Dashboard",
        description="Web-Dashboard für die Skriptendruck-Verwaltung der Fachschaft",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    
    # Session Middleware (Secret Key aus .env oder generiert)
    secret_key = os.environ.get("DASHBOARD_SECRET_KEY", secrets.token_hex(32))
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="skriptendruck_session",
        max_age=3600 * 8,  # 8 Stunden
        same_site="lax",
        https_only=False,  # Für lokale Entwicklung; in Prod auf True setzen
    )
    
    # Static Files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    
    # Templates global verfügbar machen
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates
    
    # Router einbinden
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(api_router, prefix="/api")
    
    logger.info("Skriptendruck Web-Dashboard initialisiert")
    
    return app


# Globale App-Instanz für uvicorn
app = create_app()
