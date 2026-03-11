"""Authentifizierungs-Routen (Login / Logout)."""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from ..auth import authenticate_user, get_current_user
from ...config import get_logger

logger = get_logger("web.routes.auth")

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Zeigt die Login-Seite an."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    templates = request.app.state.templates
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
    })


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    """Verarbeitet den Login-Versuch."""
    user = authenticate_user(username.strip(), password)
    
    if user:
        request.session["user"] = user
        logger.info(f"Login erfolgreich: {username}")
        return RedirectResponse(url="/", status_code=302)
    
    logger.warning(f"Login fehlgeschlagen: {username}")
    templates = request.app.state.templates
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Anmeldung fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.",
    })


@router.get("/logout")
async def logout(request: Request):
    """Loggt den Benutzer aus."""
    username = request.session.get("user", {}).get("username", "unbekannt")
    request.session.clear()
    logger.info(f"Logout: {username}")
    return RedirectResponse(url="/login", status_code=302)
