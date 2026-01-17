## MINIFORUM - Ressourcenschonende Forum-Webanwendung für eingebettete Systeme

Dies ist eine leichtgewichtige Forum-Anwendung, speziell optimiert für extrem
ressourcenbeschränkte Hardware wie OpenWRT-Router. Die Anwendung läuft mit
weniger als 50MB RAM und unterstützt 10-20 gleichzeitige Benutzer.

===================================================
DESIGN-PHILOSOPHIE UND ARCHITEKTUR
===================================================

KISS-Prinzip (Keep It Simple, Stupid)
--------------------------------------
Die Anwendung folgt dem KISS-Prinzip für maximale Effizienz:
- Minimaler Code-Overhead
- Keine unnötigen Abhängigkeiten
- Klare Trennung der Aufgabenbereiche
- Einfache Wartbarkeit

Ressourcenoptimierung für OpenWRT
----------------------------------
- SQLite statt MySQL (kein separater Prozess, ~250KB vs mehrere MB)
- Flask statt Django (50KB vs 20MB Overhead)
- Client-seitige Sessions statt serverseitiger Speicherung
- Aggressives Caching für Datenbank-Entlastung
- Soft-Delete statt Hard-Delete (Performance & Datenintegrität)

Modulare Architektur
--------------------
- Flask Blueprints für klare Trennung der Funktionalitäten
- MVC-Pattern (Model-View-Controller)
- Wiederverwendbare Komponenten
- Erweiterbarkeit für zukünftige Features

===================================================
DATEISTRUKTUR UND AUFGABENBEREICHE
===================================================

Hauptverzeichnis:
-----------------
config.py              - Zentrale Konfiguration (Development/Production)
requirements.txt       - Python-Abhängigkeiten
run.py                 - Anwendungs-Entry-Point
readme.txt            - Diese Dokumentationsdatei

app/ (Hauptanwendung)
---------------------
__init__.py           - Flask-App Factory & Extension-Initialisierung
models/               - Datenbank-Models (SQLAlchemy ORM)
views/                - Flask Blueprints (Controller)
templates/            - Jinja2 Templates (View)
static/               - CSS, minimales JS, Icons, Uploads
utils/                - Hilfsfunktionen und Decorators

Model-Dateien (app/models/):
----------------------------
__init__.py           - Model-Imports und Exports
user.py              - Benutzerverwaltung und Authentifizierung
category.py          - Forum-Kategorien und Hierarchie
thread.py            - Diskussionsthemen (Threads)
post.py              - Beiträge und Antworten
message.py           - Private Nachrichten

===================================================
DETAILLIERTE DATEI-ERKLÄRUNGEN
===================================================

config.py
---------
ZWECK: Zentrale Konfigurationsverwaltung für alle Umgebungen

DESIGN-ENTSCHEIDUNGEN:
- Drei Umgebungen: Development, Production, Testing
- Umgebungsvariablen für sensitive Daten (SECRET_KEY, DATABASE_URL)
- SQLite-Optimierung für OpenWRT: cache=shared&mode=rwc
- Unterschiedliche Rate-Limits: Development (100/min) vs Production (30/min)
- Gunicorn-Einstellungen speziell für eingebettete Systeme:
  - Nur 2 Worker (statt 4-8 bei normalen Servern)
  - 1 Thread pro Worker (weniger Speicher)
  - sync-Worker (einfach, zuverlässig)
  - Worker-Restart nach 1000 Requests (Speicherbereinigung)

PERFORMANCE-OPTIMIERUNGEN:
- CACHE_TYPE = 'SimpleCache' (Memory-basiert, kein Redis nötig)
- CACHE_DEFAULT_TIMEOUT = 600 Sekunden (10 Minuten)
- SESSION_TYPE = 'filesystem' (kein Server-Speicher)
- Minimal Logging in Production (LOG_LEVEL = 'WARNING')

SICHERHEIT:
- CSRF-Schutz aktiviert (WTF_CSRF_ENABLED = True)
- Secure Cookies in Production (SESSION_COOKIE_SECURE = True)
- HttpOnly Cookies (SESSION_COOKIE_HTTPONLY = True)

app/__init__.py
---------------
ZWECK: Flask-Application Factory und Extension-Initialisierung

DESIGN-ENTSCHEIDUNGEN:
- Factory-Pattern für flexible App-Erstellung
- Lazy Loading der Extensions
- Blueprint-Registrierung für modulare Struktur
- Performance-Monitoring für langsame Queries (>100ms)

PERFORMANCE-FEATURES:
- Slow Query Logging in Development
- Cache-Initialisierung für alle Models
- Rate-Limiter für alle Endpunkte
- Session-Management mit minimal Overhead

SICHERHEIT:
- Error Handler für 404/500
- Datenbank-Rollback bei Fehlern
- Login-Manager Konfiguration

app/models/user.py
------------------
ZWECK: Benutzerverwaltung, Authentifizierung, Profile

DESIGN-ENTSCHEIDUNGEN:
- UserMixin von Flask-Login für Session-Management
- Bcrypt für Passwort-Hashing (sicher, OpenWRT-kompatibel)
- Geo-Koordinaten (latitude, longitude) für zukünftige Karten-Integration
- Avatar-Feld für Profilbilder (optional)
- Soft-Delete statt Hard-Delete (Performance & Recovery)

PERFORMANCE-OPTIMIERUNGEN:
- Aggressives Caching aller Count-Methoden:
  - get_post_count() - 10 Minuten Cache
  - get_thread_count() - 10 Minuten Cache
  - get_unread_message_count() - 1 Minute Cache
- Datenbank-Indexes auf username, email, is_active

SICHERHEIT:
- Bcrypt mit Salt für Passwörter
- Unique Constraints auf username und email
- is_active Flag für Account-Deaktivierung

ZUKUNFTSSICHERHEIT:
- latitude/longitude als DECIMAL(10,8) / DECIMAL(11,8)
- avatar_path für Profilbild-Upload
- bio Feld für Benutzerbeschreibungen

app/models/category.py
----------------------
ZWECK: Forum-Kategorien und Hierarchie-Verwaltung

DESIGN-ENTSCHEIDUNGEN:
- Selbst-referenzielle Beziehung für Subkategorien
- Maximal 2-3 Ebenen (Performance & Usability)
- Lazy Loading für Threads (memory-effizient)
- Cascade Delete für saubere Löschung

PERFORMANCE-OPTIMIERUNGEN:
- Caching der Thread- und Post-Zahlen (5 Minuten)
- Indexes auf parent_id und name
- get_last_post() für "neueste Beiträge" Anzeige

ZUKUNFTSSICHERHEIT:
- description Feld für Kategorie-Beschreibungen
- Erweiterbar für mehr Metadaten

app/models/thread.py
--------------------
ZWECK: Diskussionsthemen (Threads) mit Status-Verwaltung

DESIGN-ENTSCHEIDUNGEN:
- is_pinned, is_locked, is_deleted Flags
- view_count für Popularitäts-Tracking
- Soft-Delete für alle Posts im Thread
- Cascade Delete für saubere Datenbank

PERFORMANCE-OPTIMIERUNGEN:
- Caching der Post-Anzahl (5 Minuten)
- Indexes auf alle Status-Felder
- get_last_post() für schnelle "letzter Beitrag" Anzeige
- increment_view_count() für Thread-Safety

SICHERHEIT:
- is_locked verhindert weitere Antworten
- is_deleted Flag statt Hard-Delete

ZUKUNFTSSICHERHEIT:
- view_count kann für "beliebte Threads" verwendet werden
- updated_at für "aktive Threads" Sortierung

app/models/post.py
------------------
ZWECK: Beiträge und Antworten im Thread

DESIGN-ENTSCHEIDUNGEN:
- Threaded Reply-System (parent_id für Hierarchie)
- **Bild-Upload Vorbereitung**: has_image und image_path Felder
- **Geo-Koordinaten**: latitude/longitude für Karten-Integration
- Soft-Delete mit Cache-Bereinigung
- Max 500KB Bildgröße (konfigurierbar)

PERFORMANCE-OPTIMIERUNGEN:
- get_reply_depth() für verschachtelte Anzeige
- Indexes auf thread_id, author_id, parent_id
- Soft-Delete statt Hard-Delete (Performance)

SICHERHEIT:
- Content als Text (kein HTML, XSS-Prävention durch Jinja2)
- Bild-Upload Typ-Prüfung (ALLOWED_EXTENSIONS)

ZUKUNFTSSICHERHEIT:
- has_image Flag für schnelle Prüfung
- image_path für Filesystem-Speicherung
- latitude/longination für Geo-Tagging
- parent_id für Threaded-Diskussionen

app/models/message.py
---------------------
ZWECK: Private Nachrichten zwischen Benutzern

DESIGN-ENTSCHEIDUNGEN:
- is_read Flag für Ungelesen-Status
- Separate Delete-Flags pro User (is_deleted_by_sender/recipient)
- Static Methods für Inbox/Sent-Queries
- Cache-Management bei Status-Änderungen

PERFORMANCE-OPTIMIERUNGEN:
- get_inbox() und get_sent() mit Filtern
- Indexes auf sender_id, recipient_id, is_read
- mark_as_read() mit Cache-Bereinigung

SICHERHEIT:
- Nur Sender/Empfänger können Nachrichten sehen
- Soft-Delete für beide Parteien unabhängig

ZUKUNFTSSICHERHEIT:
- subject Feld für Betreffzeilen
- content für Nachrichtentext

===================================================
INSTALLATION UND SETUP
===================================================

VORAUSSETZUNGEN:
----------------
- Python 3.7 oder höher
- SQLite3 (in Python enthalten)
- ~50MB freier Speicher
- OpenWRT-Router (optional, für optimale Nutzung)

SCHNELLINSTALLATION (Development):
----------------------------------
1. Repository klonen:
   git clone <repository-url>
   cd miniForum

2. Virtuelle Umgebung erstellen:
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder venv\Scripts\activate  # Windows

3. Abhängigkeiten installieren:
   pip install -r requirements.txt

4. Datenbank initialisieren:
   python -c "from app import db, create_app; db.create_all(app=create_app())"

5. Anwendung starten:
   python run.py

6. Im Browser öffnen:
   http://localhost:5000

PRODUKTIONSINSTALLATION (OpenWRT):
-----------------------------------
1. Auf OpenWRT-Router verbinden:
   ssh root@192.168.1.1

2. Python und SQLite installieren:
   opkg update
   opkg install python3 python3-pip sqlite3

3. Anwendung kopieren:
   scp -r miniForum/ root@192.168.1.1:/opt/

4. Abhängigkeiten installieren:
   cd /opt/miniForum
   pip3 install -r requirements.txt

5. Datenbank initialisieren:
   python3 -c "from app import db, create_app; db.create_all(app=create_app('production'))"

6. Als Service einrichten (siehe deploy/openwrt/miniForum.init)

7. Apache konfigurieren (siehe deploy/openwrt/apache.conf)

8. Service starten:
   /etc/init.d/miniForum start

DATENBANK-INITIALISIERUNG:
--------------------------
Für Development:
python -c "from app import db, create_app; db.create_all(app=create_app())"

Für Production:
python -c "from app import db, create_app; db.create_all(app=create_app('production'))"

Ersten Admin-Benutzer erstellen:
python -c "
from app import create_app
from app.models import User
from app import db

app = create_app()
with app.app_context():
    user = User(username='admin', email='admin@example.com')
    user.set_password('admin123')
    user.is_admin = True
    db.session.add(user)
    db.session.commit()
    print('Admin-Benutzer erstellt!')
"

ANWENDUNG STARTEN:
------------------
Development (mit Debug-Modus und Hot-Reload):
python run.py

Production (mit Gunicorn):
gunicorn -c deploy/openwrt/gunicorn.conf.py run:app

Oder mit systemd Service:
systemctl start miniForum

================================================================================
KONFIGURATION
================================================================================

UMGEBUNGSVARIABLEN:
-------------------
SECRET_KEY           - Geheimer Schlüssel für Sessions (Production!)
DATABASE_URL         - Datenbank-URL (optional)
FLASK_ENV           - 'development' oder 'production'
FLASK_CONFIG        - 'development', 'production', 'testing'

WICHTIGE KONFIGURATIONSPARAMETER (config.py):
---------------------------------------------
POSTS_PER_PAGE      - Beiträge pro Seite (Standard: 15)
THREADS_PER_PAGE    - Threads pro Seite (Standard: 20)
MESSAGES_PER_PAGE   - Nachrichten pro Seite (Standard: 20)
MAX_CONTENT_LENGTH  - Max Upload-Größe (Standard: 500KB)
CACHE_DEFAULT_TIMEOUT - Cache-Dauer in Sekunden (Standard: 300)

OPENWRT-SPEZIFISCHE EINSTELLUNGEN:
-----------------------------------
GUNICORN_WORKERS    - Anzahl Worker-Prozesse (Standard: 2)
GUNICORN_THREADS    - Threads pro Worker (Standard: 1)
GUNICORN_MAX_REQUESTS - Worker-Restart nach Requests (Standard: 1000)

================================================================================
WARTUNG UND FEHLERBEHEBUNG
================================================================================

DATENBANK-BACKUP:
-----------------
sqlite3 forum.db ".backup 'forum_backup.db'"

CACHE LEEREN:
-------------
Bei Anzeigeproblemen oder nach Datenänderungen:
python -c "from app import cache; cache.clear()"

LOGS PRÜFEN:
------------
Development: In Konsole ausgeben
Production: /var/log/miniForum.log

HÄUFIGE PROBLEME:
-----------------

Problem: "Database is locked" Fehler
Lösung: SQLite WAL-Modus aktivieren oder Gunicorn-Worker reduzieren

Problem: Langsame Antwortzeiten
Lösung: Cache prüfen, Indexes überprüfen, Speicher prüfen

Problem: Speicherverbrauch zu hoch
Lösung: Gunicorn-Worker reduzieren, Cache-Timeout verkürzen

Problem: Bild-Upload funktioniert nicht
Lösung: Upload-Verzeichnis prüfen, Schreibrechte prüfen, Dateigröße prüfen

================================================================================
PERFORMANCE-MONITORING
================================================================================

SPEICHERVERBRAUCH PRÜFEN:
-------------------------
ps aux | grep python

RESPONSE-ZEITEN MESSEN:
-----------------------
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/

DATENBANK-PERFORMANCE:
----------------------
In Development: SQLALCHEMY_ECHO = True
Langsame Queries werden automatisch geloggt (>100ms)

CACHE-EFFEKTIVITÄT:
-------------------
Cache-Hits: In Logs prüfen
Cache-Performance: response times vergleichen

================================================================================
ZUKUNFTSERWEITERUNGEN
================================================================================

Die Anwendung ist bereits vorbereitet für:

KARTEN-INTEGRATION:
-------------------
- Geo-Koordinaten in User- und Post-Modellen
- latitude/longitude Felder (DECIMAL(10,8) / DECIMAL(11,8))
- API-Endpunkte können einfach hinzugefügt werden

BILD-UPLOAD:
------------
- has_image und image_path Felder in Post-Modell
- Upload-Infrastruktur bereits implementiert
- 500KB Limit konfigurierbar
- Thumbnail-Generierung vorbereitet (Pillow)

MOBILE APP API:
---------------
- Blueprint-Struktur erlaubt einfache API-Erweiterung
- REST-like Endpunkte können hinzugefügt werden
- Authentifizierung bereits implementiert

ERWEITERTE SUCHE:
-----------------
- SQLite FTS5 (Full-Text Search) kann aktiviert werden
- Search-Indexes bereits definiert
- Performance-getestet für kleine bis mittlere Foren

================================================================================
SICHERHEITSHINWEISE
================================================================================

PRODUKTIONSEINSATZ:
-------------------
- SECRET_KEY unbedingt ändern!
- HTTPS verwenden (SESSION_COOKIE_SECURE = True)
- Regelmäßige Backups erstellen
- Logs auf verdächtige Aktivitäten prüfen
- Rate-Limits anpassen bei Bedarf

PASSWÖRTER:
-----------
- Bcrypt mit Salt (sicher)
- Mindestlänge: 8 Zeichen empfohlen
- Regelmäßiges Passwort-Change erzwingen (optional)

BENUTZERRECHTE:
---------------
- Admin-Flag nur für vertrauenswürdige Benutzer
- is_active Flag für Account-Sperrung
- IP-Logging bei Bedarf aktivieren

================================================================================
RESSOURCEN UND SPEZIFIKATIONEN
================================================================================

MINIMALE SYSTEMANFORDERUNGEN:
-----------------------------
- CPU: 400 MHz Single-Core
- RAM: 64MB (50MB für Anwendung)
- Speicher: 100MB freier Speicherplatz
- OS: Linux mit Python 3.7+

EMPFOHLENE SYSTEMANFORDERUNGEN:
--------------------------------
- CPU: 580 MHz Dual-Core (OpenWRT-Router)
- RAM: 128MB
- Speicher: 256MB freier Speicherplatz
- OS: OpenWRT 19.07+

PERFORMANCE-ZIELE:
------------------
- Speicherverbrauch: <50MB für Python-Prozesse
- Response-Zeiten: <200ms für Listen, <100ms für Assets
- Gleichzeitige Benutzer: 10-20 ohne Degradation
- Datenbank-Queries: <100ms (99% der Queries)

================================================================================
SUPPORT UND WEITERE HILFE
================================================================================

Bei Fragen oder Problemen:
- README.txt gründlich lesen
- Konfiguration prüfen
- Logs analysieren
- Cache leeren bei Anzeigeproblemen

Dokumentation: Diese Datei (readme.txt)
Konfiguration: config.py
Beispiele: deploy/openwrt/

================================================================================
LIZENZ UND CREDITS
================================================================================

Dies ist eine Open-Source-Anwendung für ressourcenschonende Foren.
Optimiert für OpenWRT und eingebettete Systeme.

Entwickelt mit Flask, SQLAlchemy, SQLite für minimale Ressourcennutzung.

================================================================================
ENDE DER DOKUMENTATION
================================================================================
