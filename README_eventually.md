# Skriptendruck 2.3

Modernisiertes Druckauftrags-Verwaltungssystem für die Fachschaft Maschinenbau, Hochschule Regensburg.
Python-Neuentwicklung des ursprünglichen MATLAB-Systems mit LDAP-Integration, automatischer Preisberechnung,
Deckblatterstellung und Ordnerverwaltung.

## Features

- **LDAP-Integration**: Benutzervalidierung über das Active Directory der HS Regensburg (ldap3, Windows-kompatibel)
- **Automatische Ordnerverwaltung**: Aufträge werden in `02_Druckfertig/sw/` bzw. `farbig/` sortiert, Fehler nach Grund
  in `04_Fehler/`, Originale gesichert
- **Ringbindungsgrößen**: 13-stufige Tabelle (6,9 mm bis 38 mm) mit automatischer Auswahl nach Seitenzahl
- **Deckblatt mit Vorschau**: Generiertes Deckblatt mit Thumbnail der ersten Dokumentseite
- **SQLite-Datenbank**: Persistente Speicherung aller Aufträge und Abrechnungen
- **Excel-Export**: Auftrags- und Abrechnungslisten auf Knopfdruck
- **Parallele Verarbeitung**: Mehrere PDFs gleichzeitig verarbeiten
- **Rich CLI**: Farbige Ausgabe mit Progress-Bars

## Voraussetzungen

- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Installation

```bash
git clone <repo-url>
cd skriptendruck-modern
poetry install
```

## Schnellstart

```bash
# 1. Ordnerstruktur und Beispieldaten erstellen
poetry run skriptendruck init

# 2. Konfiguration anpassen
cp .env.example .env
# .env editieren: BASE_PATH, LDAP-Daten, EXCEL_EXPORT_PATH

# 3. Aufträge verarbeiten
poetry run skriptendruck process
```

## Konfiguration

Alle Einstellungen werden über die `.env`-Datei gesteuert:

```env
# Basispfad – hier liegt die Ordnerstruktur
BASE_PATH=H:/stud/fsmb/03_Dienste/01_Skriptendruck

# LDAP (auf false setzen zum Testen ohne LDAP)
LDAP_ENABLED=true
LDAP_SERVER=adldap.hs-regensburg.de
LDAP_BASE_DN=dc=hs-regensburg,dc=de
LDAP_BIND_DN=abc12345@hs-regensburg.de
LDAP_BIND_PASSWORD=dein_passwort

# Excel-Export (eigener Pfad, unabhängig von BASE_PATH)
EXCEL_EXPORT_PATH=H:/stud/fsmb/03_Dienste/01_Skriptendruck/Export

# Preise
PRICE_SW=0.04
PRICE_COLOR=0.10
PRICE_BINDING_SMALL=1.00
PRICE_BINDING_LARGE=1.50
PRICE_FOLDER=0.50
```

Ohne LDAP kann eine CSV-Fallback-Datei genutzt werden (`data/users_fallback.csv`):

```
mus43225 Sebastian Müllner M
abc12345 Max Mustermann I
```

## Ordnerstruktur

`skriptendruck init` erstellt folgende Struktur unter `BASE_PATH`:

```
BASE_PATH/
├── 01_Auftraege/                  ← PDFs hier reinlegen
├── 02_Druckfertig/
│   ├── sw/                        ← Schwarz-Weiß-Aufträge mit Deckblatt
│   │   └── gedruckt/              ← Nach dem Drucken hierhin schieben
│   └── farbig/                    ← Farbaufträge mit Deckblatt
│       └── gedruckt/              ← Nach dem Drucken hierhin schieben
├── 03_Originale/                  ← Automatisches Backup der Eingabe-PDFs
│   └── 2026-01-16_12-38/          ← Zeitstempel pro Verarbeitungslauf
├── 04_Fehler/
│   ├── benutzer_nicht_gefunden/
│   ├── gesperrt/
│   ├── zu_wenig_seiten/
│   ├── zu_viele_seiten/
│   ├── passwortgeschuetzt/
│   └── sonstige/
└── 05_Manuell/                    ← Für manuelle Aufträge
```

## Dateinamen-Format

PDFs im Auftragsordner müssen folgendem Schema folgen:

```
<RZ-Kennung>_<Farbmodus>_<Bindung>_<Nummer>.pdf
```

**Beispiele:**

- `mus43225_sw_mb_001.pdf` – Schwarz-Weiß, mit Bindung
- `abc12345_farbig_ob_002.pdf` – Farbe, ohne Bindung
- `def67890_sw_sh_001.pdf` – Schwarz-Weiß, Schnellhefter

Viele Schreibvarianten werden erkannt (`schwarzweiß`, `farbe`, `mitBindung`, `ohneBindung`, `Schnellhefter`, usw.).

## CLI-Befehle

### Aufträge verarbeiten

```bash
poetry run skriptendruck process
```

Was passiert:

1. PDFs aus `01_Auftraege/` einlesen
2. Dateinamen parsen (Benutzer, Farbmodus, Bindung)
3. Benutzer per LDAP/CSV validieren
4. PDF analysieren (Seitenzahl, Passwortschutz)
5. Preis berechnen inkl. Ringbindungsgröße
6. Deckblatt mit Vorschau erstellen
7. Deckblatt + leere Seite + Dokument zusammenfügen
8. Ergebnis nach `02_Druckfertig/sw/` oder `farbig/` verschieben
9. Fehlerhafte Aufträge nach `04_Fehler/<Grund>/`
10. Originale nach `03_Originale/<Zeitstempel>/` sichern
11. In Datenbank speichern

**Optionen:**

```bash
--verbose / -v         Ausführliche Ausgabe (Debug)
--sequential           Sequenzielle statt parallele Verarbeitung
--no-organize          Dateien nicht in Ordnerstruktur verschieben
-i /pfad/zu/ordner     Anderes Auftragsverzeichnis verwenden
```

### Initialisierung

```bash
poetry run skriptendruck init
```

Erstellt die komplette Ordnerstruktur und Beispieldateien (`binding_sizes.json`, `blacklist.txt`, `users_fallback.csv`,
`.env.example`).

### Statistiken

```bash
# Dateisystem-Statistiken (Auftragsordner)
poetry run skriptendruck stats

# Datenbank-Statistiken
poetry run skriptendruck db-stats
```

### Excel-Export

```bash
# Letzte 30 Tage (Standard)
poetry run skriptendruck export-excel

# Eigener Zeitraum
poetry run skriptendruck export-excel --days 60

# Eigenes Ausgabeverzeichnis
poetry run skriptendruck export-excel -o /pfad/zu/export
```

Erstellt `Auftragsliste_YYYYMMDD.xlsx` und `Abrechnungsliste_YYYYMMDD.xlsx` im konfigurierten `EXCEL_EXPORT_PATH`.

## Ringbindungsgrößen

Die Tabelle in `data/binding_sizes.json` enthält die echten Werte:

| Ø mm | Seiten  | Bindung        |
|------|---------|----------------|
| 6,9  | 1–80    | klein (1,00 €) |
| 8,0  | 81–100  | klein          |
| 9,5  | 101–120 | klein          |
| 11,0 | 121–150 | klein          |
| 12,7 | 151–180 | klein          |
| 14,3 | 181–210 | klein          |
| 16,0 | 211–240 | klein          |
| 19,0 | 241–300 | klein          |
| 22,0 | 301–360 | groß (1,50 €)  |
| 25,4 | 361–420 | groß           |
| 28,5 | 421–480 | groß           |
| 32,0 | 481–540 | groß           |
| 38,0 | 541–660 | groß           |

## Projektstruktur

```
src/skriptendruck/
├── config/                  Konfiguration & Logging
│   ├── settings.py          Pydantic Settings (.env)
│   └── logging.py           Rich Logging
├── models/                  Datenmodelle
│   ├── user.py              User (RZ-Kennung, Name, Fakultät)
│   ├── order.py             Order (Auftrag mit Status)
│   └── pricing.py           Pricing, BindingSize, ColorMode
├── services/                Business Logic
│   ├── filename_parser.py   Dateinamen-Parsing
│   ├── user_service.py      LDAP + CSV-Fallback
│   ├── pricing_service.py   Preisberechnung
│   ├── pdf_service.py       PDF-Verarbeitung + Deckblatt + Thumbnail
│   ├── file_organizer.py    Ordnerstruktur + Dateiverschiebung
│   └── excel_service.py     Excel-Export
├── database/                SQLAlchemy
│   ├── models.py            DB-Modelle (OrderRecord, BillingRecord)
│   └── service.py           DB-Operationen
├── processing/
│   └── pipeline.py          Verarbeitungs-Pipeline
└── cli/
    └── commands.py          Typer CLI
```

## Tests

```bash
# Alle Tests
poetry run pytest

# Mit Coverage
poetry run pytest --cov

# Einzelne Testdatei
poetry run pytest tests/test_file_organizer.py -v
```

## Entwicklung

```bash
# Formatierung
poetry run black src tests

# Linting
poetry run ruff check src tests

# Type-Checking
poetry run mypy src
```

## Migration vom MATLAB-System

Siehe [docs/migration_notes.md](docs/migration_notes.md) für Details. Die wichtigsten Unterschiede:

- `01_print_sw` / `01_print_farbig` → `02_Druckfertig/sw/` / `farbig/`
- `05_wrong/02_name_not_found` etc. → `04_Fehler/benutzer_nicht_gefunden/` etc.
- `02_original_Skripte` → `03_Originale/`
- Kein pdftk.exe mehr nötig – alles native Python
- Kein Excel COM mehr – direkte PDF-Generierung mit reportlab
- Kontakte.mat → LDAP oder CSV-Fallback

## Lizenz

GPLv3

## Autoren

<<<<<<< HEAD:README_eventually.md
## 🐛 Fehlersuche

### LDAP-Probleme

```bash
# LDAP deaktivieren und CSV verwenden
LDAP_ENABLED=false poetry run skriptendruck process
```

### Verbose-Modus für Debug-Infos

```bash
poetry run skriptendruck process --verbose
```

### Logdatei erstellen

```env
# In .env
LOG_FILE=skriptendruck.log
```

## 📄 Migration vom alten System

Siehe [docs/migration_notes.md](docs/migration_notes.md) für Details zur Migration.

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Öffne einen Pull Request

## 📝 Lizenz

GPLV3

## 👥 Autoren

- Original MATLAB Version: Sebastian Müllner
- Python Modernisierung: Johannes Müller

## 🙏 Danksagungen

- Fachschaft Maschinenbau
- Hochschule Regensburg
=======
- Original MATLAB-Version: Sebastian Müllner
- Python-Modernisierung: Johannes Müller
>>>>>>> new_folder_structure:README.md
