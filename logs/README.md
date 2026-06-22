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
| `tests.log` | Unit Tests (pytest) |

## Screenshots

| Datei | Inhalt |
|-------|--------|
| `screenshots/n8n_Workflow_Succeeded.png` | n8n — Workflow erfolgreich ausgeführt (Gemini-Extraktion) |
| `screenshots/Camunda_Operate_Prozess_Abgeschlossen.png` | Camunda Operate — Prozessinstanz komplett durchgelaufen |
| `screenshots/UiPath_RPA_Successful.png` | UiPath Orchestrator — Job Successful |
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

# Unit Tests
$env:PYTHONPATH = "."; & "...\pytest.exe" tests/test_workers.py -v *>&1 | Tee-Object -FilePath logs/tests.log
```
