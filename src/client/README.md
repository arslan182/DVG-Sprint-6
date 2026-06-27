# Test-Client

`client.py` ist ein **manueller Testclient** zum direkten Testen von gRPC-Server und RabbitMQ — unabhängig vom Camunda-Prozess.

## Zweck

Im normalen Betrieb startet `start_process.py` den Camunda-Prozess, der dann automatisch alle Worker aufruft. Der Testclient umgeht Camunda und spricht gRPC-Server und RabbitMQ direkt an — nützlich zum isolierten Testen der Infrastruktur.

## Was der Client macht

1. **gRPC**: Sendet eine Test-Rechnung an den `invoice_metadata` Server (`SpeichereMetadaten`)
2. **RabbitMQ**: Falls gRPC erfolgreich → schreibt einen Zahlungsauftrag in die Queue `zahlungs_auftraege`

## Konfiguration

Alle Werte werden aus Umgebungsvariablen gelesen (`.env`):

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `TEST_RECHNUNGS_NUMMER` | `R-TEST-001` | Rechnungsnummer |
| `TEST_LIEFERANT` | `Test GmbH` | Lieferantenname |
| `TEST_BETRAG` | `99.99` | Betrag |
| `TEST_WAEHRUNG` | `EUR` | Währung |
| `TEST_DATUM` | `2026-01-01` | Datum |
| `GRPC_HOST` / `GRPC_PORT` | `localhost:50051` | gRPC Server |
| `RABBITMQ_HOST/USER/PASSWORD` | `localhost/user/password` | RabbitMQ |

## Starten

```bash
python src/client/client.py
```

Voraussetzung: gRPC Server (`python -m src.invoice_metadata.server`) und RabbitMQ (Docker) laufen.
