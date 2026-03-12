# Skriptendruck Web-Dashboard

**Automatisiertes Druckauftragssystem für die Fachschaft Maschinenbau – OTH Regensburg**

---

## Features

- 📁 **Automatische Dateiüberwachung** – Erkennt neue PDF-Aufträge im Auftragsordner
- 🖨️ **Automatischer Druck** – Integration mit SumatraPDF und PaperCut
- 🔐 **LDAP-Authentifizierung** – Login mit Hochschulkennung
- 📊 **Dashboard** – Übersicht über alle Aufträge und Statistiken
- 💾 **SQLite-Datenbank** – Auftragsverfolgung und Abrechnung
- 🪟 **Windows-Service** – Läuft zuverlässig im Hintergrund

---

## Voraussetzungen

- Windows 10/11 oder Windows Server
- Python 3.11+
- SumatraPDF (für Silent-Print)
- PaperCut Client (optional, für Kostenzuordnung)
- Zugriff auf Netzwerkdrucker

---

## Installation

### 1. Repository klonen

```powershell
git clone https://github.com/YOUR-ORG/skriptendruck.git
cd skriptendruck
```

### 2. Python-Umgebung einrichten

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install poetry
poetry install
```

### 3. Konfiguration

Kopiere `.env.example` nach `.env` und passe die Werte an:

```powershell
copy .env.example .env
notepad .env
```

**Wichtige Einstellungen:**
- `BASE_PATH` – Netzwerkpfad zum Auftragsordner (z.B. `\\\\server\\skripten`)
- `LDAP_SERVER` – LDAP-Server für Authentifizierung
- `PRINTER_SW` – Name des Schwarz-Weiß-Druckers
- `PRINTER_COLOR` – Name des Farbdruckers
- `SUMATRA_PDF_PATH` – Pfad zu SumatraPDF.exe

### 4. Als Windows-Service installieren

```powershell
# Als Administrator ausführen:
.\install_service.ps1 -ServiceUser "skriptendruck-service" -ServicePassword "PASSWORT"
```

Das Dashboard ist dann unter **http://localhost:8080** erreichbar.

---

## Verwendung

1. **Anmelden** mit Hochschulkennung (LDAP)
2. **Dashboard** zeigt ausstehende und verarbeitete Aufträge
3. **Aufträge starten** – Einzeln oder alle auf einmal
4. **Statistiken** – Übersicht über Druckvolumen und Kosten

---

## Projektstruktur

```
skriptendruck/
├── src/skriptendruck/
│   ├── config/          # Einstellungen, Logging
│   ├── database/        # SQLite-Modelle und Service
│   ├── models/          # Datenmodelle (Order, User, Pricing)
│   ├── processing/      # PDF-Verarbeitung
│   ├── services/        # Druck, Excel, PDF
│   └── web/             # FastAPI Dashboard
├── docs/                # Dokumentation
├── data/                # Statische Daten
├── install_service.ps1  # Service-Installation
└── .env.example         # Konfigurationsvorlage
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Service startet nicht | Log prüfen: `logs/service_stderr.log` |
| Drucker nicht gefunden | Druckername in `.env` prüfen, `Get-Printer` ausführen |
| LDAP-Login fehlgeschlagen | LDAP-Server und Basis-DN in `.env` prüfen |
| Aufträge werden nicht erkannt | `BASE_PATH` prüfen, Ordnerstruktur vorhanden? |

---

## Dokumentation

- [Windows Service Setup](docs/WINDOWS_SERVICE_SETUP.md)
- [PaperCut Setup](docs/PAPERCUT_SETUP.md)

---

## Lizenz

© 2026 Fachschaft Maschinenbau – OTH Regensburg
