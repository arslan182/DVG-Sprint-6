# Logs – Sprint 6

Terminal-Ausgaben der Worker und Server, plus Screenshots aus Camunda, n8n und UiPath als Nachweis für den Testlauf.

## Log-Dateien

| Datei | Inhalt |
|-------|--------|
| `server.log` | gRPC Server — Datenbankverbindung und gespeicherte Rechnungen |
| `extraction_worker.log` | AI Extraction Worker — PDF-Versand an n8n und Gemini-Ergebnis |
| `auto_workers.log` | Auto Workers — Camunda Tasks inkl. UiPath Bot-Start und Polling |
| `grpc_worker.log` | gRPC Worker — Metadaten speichern |
| `payment_worker.log` | Payment Worker — Zahlungsauftrag per RabbitMQ |
| `start_process.log` | Prozess starten |
| `email_receiver.log` | Email Receiver Server — Gmail-Trigger → Camunda Message Publish |
| `tests.log` | Unit Tests (pytest) |

## Screenshots

| Datei | Inhalt |
|-------|--------|
| `screenshots/n8n_Gmail_Workflow_Published.png` | n8n — Gmail → Camunda Rechnungseingang Workflow (published) |
| `screenshots/n8n_Extraktion_Workflow_Published.png` | n8n — Rechnungsextraktion AI Workflow (published) |
| `screenshots/Camunda_Operate_Email_Prozess_Komplett_1.png` | Camunda Operate — Email-Eingang: Prozess vollständig abgeschlossen (1) |
| `screenshots/Camunda_Operate_Email_Prozess_Komplett_2.png` | Camunda Operate — Email-Eingang: Prozess vollständig abgeschlossen (2) |
| `screenshots/Camunda_Operate_Manuell_Fallback_Komplett.png` | Camunda Operate — Prozess mit manuellem gRPC-Fallback abgeschlossen |
| `screenshots/UiPath_Orchestrator_RPA_Erfolgreich.png` | UiPath Orchestrator — RPA Workflow Job Successful (inkl. Rechnungspositionen) |
| `screenshots/DMN_Compliance_Schwellenwert.png` | Camunda Modeler — DMN Entscheidungstabelle |

> Docker-Logs werden nicht als Datei gespeichert. Mit `docker logs <container-name>` abrufbar.

## Logs erzeugen

```powershell
# Docker (PostgreSQL, RabbitMQ, n8n)
docker-compose up -d

# gRPC Server
& "...\python.exe" -u -m src.invoice_metadata.server *>&1 | Tee-Object -FilePath logs/server.log

# AI Extraction Worker
& "...\python.exe" -u src/workers/extraction_worker.py *>&1 | Tee-Object -FilePath logs/extraction_worker.log

# Auto Workers
& "...\python.exe" -u src/workers/auto_workers.py *>&1 | Tee-Object -FilePath logs/auto_workers.log

# gRPC Worker
& "...\python.exe" -u src/workers/grpc_worker.py *>&1 | Tee-Object -FilePath logs/grpc_worker.log

# Payment Worker
& "...\python.exe" -u src/workers/payment_worker.py *>&1 | Tee-Object -FilePath logs/payment_worker.log

# Prozess starten
& "...\python.exe" -u start_process.py test_rechnung.pdf *>&1 | Tee-Object -FilePath logs/start_process.log

# Email Receiver (Gmail → Camunda)
& "...\python.exe" -u email_receiver.py *>&1 | Tee-Object -FilePath logs/email_receiver.log

# Unit Tests
$env:PYTHONPATH = "."; & "...\pytest.exe" tests/test_workers.py -v *>&1 | Tee-Object -FilePath logs/tests.log
```
