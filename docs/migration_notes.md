# Migration vom MATLAB-System zu Python

## Überblick

Dieses Dokument beschreibt die Unterschiede und Migrationsschritte vom ursprünglichen MATLAB-basierten Skriptendruckprogramm zum neuen Python-System.

## Hauptunterschiede

### 1. Technologie-Stack

**Alt (MATLAB):**
- MATLAB/Octave
- Excel COM Automation
- PDFtk.exe (externes Tool)
- .mat Dateien für Benutzerdaten
- Windows-spezifisch

**Neu (Python):**
- Python 3.11+
- pypdf (native Python)
- reportlab (PDF-Generierung)
- LDAP (dynamische Benutzervalidierung)
- Cross-platform

### 2. Datenspeicherung

#### Benutzerdaten

**Alt:**
```matlab
% ContactsM.mat, ContactsS.mat
load('ContactsM.mat');
```

**Neu:**
- LDAP-Integration (primär)
- CSV-Fallback (optional)
- Kein Vorladen aller Kontakte

#### Migration:
Die `Kontakte.txt` Datei kann in CSV umgewandelt werden:

```bash
# Format: username firstname lastname faculty
# Beispiel aus Kontakte.txt:
# haa37169 Ahmad Harkal M
```

Wenn LDAP aktiviert ist, werden Kontakte automatisch on-the-fly abgefragt.

### 3. Dateinamen-Parsing

#### Unterstützte Formate bleiben gleich:

- `abc12345_sw_mb_001.pdf`
- `def67890_farbig_ob_002.pdf`
- `RZ-Kennung_farbig/sw_mb/ob/sh_000.pdf`

#### Neue Features:
- Robustere Pattern-Erkennung
- Nickname-Mapping eingebaut
- Bessere Fehlerbehandlung

### 4. Preisberechnung

#### Ringbindungsgrößen

**Alt:**
```matlab
maxpagehcs=320;  % Klein
maxpagehcl=600;  % Groß
```

**Neu:**
Detaillierte Tabelle in `data/binding_sizes.json`:

```json
{
  "binding_sizes": [
    {"min_pages": 1, "max_pages": 80, "size_mm": 8, "binding_type": "small"},
    {"min_pages": 81, "max_pages": 120, "size_mm": 10, "binding_type": "small"},
    ...
  ]
}
```

Diese Tabelle muss mit den tatsächlichen Ringbindungsgrößen gefüllt werden!

### 5. Deckblatt-Erstellung

**Alt:**
- Excel-Template + Export als PDF
- COM Automation erforderlich
- Langsam

**Neu:**
- Direkte PDF-Generierung mit reportlab
- Keine Excel-Abhängigkeit
- Schneller
- **WICHTIG**: Das neue Deckblatt hat ein anderes Design als das Excel-basierte

**Anpassungen am Design:**
Siehe `src/skriptendruck/services/pdf_service.py` → `create_coversheet()`

### 6. Error-Handling & Logging

**Alt:**
```matlab
diary([pathProgramm,'\Skriptendruck.log']);
```

**Neu:**
- Strukturiertes Logging mit Python logging
- Rich Console Output mit Farben
- Verschiedene Log-Level
- Optional: Logdatei

### 7. Verzeichnisstruktur

**Alt:**
```
H:\stud\fsmb\03_Dienste\01_Skriptendruck\
├── 01_Auftraege\
├── 01_print_sw\
├── 01_print_farbig\
├── 02_original_Skripte\
├── 05_wrong\
└── ...
```

**Neu:**
```
BASE_PATH/
├── 01_Auftraege/           # Input
├── output/                  # Verarbeitete PDFs
└── [optional weitere]
```

Die alte Ordnerstruktur mit `01_print_sw`, `01_print_farbig`, `05_wrong` etc. wird im neuen System nicht mehr verwendet. Stattdessen werden alle verarbeiteten Dateien im `output/` Verzeichnis gespeichert.

## Migrations-Checkliste

### 1. Vorbereitung

- [ ] Python 3.11+ installieren
- [ ] Poetry installieren
- [ ] Repository klonen
- [ ] Dependencies installieren: `poetry install`

### 2. Konfiguration

- [ ] `.env` Datei aus `.env.example` erstellen
- [ ] Pfade in `.env` anpassen
- [ ] LDAP-Konfiguration eintragen (oder LDAP_ENABLED=false)

### 3. Daten migrieren

- [ ] `Kontakte.txt` → `data/users_fallback.csv` konvertieren (wenn kein LDAP)
- [ ] `blacklist.mat` → `data/blacklist.txt` konvertieren
- [ ] Ringbindungsgrößen-Tabelle ausfüllen: `data/binding_sizes.json`

### 4. Testen

- [ ] `poetry run skriptendruck init-data` ausführen
- [ ] Test-PDFs vorbereiten
- [ ] `poetry run skriptendruck process --orders-dir <test-dir>` ausführen
- [ ] Output prüfen

### 5. Deckblatt anpassen (optional)

- [ ] Design in `pdf_service.py` → `create_coversheet()` anpassen
- [ ] Logo hinzufügen (falls gewünscht)
- [ ] Layout testen

### 6. Produktiv-Betrieb

- [ ] Alte MATLAB-Version sichern
- [ ] Neue Version in Produktionsumgebung deployen
- [ ] Monitoring & Logging einrichten

## LDAP-Konfiguration

### Beispiel für Hochschule Regensburg

```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://ldap.hs-regensburg.de
LDAP_BASE_DN=ou=people,dc=hs-regensburg,dc=de
# Optional: Bind-Credentials wenn erforderlich
# LDAP_BIND_DN=cn=admin,dc=hs-regensburg,dc=de
# LDAP_BIND_PASSWORD=geheim
```

### LDAP-Attribute

Das System erwartet folgende LDAP-Attribute:
- `uid`: RZ-Kennung
- `givenName`: Vorname
- `sn`: Nachname
- `ou`: Fakultät
- `mail`: E-Mail (optional)

Falls eure LDAP-Struktur anders ist, muss `user_service.py` → `_query_ldap()` angepasst werden.

## Bekannte Unterschiede / Einschränkungen

### 1. Kein automatisches Verschieben in Unterordner

Das alte System hat PDFs automatisch in verschiedene Ordner verschoben:
- `01_print_sw/` (Schwarz-Weiß)
- `01_print_farbig/` (Farbe)
- `05_wrong/02_name_not_found/` (Fehler)
- etc.

Das neue System speichert alles in `output/` und markiert Fehler im Status.

**Migration-Option:** Kann bei Bedarf in `moveDocs()` Funktion nachgebaut werden.

### 2. Excel-Listen

Das alte System hat Excel-Listen erstellt:
- `Abrechnungsliste.xlsx`
- `Auftragsliste.xlsx`

**Status:** Noch nicht implementiert in v2.0

**Workaround:** Export-Funktionalität kann später hinzugefügt werden.

### 3. Deckblatt-Design

Das neue Deckblatt sieht anders aus als das Excel-basierte Original.

**Anpassung:** Code in `pdf_service.py` kann angepasst werden, um näher am Original zu sein.

### 4. PDFtk-Features

Das alte System nutzte PDFtk für:
- Seitenzahl auslesen
- PDFs zusammenfügen

Das neue System nutzt pypdf (native Python), was die meisten Features abdeckt, aber bei sehr komplexen PDFs ggf. anders verhält.

## Performance

### Geschwindigkeitsvergleich (Beispiel: 100 PDFs)

**Alt (MATLAB):**
- ~10-15 Minuten (sequenziell)
- Excel COM Automation ist langsam

**Neu (Python):**
- ~2-3 Minuten (parallel, 4 Worker)
- ~5-6 Minuten (sequenziell)

## Troubleshooting

### Problem: LDAP-Verbindung schlägt fehl

```bash
# Test mit deaktiviertem LDAP
LDAP_ENABLED=false poetry run skriptendruck process
```

### Problem: Benutzer werden nicht gefunden

1. CSV-Fallback prüfen: `data/users_fallback.csv`
2. LDAP-Konfiguration prüfen
3. Verbose-Modus: `poetry run skriptendruck process -v`

### Problem: PDFs können nicht gelesen werden

- Passwortgeschützte PDFs werden erkannt und markiert
- Prüfe PDF-Integrität mit: `pypdf`

## Weitere Hilfe

Bei Fragen oder Problemen:
1. Verbose-Modus aktivieren: `--verbose`
2. Logdatei prüfen (wenn konfiguriert)
3. Issue im Repository erstellen
