# Quick Start Guide

## 5-Minuten Schnellstart

### 1. Installation (2 Minuten)

```bash
# Repository klonen
git clone <your-repo-url>
cd skriptendruck

# Dependencies installieren
poetry install
```

### 2. Konfiguration (2 Minuten)

```bash
# Beispieldaten initialisieren
poetry run skriptendruck init-data

# .env erstellen
cp .env.example .env

# .env editieren (wichtigste Einstellungen):
# - BASE_PATH: Pfad zu deinem Skriptendruck-Verzeichnis
# - LDAP_ENABLED: true/false je nachdem ob LDAP verfügbar
```

**Minimale .env für Start ohne LDAP:**
```env
BASE_PATH=/pfad/zu/skriptendruck
ORDERS_PATH=01_Auftraege
OUTPUT_PATH=output
LDAP_ENABLED=false
```

### 3. Erste Verwendung (1 Minute)

```bash
# Test: Hilfe anzeigen
poetry run skriptendruck --help

# Test: Statistik
poetry run skriptendruck stats --orders-dir /pfad/zu/test/pdfs

# Echte Verarbeitung
poetry run skriptendruck process --orders-dir /pfad/zu/auftraegen
```

## Testdaten erstellen

Erstelle Test-PDFs mit korrekten Namen:

```bash
# Format: username_farbmodus_bindung_nummer.pdf
# Beispiele:
test123_sw_mb_001.pdf        # Schwarz-Weiß mit Bindung
test123_farbig_ob_001.pdf    # Farbe ohne Bindung
test123_sw_sh_001.pdf        # Schwarz-Weiß Schnellhefter
```

## Ohne LDAP testen

1. CSV erstellen: `data/users_fallback.csv`
```
test123 Max Mustermann M
abc456 Lisa Schmidt I
```

2. In .env setzen:
```env
LDAP_ENABLED=false
```

## Mit LDAP testen

1. In .env setzen:
```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://dein-ldap-server.de
LDAP_BASE_DN=ou=people,dc=example,dc=de
```

2. Test mit echten RZ-Kennungen

## Häufigste Probleme

### "User not found"
- CSV-Fallback prüfen: `data/users_fallback.csv`
- LDAP-Konfiguration prüfen
- Verbose-Modus: `--verbose`

### "Directory not found"
- Pfade in .env prüfen
- `--orders-dir` Option nutzen

### "LDAP connection failed"
- LDAP temporär deaktivieren: `LDAP_ENABLED=false`
- Server-URL prüfen

## Nächste Schritte

1. ✅ Quick Start abgeschlossen
2. 📖 README.md lesen für Details
3. ⚙️ Ringbindungsgrößen in `data/binding_sizes.json` anpassen
4. 🚀 Produktiv nutzen!

## Weitere Befehle

```bash
# Ausführliche Ausgabe
poetry run skriptendruck process --verbose

# Eigene Verzeichnisse
poetry run skriptendruck process \
    --orders-dir /custom/input \
    --output-dir /custom/output

# Sequenziell statt parallel
poetry run skriptendruck process --sequential

# Tests ausführen
poetry run pytest

# Code-Qualität prüfen
poetry run black src tests
poetry run ruff check src
```

## Support

- 📖 Dokumentation: `README.md`
- 🔄 Migration: `docs/migration_notes.md`
- 📝 Zusammenfassung: `ZUSAMMENFASSUNG.md`
- 🐛 Issues: [GitHub Issues]
