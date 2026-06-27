# Camunda – BPMN, DMN und Formulare

## Ordnerstruktur

```
src/camunda/
├── Workflow-Sprint-6.bpmn     # BPMN-Prozessdefinition (in Camunda deployen)
├── compliance_check.dmn       # DMN Entscheidungstabelle für Compliance-Schwellenwerte
├── forms/
│   ├── invoice_form.json      # User Task Formular: Rechnungsdaten erfassen / prüfen
│   └── compliance_form.json   # User Task Formular: Compliance / Freigabe / Zurückweisung
└── README.md
```

## Formulare

Formulare werden nur für **User Tasks** benötigt — also Tasks, bei denen ein Mensch im Camunda Tasklist eingreift. Alle anderen Tasks sind Service Tasks (automatisch per Python Worker).

| User Task im BPMN | Formular |
|---|---|
| Rechnung Validieren | `invoice-form` |
| Zahlung manuell erfassen | `invoice-form` |
| Metadaten manuell speichern | `invoice-form` |
| Compliance-Fall manuell prüfen | `compliance-form` |
| Rechnung freigeben | `compliance-form` |
| Rechnung zurückweisen | `compliance-form` |

## DMN – Compliance-Entscheidungstabelle

Die Tabelle `compliance_check.dmn` wird als **Business Rule Task** direkt in Camunda ausgewertet — kein Python Worker nötig. Hit Policy: **First** (erste zutreffende Regel gewinnt).

| Währung | compliance_notwendig | schwellenwert |
|---------|---------------------|--------------|
| EUR | true (Betrag > 10000) | 10000 |
| USD | true (Betrag > 11000) | 11000 |
| CHF | true (Betrag > 10800) | 10800 |
| GBP | true (Betrag > 8700)  | 8700  |
| Andere | true (immer) | 0 (Fallback) |

Die Fallback-Regel (leere Bedingungen) greift bei unbekannten Währungen — der Compliance-Check wird dann immer ausgelöst.

## Service Task Typen (im BPMN eingetragen)

| BPMN Task | Task-Typ | Worker |
|-----------|----------|--------|
| KI-Extraktion | `ki-extraktion` | extraction_worker.py |
| Rechnung erfassen | `rechnung-erfassen` | auto_workers.py |
| Automatische Validierung | `automatische-validierung` | auto_workers.py |
| Fehlende Infos anfordern | `send-request-email` | auto_workers.py |
| ERP-Eintrag (RPA) | `uipath-erp-queue` | auto_workers.py |
| Metadaten speichern | `save-invoice-metadata` | grpc_worker.py |
| Zahlung veranlassen | `initiate-payment` | payment_worker.py |
| Rechnung archivieren | `rechnung-archivieren` | auto_workers.py |

## Prozessvariablen

| Variable | Typ | Beschreibung |
|----------|-----|-------------|
| `rechnung_pdf_pfad` | String | Pfad zur PDF-Datei |
| `rechnungs_nummer` | String | Eindeutige Rechnungsnummer |
| `lieferant` | String | Name des Lieferanten |
| `betrag` | Number | Rechnungsbetrag |
| `waehrung` | String | EUR / USD / CHF / GBP |
| `datum` | String | Datum im Format YYYY-MM-DD |
| `eingangskanal` | String | email / portal / edi |
| `validierung_erfolgreich` | Boolean | Ergebnis der automatischen Validierung |
| `rechnung_genehmigt` | Boolean | Manuelle Freigabe durch Sachbearbeiter |
| `ki_extraktion_erfolgreich` | Boolean | Ob Gemini-Extraktion geklappt hat |
