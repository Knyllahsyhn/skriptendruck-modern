"""LDAP-Authentifizierung und Session-Management für das Web-Dashboard."""
import os
import ssl
from datetime import datetime
from typing import Optional

from starlette.requests import Request
from starlette.responses import RedirectResponse

from ..config import get_logger, settings

logger = get_logger("web.auth")

# Erlaubte LDAP-Gruppen für Dashboard-Zugriff
ALLOWED_GROUPS = {"M_FB_STUD_FSMB_Dienst_1", "M_FB_STUD_FSMB_Administratoren"}


def get_current_user(request: Request) -> Optional[dict]:
    """Gibt den aktuell eingeloggten User aus der Session zurück."""
    return request.session.get("user")


def require_login(request: Request) -> Optional[RedirectResponse]:
    """Prüft ob ein User eingeloggt ist, redirect zu Login wenn nicht."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authentifiziert einen Benutzer via LDAP oder .env-Fallback.
    
    Returns:
        Dict mit User-Infos oder None bei Fehler.
    """
    # 1. Versuche .env / Umgebungsvariablen Fallback
    env_user = os.environ.get("DASHBOARD_ADMIN_USER", "").strip()
    env_pass = os.environ.get("DASHBOARD_ADMIN_PASSWORD", "").strip()
    
    if env_user and env_pass and username == env_user and password == env_pass:
        logger.info(f"User '{username}' via .env-Fallback authentifiziert")
        return {
            "username": username,
            "display_name": "Administrator",
            "groups": list(ALLOWED_GROUPS),
            "auth_method": "env_fallback",
            "login_time": datetime.now().isoformat(),
        }
    
    # 2. LDAP-Authentifizierung
    if settings.ldap_enabled:
        return _authenticate_ldap(username, password)
    
    # 3. Kein Auth-Backend verfügbar
    logger.warning("Kein Authentifizierungs-Backend verfügbar (LDAP deaktiviert, kein .env-Fallback)")
    return None


def _authenticate_ldap(username: str, password: str) -> Optional[dict]:
    """
    Authentifiziert einen Benutzer gegen das LDAP (Active Directory der HS Regensburg).
    
    Ablauf:
    1. Bind mit dem Service-Account (aus Settings)
    2. Suche den User per sAMAccountName
    3. Re-Bind mit den User-Credentials (Passwort-Prüfung)
    4. Gruppen des Users laden und gegen ALLOWED_GROUPS prüfen
    """
    try:
        from ldap3 import ALL, SUBTREE, Connection, Server, Tls
    except ImportError:
        logger.error("ldap3 nicht installiert – LDAP-Auth nicht verfügbar")
        return None
    
    if not settings.ldap_server or not settings.ldap_base_dn:
        logger.error("LDAP nicht vollständig konfiguriert")
        return None
    
    try:
        # TLS Konfiguration
        tls_config = None
        if settings.ldap_use_ssl:
            try:
                tls_config = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
            except Exception:
                tls_config = Tls(validate=ssl.CERT_NONE)
        
        server = Server(
            settings.ldap_server,
            port=settings.ldap_port,
            use_ssl=settings.ldap_use_ssl,
            tls=tls_config,
            get_info=ALL,
            connect_timeout=10,
        )
        
        # --- Schritt 1: Service-Account Bind ---
        if settings.ldap_bind_dn and settings.ldap_bind_password:
            service_conn = Connection(
                server,
                user=settings.ldap_bind_dn,
                password=settings.ldap_bind_password,
                auto_bind=True,
                raise_exceptions=True,
            )
        else:
            logger.error("LDAP Service-Account nicht konfiguriert")
            return None
        
        # --- Schritt 2: User suchen ---
        raw_filter = settings.ldap_search_filter.format(username=username)
        search_filter = raw_filter if raw_filter.startswith("(") else f"({raw_filter})"
        
        attributes = [
            "givenName", "sn", "mail", "department",
            "samAccountName", "memberOf", "distinguishedName",
        ]
        
        service_conn.search(
            search_base=settings.ldap_base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes,
        )
        
        if not service_conn.entries:
            logger.info(f"LDAP: User '{username}' nicht gefunden")
            service_conn.unbind()
            return None
        
        entry = service_conn.entries[0]
        user_dn = str(entry.entry_dn)
        
        # Attribute extrahieren
        first_name = str(entry.givenName.value) if hasattr(entry, "givenName") and entry.givenName.value else username
        last_name = str(entry.sn.value) if hasattr(entry, "sn") and entry.sn.value else ""
        email = str(entry.mail.value) if hasattr(entry, "mail") and entry.mail.value else ""
        
        # Gruppen extrahieren (memberOf enthält DNs)
        groups = []
        if hasattr(entry, "memberOf") and entry.memberOf.values:
            for group_dn in entry.memberOf.values:
                # CN aus dem DN extrahieren: "CN=Vorstand,OU=..."
                cn = _extract_cn(str(group_dn))
                if cn:
                    groups.append(cn)
        
        service_conn.unbind()
        
        # --- Schritt 3: User-Bind (Passwort prüfen) ---
        try:
            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True,
                raise_exceptions=True,
            )
            user_conn.unbind()
        except Exception as bind_err:
            logger.info(f"LDAP: Falsches Passwort für '{username}': {bind_err}")
            return None
        
        # --- Schritt 4: Gruppen prüfen ---
        user_allowed_groups = [g for g in groups if g in ALLOWED_GROUPS]
        
        if not user_allowed_groups:
            logger.warning(
                f"User '{username}' hat keine der erlaubten Gruppen: "
                f"hat {groups}, braucht eine aus {ALLOWED_GROUPS}"
            )
            return None
        
        display_name = f"{first_name} {last_name}".strip() or username
        
        logger.info(f"User '{username}' erfolgreich via LDAP authentifiziert (Gruppen: {user_allowed_groups})")
        
        return {
            "username": username,
            "display_name": display_name,
            "email": email,
            "groups": user_allowed_groups,
            "all_groups": groups,
            "auth_method": "ldap",
            "login_time": datetime.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"LDAP-Authentifizierung fehlgeschlagen: {e}")
        return None


def _extract_cn(dn: str) -> Optional[str]:
    """Extrahiert den CN (Common Name) aus einem Distinguished Name."""
    for part in dn.split(","):
        part = part.strip()
        if part.upper().startswith("CN="):
            return part[3:]
    return None
