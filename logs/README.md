# Logs – Sprint 5

Terminal-Ausgaben der Worker und Server, plus Screenshots aus Camunda und UiPath als Nachweis für den Testlauf.

## Log-Dateien

| Datei | Inhalt |
|-------|--------|
| `server.log` | gRPC Server — Datenbankverbindung und gespeicherte Rechnungen |
| `auto_workers.log` | Auto Workers — Camunda Tasks inkl. UiPath Bot-Start und Polling |
| `grpc_worker.log` | gRPC Worker — Metadaten speichern |
| `payment_worker.log` | Payment Worker — Zahlungsauftrag per RabbitMQ |
| `start_process.log` | Prozess starten |
| `tests.log` | Unit Tests (pytest) |

## Screenshots

| Datei | Inhalt |
|-------|--------|
| `camunda_prozess_abgeschlossen-sprint-5.png` | Camunda Operate — Prozessinstanz komplett durchgelaufen |
| `uipath_job_successful-sprint-5.png` | UiPath Orchestrator — Job Successful mit den echten Rechnungsdaten aus Camunda |
| `uipath_studio_workflow.png` | UiPath Studio — Workflow-Struktur mit Inject JS Script |
| `uipath_manueller_test.png` | UiPath Orchestrator — manueller Test-Run aus Studio |

> Docker-Logs werden nicht als Datei gespeichert. Mit `docker logs <container-name>` abrufbar.

## Logs erzeugen

```powershell
# Docker
docker-compose up -d

# gRPC Server
& "...\python.exe" -u -m src.invoice_metadata.server *>&1 | Tee-Object -FilePath logs/server.log

# Auto Workers
& "...\python.exe" -u src/workers/auto_workers.py *>&1 | Tee-Object -FilePath logs/auto_workers.log

# gRPC Worker
& "...\python.exe" -u src/workers/grpc_worker.py *>&1 | Tee-Object -FilePath logs/grpc_worker.log

# Payment Worker
& "...\python.exe" -u src/workers/payment_worker.py *>&1 | Tee-Object -FilePath logs/payment_worker.log

# Prozess starten
& "...\python.exe" -u start_process.py *>&1 | Tee-Object -FilePath logs/start_process.log

# Unit Tests
$env:PYTHONPATH = "."; & "...\pytest.exe" tests/test_workers.py -v *>&1 | Tee-Object -FilePath logs/tests.log
```
