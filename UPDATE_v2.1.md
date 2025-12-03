# Update v2.1 - Windows & Datenbank Support

## 🎉 Neue Features

### 1. ✅ **Vollständige Windows-Kompatibilität**

**Problem gelöst:**
- ❌ `python-ldap` benötigt C-Compiler unter Windows (kompliziert!)
- ✅ Jetzt `ldap3` - Pure Python, funktioniert out-of-the-box

**Änderungen:**
- `pyproject.toml`: `python-ldap` → `ldap3`
- `user_service.py`: Umgeschrieben für ldap3-API
- Getestet unter Windows 10/11

### 2. ✅ **SQLite Datenbank statt nur Excel**

**Neue Datenbank-Struktur:**
- **orders** Tabelle: Alle Druckaufträge mit vollständigen Details
- **billing** Tabelle: Abrechnungsdatensätze für erfolgreiche Aufträge

**Vorteile:**
- 📊 Historische Daten bleiben erhalten
- 🔍 Schnelle Suche und Filterung
- 📈 Statistiken und Reporting
- 💾 Automatische Backups möglich

**Dateien:**
- `src/skriptendruck/database/models.py` - SQLAlchemy Models
- `src/skriptendruck/database/service.py` - Datenbank-Service
- Datenbank-Datei: `skriptendruck.db` (SQLite)

### 3. ✅ **Excel-Export on Demand**

**Statt** nur Excel-Dateien **jetzt** Datenbank + Excel-Export:

```bash
# Auftrags- und Abrechnungslisten erstellen
poetry run skriptendruck export-excel
```

**Generierte Dateien:**
- `Auftragsliste_YYYYMMDD.xlsx`: Alle Aufträge
- `Abrechnungsliste_YYYYMMDD.xlsx`: Offene Abrechnungen

**Features:**
- Farbige Formatierung (Bezahlt = Grün, Unbezahlt = Rot)
- Autofilter aktiviert
- Deutsche Zahlenformate (1,50 € statt 1.50)
- Automatische Summenberechnung
- Anpassbare Zeiträume (--days Parameter)

**Datei:**
- `src/skriptendruck/services/excel_service.py` - Excel-Export Service

### 4. ✅ **Neue CLI-Befehle**

#### Datenbank-Statistiken
```bash
poetry run skriptendruck db-stats
```
Zeigt:
- Gesamt-Aufträge
- Erfolgreiche/Fehlerhafte Aufträge
- Gesamtumsatz

#### Excel-Export
```bash
# Standard (30 Tage)
poetry run skriptendruck export-excel

# Custom
poetry run skriptendruck export-excel --days 60 --output-dir C:\Export
```

### 5. ✅ **Automatische Persistierung**

- Alle verarbeiteten Aufträge werden automatisch in DB gespeichert
- Abrechnungsdatensätze werden automatisch erstellt
- Integration in bestehende Pipeline

## 📁 Neue Dateien

```
src/skriptendruck/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy Models (OrderRecord, BillingRecord)
│   └── service.py         # DatabaseService
└── services/
    └── excel_service.py   # ExcelExportService

docs/
└── WINDOWS_DATABASE.md    # Ausführliche Dokumentation
```

## 🔄 Geänderte Dateien

- `pyproject.toml`: ldap3, sqlalchemy, xlsxwriter hinzugefügt
- `user_service.py`: LDAP-Code auf ldap3 umgestellt
- `processing/pipeline.py`: Datenbank-Integration
- `cli/commands.py`: Neue Commands (export-excel, db-stats)
- `config/settings.py`: Datenbank-Einstellungen
- `README.md`: Aktualisiert mit neuen Features

## 📊 Datenbankschema

### Table: orders
- **id**: Primary Key
- **order_id**: Auftrags-ID (unique)
- **filename**: Dateiname
- **username, first_name, last_name, faculty**: Benutzer-Infos
- **page_count, color_mode, binding_type**: PDF-Details
- **prices**: Alle Preisberechnungen
- **status**: Auftragsstatus
- **timestamps**: created_at, processed_at
- **paths**: Dateipfade zu PDFs

### Table: billing
- **id**: Primary Key
- **order_id**: Verknüpfung zu Auftrag
- **username, full_name**: Benutzer
- **total_amount, paid_deposit, remaining_amount**: Beträge
- **is_paid, paid_at**: Bezahlt-Status
- **notes**: Zusatzinformationen

## 🚀 Migration von v2.0 zu v2.1

### Schritt 1: Dependencies aktualisieren
```bash
cd skriptendruck
poetry install
```

### Schritt 2: .env anpassen (optional)
```env
# Neu:
DATABASE_PATH=skriptendruck.db
USE_DATABASE=true
```

### Schritt 3: Erste Verwendung
```bash
# Datenbank wird automatisch initialisiert
poetry run skriptendruck process

# Statistiken prüfen
poetry run skriptendruck db-stats

# Excel-Export testen
poetry run skriptendruck export-excel
```

### Schritt 4: Alte Excel-Dateien (optional)
- Behalte alte Excel-Dateien als Backup
- Neue Excel-Dateien werden aus Datenbank generiert
- Kein Datenverlust, nur neues System parallel

## 🎯 Vorteile zusammengefasst

| Feature | v2.0 | v2.1 |
|---------|------|------|
| **Windows** | ⚠️ Problematisch (python-ldap) | ✅ Funktioniert (ldap3) |
| **Datenspeicherung** | ❌ Keine | ✅ SQLite Datenbank |
| **Historische Daten** | ❌ Nein | ✅ Ja, dauerhaft |
| **Excel-Listen** | ❌ Geplant | ✅ On-demand Export |
| **Statistiken** | ⚠️ Nur Dateisystem | ✅ DB-basiert + Dateisystem |
| **Suche/Filter** | ❌ Keine | ✅ SQL-basiert |
| **Reporting** | ❌ Manuell | ✅ Automatisiert |

## 📚 Neue Dokumentation

- `docs/WINDOWS_DATABASE.md`: Ausführliche Anleitung
  - Windows-Installation
  - LDAP-Konfiguration
  - Datenbank-Nutzung
  - Excel-Export
  - Backup-Strategien

## ⚠️ Breaking Changes

**Keine!** Alle v2.0 Features bleiben erhalten:
- ✅ Alle bestehenden CLI-Commands funktionieren
- ✅ Konfiguration abwärtskompatibel
- ✅ Optional: Datenbank kann deaktiviert werden

## 🐛 Bekannte Einschränkungen (behoben)

v2.0:
- ❌ LDAP unter Windows kompliziert
- ❌ Keine Datenspeicherung
- ❌ Kein Excel-Export

v2.1:
- ✅ Alle behoben!

## 🎓 Empfohlener Workflow

1. **Aufträge verarbeiten**:
   ```bash
   poetry run skriptendruck process
   ```
   → Speichert automatisch in Datenbank

2. **Statistiken prüfen**:
   ```bash
   poetry run skriptendruck db-stats
   ```

3. **Wöchentlich: Excel-Export**:
   ```bash
   poetry run skriptendruck export-excel --days 7
   ```

4. **Monatlich: Vollständiger Export**:
   ```bash
   poetry run skriptendruck export-excel --days 30
   ```

5. **Datenbank-Backup** (täglich):
   ```bash
   cp skriptendruck.db backup/skriptendruck_$(date +%Y%m%d).db
   ```

## 📦 Download

**Version 2.1** - Windows & Datenbank Support  
**Größe**: ~51 KB  
**Neue Dateien**: 4  
**Geänderte Dateien**: 6

---

**Status**: ✅ Production Ready  
**Version**: 2.1.0  
**Datum**: November 2024  
**Windows-kompatibel**: ✅ Ja  
**Datenbank**: ✅ SQLite integriert  
**Excel-Export**: ✅ Implementiert
