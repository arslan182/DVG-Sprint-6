# Dvg Sprint 6 – AI-gestützte Rechnungsverarbeitung

**Hochschule Karlsruhe** | Modul: Digitalisierung von Geschäftsprozessen | Gruppe G11

---

## Überblick

Sprint 6 erweitert den RPA-Bot aus Sprint 5 um einen AI-Agenten und einen automatischen E-Mail-Eingang. Rechnungen können jetzt per E-Mail eingehen — der Prozess startet vollautomatisch. Google Gemini 2.5 Flash extrahiert die Daten aus dem PDF, der Mitarbeiter prüft kurz im Camunda Tasklist und gibt frei — danach läuft alles automatisch weiter.

**Neu in Sprint 6:**
- AI-Extraktion per n8n + Google Gemini (Rechnungsnummer, Lieferant, Betrag, Positionen, …)
- **E-Mail-Eingang:** Gmail → Google Drive → Camunda (Message Start Event) — vollautomatisch
- UiPath Bot trägt jetzt auch einzelne Rechnungspositionen ins ERP ein
- Compliance-Check läuft direkt über eine DMN-Entscheidungstabelle in Camunda (kein Worker mehr nötig)

---

## Architektur

Das vollständige Architekturdiagramm für Sprint 6 befindet sich unter:

```
docs/Architekturdiagramm/Architekturdiagramm.png   ← Gesamtübersicht (alle 6 Ebenen)
docs/Architekturdiagramm/Ebene (1-2-3).png         ← Ebenen 1–3: Eingang, KI, Prozess
docs/Architekturdiagramm/Ebene (4-5-6).png         ← Ebenen 4–6: Worker, Services, Daten
```

Das System ist in 6 horizontale Ebenen gegliedert:

| Ebene | Name | Komponenten |
|-------|------|-------------|
| 1 | Benutzer- und Eingangsebene | Benutzer, PDF-Datei, `start_process.py` / Gmail → n8n → `email_receiver.py` |
| 2 | KI-Extraktions-Ebene *(neu in Sprint 6)* | `extraction_worker.py` → n8n → Google Gemini 2.5 Flash |
| 3 | Prozess- und Workflow-Ebene | Camunda 8 SaaS, BPMN, DMN, Camunda Tasklist (User Tasks) |
| 4 | Integrations-Ebene | Python Workers (pyzeebe), RabbitMQ Queue |
| 5 | Service-Ebene | gRPC Server, UiPath RPA Bot, Payment Consumer |
| 6 | Datenhaltung | PostgreSQL, Google Drive |

---

## Projektstruktur

```
Dvg-sprint-6/
├── src/
│   ├── workers/
│   │   ├── extraction_worker.py   # Sendet PDF an n8n, gibt KI-Daten an Camunda zurück
│   │   ├── auto_workers.py        # Service Tasks (Erfassen, Validieren, UiPath, Archiv)
│   │   ├── grpc_worker.py         # Speichert Metadaten per gRPC in PostgreSQL
│   │   └── payment_worker.py      # Schickt Zahlungsauftrag per RabbitMQ
│   ├── invoice_metadata/
│   │   ├── server.py              # gRPC Server
│   │   ├── invoice.proto          # Protobuf Definition
│   │   ├── invoice_pb2.py
│   │   └── invoice_pb2_grpc.py
│   ├── payment_system/
│   │   └── payment.py             # RabbitMQ Consumer
│   ├── client/
│   │   └── client.py              # Testclient für gRPC + RabbitMQ
│   └── camunda/
│       ├── Workflow-Sprint-6.bpmn # BPMN-Prozess
│       ├── compliance_check.dmn   # DMN Compliance-Entscheidungstabelle
│       └── forms/
│           ├── invoice_form.json  # User Task Formular: Rechnungsdaten
│           └── compliance_form.json # User Task Formular: Freigabe / Compliance
├── n8n/
│   ├── workflow_rechnungsextraktion.json       # n8n Workflow: KI-Extraktion (Gemini)
│   └── workflow_gmail_rechnungseingang.json    # n8n Workflow: Gmail → Google Drive → Camunda
├── UiPath_ERP_Bot/
│   ├── Main.xaml                  # UiPath Workflow
│   ├── inject_script.js           # JavaScript für ERP-Formular Ausfüllung
│   └── project.json
├── extras/
│   └── compose/
│       ├── n8n/docker-compose.yml
│       ├── RabbitMQ/docker-compose.yml
│       └── postgres/docker-compose.yml
├── docs/
│   ├── Architekturdiagramm/       # Architekturdiagramme (Sprint 6)
│   └── screenshots/               # Testdokumentation (Prozess-Screenshots)
├── tests/
│   └── test_workers.py
├── start_process.py               # Prozess starten (PDF-Pfad als Argument)
├── email_receiver.py              # Lokaler HTTP-Server: Gmail-Trigger → Camunda Message
├── send_correction.py             # Korrektur-Nachricht an wartenden Prozess senden
├── test_rechnung.pdf              # Test-PDF für manuelle Tests
├── .env                           # Secrets (nicht ins Git!)
├── requirements.txt
└── README.md
```

---

## Voraussetzungen

- Python 3.10+
- Docker
- Camunda 8 SaaS Account (kostenlos unter [camunda.io](https://camunda.io))
- Google AI Studio API-Key ([aistudio.google.com](https://aistudio.google.com))
- Google Cloud Projekt mit Gmail API + Google Drive API (für E-Mail-Eingang)
- UiPath Cloud Account mit deployed RPA Workflow

```bash
pip install -r requirements.txt
```

---

## Einrichtung

### 1. `.env` Datei anlegen

```env
# Camunda
CAMUNDA_CLIENT_ID=...
CAMUNDA_CLIENT_SECRET=...
CAMUNDA_CLUSTER_ID=...
CAMUNDA_REGION=bru-2

# gRPC Server (PostgreSQL)
GRPC_HOST=localhost
GRPC_PORT=50051

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_USER=user
RABBITMQ_PASSWORD=password

# PostgreSQL
DB_HOST=localhost
DB_NAME=invoice_db
DB_USER=admin
DB_PASSWORD=...

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/rechnungsextraktion
N8N_TIMEOUT_SECONDS=60

# Google Drive (E-Mail-Eingang)
GOOGLE_DRIVE_FOLDER_ID=...

# Email Receiver Server
EMAIL_RECEIVER_PORT=8081

# UiPath
UIPATH_CLIENT_ID=...
UIPATH_CLIENT_SECRET=...
UIPATH_ORG=gruppe11dvg
UIPATH_TENANT=DefaultTenant
UIPATH_FOLDER_ID=7919369
UIPATH_QUEUE_NAME=ERP-Rechnungen
UIPATH_PROCESS_NAME=RPA Workflow
UIPATH_POLL_INTERVAL=5
UIPATH_POLL_RETRIES=30
UIPATH_JOB_TIMEOUT_MS=180000
```

### 2. n8n Workflows importieren

```bash
cd extras/compose/n8n
docker-compose up -d
```

Dann unter `http://localhost:5678` öffnen und beide Workflows importieren:

- `n8n/workflow_rechnungsextraktion.json` — Google Gemini API-Key als Credential hinterlegen (Typ: *Google Gemini(PaLM) Api*)
- `n8n/workflow_gmail_rechnungseingang.json` — Gmail OAuth2 und Google Drive OAuth2 Credentials hinterlegen

Beide Workflows aktivieren.

### 3. PostgreSQL und RabbitMQ starten

```bash
cd extras/compose/postgres && docker-compose up -d
cd extras/compose/RabbitMQ && docker-compose up -d
```

---

## System starten

Für den vollständigen Betrieb (inkl. E-Mail-Eingang) müssen alle sechs Terminals gleichzeitig laufen:

**Terminal 1** – gRPC Server:
```bash
python -m src.invoice_metadata.server
```

**Terminal 2** – AI Extraction Worker:
```bash
python src/workers/extraction_worker.py
```

**Terminal 3** – Auto Workers (Validierung, UiPath, Archivierung):
```bash
python src/workers/auto_workers.py
```

**Terminal 4** – gRPC Worker (Metadaten speichern):
```bash
python src/workers/grpc_worker.py
```

**Terminal 5** – Payment Worker:
```bash
python src/workers/payment_worker.py
```

**Terminal 6** – Email Receiver (nur für E-Mail-Eingang nötig):
```bash
python email_receiver.py
```

---

## Prozess starten

**Option 1 – Manuell (lokale PDF):**
```bash
python start_process.py test_rechnung.pdf
```

Oder ohne Argument — dann wird nach dem Pfad gefragt:
```bash
python start_process.py
```

**Option 2 – Per E-Mail:**
Eine E-Mail mit PDF-Anhang an die verknüpfte Gmail-Adresse schicken. n8n erkennt die E-Mail automatisch, lädt das PDF in Google Drive hoch und startet den Camunda-Prozess über den Message Start Event `Rechnung_per_Mail`.

---

## Prozessablauf

### Service Tasks (automatisch)

| Task | Worker | Was passiert |
|------|--------|-------------|
| ki-extraktion | extraction_worker.py | PDF → n8n → Gemini → JSON |
| rechnung-erfassen | auto_workers.py | Zeitstempel setzen |
| automatische-validierung | auto_workers.py | Pflichtfelder prüfen |
| compliance-check | DMN in Camunda | Schwellenwert automatisch auswerten |
| uipath-erp-queue | auto_workers.py | UiPath Bot starten (StartJobs API) |
| save-invoice-metadata | grpc_worker.py | Metadaten in PostgreSQL speichern |
| initiate-payment | payment_worker.py | Zahlungsauftrag per RabbitMQ |
| rechnung-archivieren | auto_workers.py | Archivierung abschließen |

### User Tasks (manuell im Camunda Tasklist)

- **KI-extrahierte Daten prüfen** – extrahierte Felder kontrollieren und korrigieren
- **Rechnung freigeben** – finale Freigabe vor ERP-Eintrag
- **Compliance-Fall manuell prüfen** – nur wenn Betrag über Schwellenwert

### Fehlerbehandlung

Wenn der gRPC Server oder RabbitMQ nicht erreichbar ist, landet der Prozess in einem Boundary Error Event und der Task wird als manueller Schritt im Tasklist angezeigt.

---

## Compliance-Schwellenwerte (DMN)

| Währung | Compliance nötig | Schwellenwert |
|---------|-----------------|--------------|
| EUR     | Ja (> 10.000)   | 10000        |
| USD     | Ja (> 11.000)   | 11000        |
| CHF     | Ja (> 10.800)   | 10800        |
| GBP     | Ja (> 8.700)    | 8700         |
| Andere  | Ja (> 0)        | 0 (Fallback) |

Die Regeln sind in `src/camunda/compliance_check.dmn` definiert und werden direkt in Camunda als Business Rule Task ausgewertet (kein Python Worker nötig). Die Fallback-Regel greift bei unbekannten Währungen — der Compliance-Check wird dann immer ausgelöst.

---

## n8n Workflow

Der Workflow hat 6 Nodes:

1. **Webhook** – empfängt die PDF als HTTP POST (raw binary body)
2. **PDF in Base64 konvertieren** – kodiert die PDF als Base64-String für die Gemini API
3. **Gemini Anfrage bauen** – erstellt den API-Request mit der PDF als `inline_data` (funktioniert auch mit gescannten PDFs ohne Textlayer)
4. **Gemini – Rechnung analysieren** – ruft `gemini-2.5-flash` via REST API auf
5. **JSON parsen & validieren** – bereinigt die Gemini-Antwort und validiert die Felder
6. **Respond to Webhook** – schickt das JSON-Ergebnis zurück an den Python Worker

> Die PDF wird direkt als `inline_data` an Gemini übergeben — kein separater Text-Extraktionsschritt. Das funktioniert auch für gescannte (image-only) PDFs.

---

## UiPath RPA Bot

Der Bot läuft als Unattended Cloud Robot in UiPath Orchestrator (Folder: Solution). Er wird automatisch vom Python Worker gestartet, sobald Camunda den Task `uipath-erp-queue` picked.

Der Bot öffnet das ERP-Frontend in Edge und füllt das Formular per JavaScript Injection aus — inklusive einzelner Rechnungspositionen. Das ERP-Frontend ist unter folgendem Link erreichbar:

```
https://anhe0003.github.io/this-and-that/ERP_Rechnungserfassung.html
```

**UiPath Konfiguration:**
- Org: `gruppe11dvg`
- Tenant: `DefaultTenant`
- Folder: Solution (ID: 7919369)
- Process: `RPA Workflow`
- Robot: Default Robot (Unattended, Cloud Serverless)

---

## Korrektur senden

Wenn ein Prozess auf fehlende Informationen vom Lieferanten wartet:

```bash
python send_correction.py RE-2026-001
```

---

## Tests

```bash
$env:PYTHONPATH = "."; pytest tests/test_workers.py -v
```

---

## Hinweise

- Der Camunda Trial Cluster pausiert nach längerer Inaktivität — vor dem Testen im [Camunda Console](https://console.camunda.io) prüfen ob er noch läuft.
- n8n muss laufen und beide Workflows müssen aktiviert sein, bevor ein Prozess gestartet wird.
- Der Google Gemini API-Key hat auf dem Free-Tier ein Rate Limit — zwischen Tests kurz warten wenn 429-Fehler auftreten.
- Der UiPath Bot läuft in einer Cloud-Session — das ausgefüllte ERP-Formular ist nur über den UiPath Live Stream sichtbar, nicht im lokalen Browser.
- Für den E-Mail-Eingang muss `email_receiver.py` lokal laufen — n8n (Docker) erreicht ihn über `host.docker.internal:8081`.
- Die Gmail OAuth2 App muss im Google Cloud Projekt als Testnutzer die eigene E-Mail-Adresse eingetragen haben.
