## Dokumentation des Gesamtergebnisses

Sprint 6 wurde vollständig implementiert und getestet. Alle Prozessvarianten — automatischer E-Mail-Eingang und manueller Start — wurden erfolgreich durchlaufen.

### Was wurde umgesetzt

| Ziel | Status |
|------|--------|
| AI-Extraktion per n8n + Google Gemini 2.5 Flash | ✅ |
| Automatischer E-Mail-Eingang (Gmail → Camunda) | ✅ |
| UiPath Bot mit Rechnungspositionen | ✅ |
| Compliance-Check per DMN-Entscheidungstabelle | ✅ |
| Manueller Fallback bei gRPC/RabbitMQ-Fehler | ✅ |

### Architektur

Das vollständige Architekturdiagramm befindet sich unter `docs/Architekturdiagramm/`:

| Datei | Inhalt |
|-------|--------|
| `docs/Architekturdiagramm/Architekturdiagramm.png` | Gesamtübersicht – alle 6 Ebenen |
| `docs/Architekturdiagramm/Ebene (1-2-3).png` | Ebenen 1–3: Eingang, KI, Prozess |
| `docs/Architekturdiagramm/Ebene (4-5-6).png` | Ebenen 4–6: Worker, Services, Daten |

### Nachweise

Die vollständigen Logs der Worker befinden sich unter `docs/logs/` — siehe [`docs/logs/README.md`](docs/logs/README.md).

Die Prozess-Screenshots befinden sich unter `docs/screenshots/` — siehe [`docs/README.md`](docs/README.md).

| Datei | Inhalt |
|-------|--------|
| `docs/screenshots/n8n_Gmail_Workflow_Published.png` | n8n — Gmail → Camunda Rechnungseingang Workflow (published) |
| `docs/screenshots/n8n_Extraktion_Workflow_Published.png` | n8n — Rechnungsextraktion AI Workflow (published) |
| `docs/screenshots/Camunda_Operate_Email_Prozess_Komplett_1.png` | Camunda Operate — Email-Eingang: Prozess vollständig abgeschlossen (1) |
| `docs/screenshots/Camunda_Operate_Email_Prozess_Komplett_2.png` | Camunda Operate — Email-Eingang: Prozess vollständig abgeschlossen (2) |
| `docs/screenshots/Camunda_Operate_Manuell_Fallback_Komplett.png` | Camunda Operate — Prozess mit manuellem gRPC-Fallback abgeschlossen |
| `docs/screenshots/UiPath_Orchestrator_RPA_Erfolgreich.png` | UiPath Orchestrator — RPA Workflow Job Successful (inkl. Rechnungspositionen) |
| `docs/screenshots/DMN_Compliance_Schwellenwert.png` | Camunda Modeler — DMN Entscheidungstabelle |