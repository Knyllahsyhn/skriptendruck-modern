# LDAP-Konfiguration für HS Regensburg

## Wichtige Informationen

Die HS Regensburg nutzt **Active Directory** mit LDAPS (LDAP über SSL).

### Verbindungsdaten

Basierend auf der offiziellen Dokumentation:

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| **URL** | `ldaps://adldap.hs-regensburg.de/` | Vollständige URL |
| **Server** | `adldap.hs-regensburg.de` | Server-Adresse |
| **Port** | `636` | Standard LDAPS-Port |
| **Base DN** | `dc=hs-regensburg,dc=de` | Basis für Suchen |
| **Bind DN** | `abc12345@hs-regensburg.de` | Format: RZ-Kennung@hs-regensburg.de |
| **Search Filter** | `samAccountName=abc12345` | Active Directory verwendet samAccountName |

## .env Konfiguration

Erstelle/bearbeite deine `.env` Datei:

```env
# LDAP aktivieren
LDAP_ENABLED=true

# Server-Konfiguration
LDAP_SERVER=adldap.hs-regensburg.de
LDAP_PORT=636
LDAP_USE_SSL=true

# Base DN
LDAP_BASE_DN=dc=hs-regensburg,dc=de

# Authentifizierung (DEINE Zugangsdaten)
LDAP_BIND_DN=abc12345@hs-regensburg.de
LDAP_BIND_PASSWORD=dein_hochschul_passwort

# Search Filter
LDAP_SEARCH_FILTER=samAccountName={username}
```

## Wichtige Hinweise

### 1. Bind DN Format

**Active Directory** erwartet das Format: `username@domain`

✅ Richtig: `mus43225@hs-regensburg.de`  
❌ Falsch: `cn=mus43225,ou=users,dc=hs-regensburg,dc=de`

### 2. Search Filter

Active Directory nutzt `samAccountName` statt `uid`:

✅ Richtig: `samAccountName=abc12345`  
❌ Falsch: `uid=abc12345`

### 3. SSL/TLS

LDAPS (Port 636) nutzt SSL/TLS automatisch.

### 4. Attribute

Active Directory liefert folgende Attribute:
- `givenName` → Vorname
- `sn` → Nachname (surname)
- `mail` → E-Mail
- `department` → Fakultät/Abteilung
- `samAccountName` → RZ-Kennung

## Test der LDAP-Verbindung

### Manueller Test mit ldapsearch (Linux/Mac)

```bash
ldapsearch -H ldaps://adldap.hs-regensburg.de:636 \
  -D "abc12345@hs-regensburg.de" \
  -W \
  -b "dc=hs-regensburg,dc=de" \
  "samAccountName=abc12345"
```

### Test mit Python (ldap3)

```python
from ldap3 import Server, Connection, ALL

server = Server('adldap.hs-regensburg.de', port=636, use_ssl=True, get_info=ALL)
conn = Connection(
    server, 
    user='abc12345@hs-regensburg.de',
    password='dein_passwort',
    auto_bind=True
)

conn.search(
    search_base='dc=hs-regensburg,dc=de',
    search_filter='(samAccountName=abc12345)',
    attributes=['givenName', 'sn', 'mail', 'department']
)

print(conn.entries)
conn.unbind()
```

### Test mit Skriptendruck

```bash
# LDAP-Tests ausführen
poetry run pytest tests/test_user_service_ldap.py -v

# Oder direkt im Code testen
poetry run python -c "
from skriptendruck.services import UserService
service = UserService()
user = service.get_user('abc12345')  # Deine RZ-Kennung
print(user)
"
```

## Troubleshooting

### Fehler: "Invalid credentials"

**Ursache:** Falsche Bind DN oder Passwort

**Lösung:**
- Prüfe Format: `abc12345@hs-regensburg.de` (nicht vergessen!)
- Prüfe Passwort
- Teste Login im Browser: https://portal.hs-regensburg.de

### Fehler: "Can't connect to LDAP server"

**Ursache:** Server nicht erreichbar oder falsche Konfiguration

**Lösung:**
- Prüfe Server: `adldap.hs-regensburg.de`
- Prüfe Port: `636`
- Prüfe SSL: `LDAP_USE_SSL=true`
- Bist du im Hochschul-Netz? (VPN erforderlich?)

### Fehler: "No such object"

**Ursache:** Falsche Base DN oder Search Filter

**Lösung:**
- Prüfe Base DN: `dc=hs-regensburg,dc=de`
- Prüfe Search Filter: `samAccountName={username}`
- Nicht `uid=` verwenden!

### Benutzer nicht gefunden

**Ursache:** User existiert nicht oder hat keinen LDAP-Zugang

**Lösung:**
- Prüfe ob RZ-Kennung korrekt
- Prüfe ob Account aktiv ist
- Nutze CSV-Fallback temporär

## CSV-Fallback

Falls LDAP nicht funktioniert, kannst du temporär den CSV-Fallback nutzen:

```env
# LDAP deaktivieren
LDAP_ENABLED=false
```

Dann `data/users_fallback.csv` erstellen:
```csv
abc12345 Max Mustermann M
def67890 Lisa Schmidt I
```

## Sicherheitshinweise

⚠️ **WICHTIG:**

1. **Niemals** Zugangsdaten ins Git committen!
2. `.env` ist in `.gitignore` → wird nicht committed
3. Nur `.env.example` mit Platzhaltern committen
4. Verwende ein **Service-Account** für Produktiv-Betrieb (nicht deinen persönlichen Account)

## Produktiv-Betrieb

Für den Produktiv-Betrieb empfohlen:

1. **Service-Account** beantragen bei IT-Abteilung
2. Minimale Rechte vergeben (nur Lesezugriff)
3. Starkes Passwort verwenden
4. Passwort-Rotation einplanen

## Weiterführende Links

- ldap3 Dokumentation: https://ldap3.readthedocs.io/
- Active Directory & LDAP: https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/

## Support

Bei Problemen mit LDAP:
1. Teste mit `--verbose` Flag
2. Prüfe Logs
3. Teste manuelle Verbindung (siehe oben)
4. Kontaktiere IT-Support der Hochschule
