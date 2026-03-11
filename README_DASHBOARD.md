# Skriptendruck Web-Dashboard

Web-basiertes Dashboard zur Verwaltung von Druckaufträgen der Fachschaft Maschinenbau (OTH Regensburg).

## Features

- **LDAP-Authentifizierung**: Login mit RZ-Kennung (Active Directory der HS Regensburg)
- **Gruppen-basierte Zugriffskontrolle**: Nur Mitglieder der Gruppen *Vorstand*, *IT* oder *Skriptendruck*
- **Auftragsübersicht**: Alle Druckaufträge mit Status, Benutzer, Datum, Kosten
- **Auftrags-Aktionen**: Aufträge freigeben (starten) oder löschen
- **Statistiken**: Umsatz, Aufträge nach Status/Fakultät/Farbmodus/Bindung, offene Rechnungen
- **Excel-Export**: Auftrags- und Abrechnungslisten als `.xlsx` herunterladen
- **Responsive Design**: Funktioniert auf Desktop und Tablet (Bootstrap 5)

## Voraussetzungen

- Python 3.11+
- Installierte Abhängigkeiten (siehe `pyproject.toml`)

## Installation

```bash
# 1. Abhängigkeiten installieren
poetry install
# oder:
pip install fastapi uvicorn[standard] jinja2 python-multipart itsdangerous

# 2. .env konfigurieren (falls noch nicht geschehen)
copy .env.example .env
# Dashboard-spezifische Einstellungen anpassen:
#   DASHBOARD_ADMIN_USER=admin
#   DASHBOARD_ADMIN_PASSWORD=<sicheres_passwort>
#   DASHBOARD_HOST=0.0.0.0
#   DASHBOARD_PORT=8080
```

## Dashboard starten

### Windows (Batch)
```cmd
start_dashboard.bat
```

### Windows (PowerShell)
```powershell
.\start_dashboard.ps1
```

### Manuell
```bash
python -m uvicorn skriptendruck.web.app:app --host 0.0.0.0 --port 8080 --reload --app-dir src
```

Das Dashboard ist dann erreichbar unter: **http://localhost:8080**

## Konfiguration

Alle Einstellungen erfolgen über die `.env`-Datei:

| Variable | Beschreibung | Default |
|---|---|---|
| `DASHBOARD_ADMIN_USER` | Fallback-Admin-Benutzername (wenn LDAP nicht verfügbar) | `admin` |
| `DASHBOARD_ADMIN_PASSWORD` | Fallback-Admin-Passwort | `changeme` |
| `DASHBOARD_HOST` | Server-Host | `0.0.0.0` |
| `DASHBOARD_PORT` | Server-Port | `8080` |
| `DASHBOARD_SECRET_KEY` | Session-Secret (wird auto-generiert wenn nicht gesetzt) | *auto* |
| `LDAP_ENABLED` | LDAP-Authentifizierung aktivieren | `true` |
| `LDAP_SERVER` | LDAP-Server Adresse | `adldap.hs-regensburg.de` |

## Authentifizierung

### LDAP (Primär)
Wenn `LDAP_ENABLED=true`, wird der Benutzer gegen das Active Directory der HS Regensburg authentifiziert:
1. Service-Account sucht den Benutzer per `sAMAccountName`
2. Re-Bind mit den Benutzer-Credentials prüft das Passwort
3. Gruppenmitgliedschaft wird geprüft (mindestens eine aus: Vorstand, IT, Skriptendruck)

### .env-Fallback
Wenn LDAP nicht verfügbar ist, kann ein Admin-Account über die `.env`-Datei konfiguriert werden.

## Projektstruktur

```
src/skriptendruck/web/
├── __init__.py
├── app.py              # FastAPI-App mit Middleware
├── auth.py             # LDAP-Auth + Session-Management
├── routes/
│   ├── auth_routes.py      # Login / Logout
│   ├── dashboard_routes.py # Dashboard, Aufträge, Statistiken
│   └── api_routes.py       # REST-API (Start, Löschen, Export)
├── templates/          # Jinja2 HTML-Templates
│   ├── base.html           # Basis-Layout mit Navigation
│   ├── login.html          # Login-Seite
│   ├── dashboard.html      # Haupt-Dashboard
│   ├── orders.html         # Auftragsübersicht
│   └── statistics.html     # Statistiken
└── static/
    ├── css/dashboard.css   # Custom Styles
    └── js/dashboard.js     # Client-side JavaScript
```

## API-Endpoints

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/` | Dashboard-Übersicht |
| `GET` | `/login` | Login-Seite |
| `POST` | `/login` | Login-Verarbeitung |
| `GET` | `/logout` | Abmelden |
| `GET` | `/orders` | Auftragsübersicht |
| `GET` | `/statistics` | Statistiken |
| `POST` | `/api/orders/{id}/start` | Auftrag freigeben |
| `DELETE` | `/api/orders/{id}` | Auftrag löschen |
| `GET` | `/api/export/orders` | Excel-Export Aufträge |
| `GET` | `/api/export/billing` | Excel-Export Abrechnungen |
| `GET` | `/api/statistics` | Statistiken (JSON) |
| `GET` | `/api/docs` | Swagger API-Dokumentation |

## Technologie-Stack

- **Backend**: FastAPI + Uvicorn
- **Frontend**: Jinja2 Templates + Bootstrap 5.3 + Bootstrap Icons
- **Auth**: LDAP3 (Active Directory) + Starlette Session Middleware
- **Datenbank**: SQLite + SQLAlchemy (bestehende Integration)
- **Export**: XlsxWriter (bestehender Excel-Service)
