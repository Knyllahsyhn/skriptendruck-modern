# Windows-Installation & Datenbank-Guide

## Windows-Installation

### 1. Python installieren

```powershell
# Python 3.11+ von python.org herunterladen
# https://www.python.org/downloads/windows/

# Bei Installation "Add Python to PATH" aktivieren!
```

### 2. Poetry installieren

```powershell
# PowerShell als Administrator öffnen
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Poetry zum PATH hinzufügen (in aktueller Session):
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### 3. Projekt einrichten

```powershell
cd skriptendruck
poetry install
```

### 4. LDAP unter Windows

**Wichtig**: Das Projekt nutzt jetzt `ldap3` statt `python-ldap`:
- ✅ `ldap3` ist **Pure Python** und funktioniert problemlos unter Windows
- ❌ `python-ldap` benötigt C-Compiler und ist unter Windows kompliziert

## Datenbank

### SQLite Datenbank

Das System nutzt SQLite für die Datenspeicherung:

**Vorteile:**
- ✅ Keine separate Datenbank-Installation nötig
- ✅ Datei-basiert (`skriptendruck.db`)
- ✅ Schnell und zuverlässig
- ✅ Perfekt für Single-User Anwendungen

**Speicherort:**
- Standard: `BASE_PATH/skriptendruck.db`
- Konfigurierbar über `.env`

### Datenbank-Struktur

#### Tabelle: `orders`
Speichert alle Druckaufträge:
- Order-ID, Dateiname
- Benutzer-Informationen (Username, Name, Fakultät)
- PDF-Informationen (Seiten, Farbmodus, Bindung)
- Preisberechnung
- Status und Fehlermeldungen
- Zeitstempel
- Dateipfade

#### Tabelle: `billing`
Speichert Abrechnungsdaten:
- Verknüpfung zu Order
- Benutzer-Informationen
- Beträge (Total, Anzahlung, Restbetrag)
- Bezahlt-Status
- Notizen

### Datenbank-Befehle

#### Statistiken anzeigen
```bash
poetry run skriptendruck db-stats
```

#### Excel-Export erstellen
```bash
# Letzte 30 Tage
poetry run skriptendruck export-excel

# Eigener Zeitraum
poetry run skriptendruck export-excel --days 60

# Eigenes Ausgabeverzeichnis
poetry run skriptendruck export-excel --output-dir C:\Export
```

## Excel-Export

### Auftragsliste
Enthält alle verarbeiteten Aufträge mit:
- Auftrags-ID und Datum
- Dateiname
- Benutzer-Informationen
- PDF-Details (Seiten, Farbmodus, Bindung)
- Preisberechnung
- Status
- Bearbeiter

**Features:**
- Farbige Formatierung
- Autofilter
- Deutsche Zahlenformate (1,50 € statt 1.50)

### Abrechnungsliste
Enthält offene Abrechnungen mit:
- Abrechnung s-ID und Auftrags-ID
- Benutzer-Informationen
- Beträge (Gesamtbetrag, Anzahlung, Restbetrag)
- Bezahlt-Status (farblich markiert)
- Summen am Ende

**Features:**
- Grün: Bezahlt
- Rot: Unbezahlt
- Automatische Summenberechnung

## Workflow mit Datenbank

### 1. Aufträge verarbeiten
```bash
poetry run skriptendruck process
```
→ Aufträge werden automatisch in Datenbank gespeichert

### 2. Statistiken prüfen
```bash
poetry run skriptendruck db-stats
```

### 3. Excel-Listen erstellen
```bash
poetry run skriptendruck export-excel
```

### 4. Excel-Dateien an Buchhaltung weitergeben
- `Auftragsliste_YYYYMMDD.xlsx`: Alle Aufträge
- `Abrechnungsliste_YYYYMMDD.xlsx`: Offene Zahlungen

## Konfiguration

### .env Datei
```env
# Datenbank
DATABASE_PATH=skriptendruck.db
USE_DATABASE=true

# LDAP (Windows-kompatibel mit ldap3)
LDAP_ENABLED=true
LDAP_SERVER=ldap://ldap.hs-regensburg.de
LDAP_BASE_DN=ou=people,dc=hs-regensburg,dc=de
```

## Datenbank-Backup

### Backup erstellen
```powershell
# Einfach die DB-Datei kopieren
Copy-Item skriptendruck.db skriptendruck_backup_$(Get-Date -Format 'yyyyMMdd').db
```

### Backup wiederherstellen
```powershell
# DB-Datei ersetzen
Copy-Item skriptendruck_backup_20241128.db skriptendruck.db
```

## Migration von Excel zu Datenbank

Falls du bereits Excel-Listen hast:

1. **Alte Daten bleiben erhalten**: Die Datenbank ist zusätzlich
2. **Excel-Export**: Erstelle jederzeit Excel-Dateien aus der Datenbank
3. **Keine Datenverluste**: Alle Informationen aus dem alten System bleiben verfügbar

## Vorteile Datenbank vs. nur Excel

| Aspekt | Nur Excel | Mit Datenbank |
|--------|-----------|---------------|
| **Performance** | Langsam bei >1000 Zeilen | Schnell, auch bei 100.000+ Einträgen |
| **Suche** | Manuell | SQL-basiert, sehr schnell |
| **Integrität** | Keine Prüfung | Automatische Validierung |
| **Gleichzeitiger Zugriff** | Problematisch | Möglich |
| **Backup** | Ganze Datei | Inkrementell möglich |
| **Historien** | Manuell | Automatisch |
| **Export** | Ist das Format | Jederzeit Excel-Export |

## Troubleshooting

### LDAP-Fehler unter Windows
```bash
# ldap3 neu installieren
poetry remove ldap3
poetry add ldap3
```

### Datenbank gesperrt
```bash
# Alle Programme schließen die auf die DB zugreifen
# Ggf. DB-Datei löschen (Achtung: Datenverlust!)
```

### Excel-Export funktioniert nicht
```bash
# xlsxwriter neu installieren
poetry install --sync
```

## Best Practices

1. **Regelmäßige Backups**: DB-Datei täglich sichern
2. **Excel-Export**: Wöchentlich für Archivierung
3. **Statistiken**: Monatlich für Reporting
4. **Logs prüfen**: Bei Fehlern `--verbose` nutzen

## Weiterführende Infos

- SQLite Dokumentation: https://www.sqlite.org/
- ldap3 Dokumentation: https://ldap3.readthedocs.io/
- Poetry Dokumentation: https://python-poetry.org/
