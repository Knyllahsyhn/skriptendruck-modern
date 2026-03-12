# CLI vs. Web-Dashboard – Feature-Vergleich

> Stand: 2026-03-12

## Übersicht

| Feature                            | CLI (`commands.py`)        | Web-Dashboard                  | Status      |
| ---------------------------------- | -------------------------- | ------------------------------ | ----------- |
| **Aufträge verarbeiten**           | `process` (einzeln/batch)  | Starten-Button / Alle starten  | ✅ Parität  |
| **Drucken (SumatraPDF)**          | `--print` Flag             | `ENABLE_PRINTING=true` in .env | ✅ Parität  |
| **Ordnerstruktur initialisieren** | `init`                     | —                              | ❌ Nur CLI  |
| **Datei-Statistik (Orders-Dir)**  | `stats`                    | —                              | ❌ Nur CLI  |
| **Datenbank-Statistiken**         | `db_stats`                 | Statistik-Seite `/statistics`  | ✅ Parität  |
| **Excel-Export (Aufträge)**       | `export_excel`             | Download-Button `/api/export/` | ✅ Parität  |
| **Excel-Export (Abrechnungen)**   | `export_excel`             | Download-Button `/api/export/` | ✅ Parität  |
| **LDAP-Credentials verwalten**    | `credentials setup/check`  | —                              | ❌ Nur CLI  |
| **File-Watcher (auto-scan)**      | — (manuell via CLI)        | Background-Task + Scan-Button  | ✅ Dashboard |
| **Aufträge löschen**              | —                          | Delete-Button                  | ✅ Dashboard |
| **Bulk-Verarbeitung**             | Parallele Pipeline         | „Alle starten" Button          | ✅ Parität  |
| **Login / Authentifizierung**     | — (kein Auth)              | LDAP + Fallback-Admin          | ✅ Dashboard |
| **Dark/Light Mode**               | —                          | Theme-Toggle                   | ✅ Dashboard |

## Empfehlung: Welche CLI-Commands bleiben relevant?

### Weiterhin sinnvoll (nur CLI)
- **`init`** – Erstmalige Einrichtung der Ordnerstruktur & Beispieldaten.
  Wird typischerweise nur 1× bei der Installation benötigt.
- **`credentials setup/check/delete`** – Verwaltung verschlüsselter LDAP-Passwörter.
  Sensible Operation, die nicht über ein Web-Interface exponiert werden sollte.
- **`stats`** – Schnelle Datei-basierte Statistik direkt auf dem Dateisystem
  (ohne DB). Nützlich für Debugging.

### Abgelöst durch Dashboard
- **`process`** → Dashboard „Starten" / „Alle starten"
- **`db_stats`** → Dashboard Statistik-Seite
- **`export_excel`** → Dashboard Excel-Download

### Fazit
Die CLI bleibt als **Setup- und Admin-Werkzeug** relevant (`init`, `credentials`).
Für den täglichen Betrieb (Aufträge verarbeiten, exportieren, Statistiken) ist
das Web-Dashboard die primäre Oberfläche.
