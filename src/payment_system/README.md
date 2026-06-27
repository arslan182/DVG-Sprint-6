# Payment System – RabbitMQ Consumer

Dieses Modul ist der **RabbitMQ Consumer** für die asynchrone Zahlungsabwicklung. Er läuft unabhängig vom Camunda-Prozess und verarbeitet Zahlungsaufträge aus der Queue.

## Rolle im Gesamtsystem

Der Datenfluss für eine Zahlung sieht so aus:

```
Camunda (BPMN)
    │
    ▼  Task: initiate-payment
payment_worker.py          ← Camunda Zeebe Worker
    │  Schreibt Auftrag
    ▼
RabbitMQ Queue: zahlungs_auftraege
    │  Liest Auftrag
    ▼
payment.py                 ← RabbitMQ Consumer (dieses Modul)
    │  Aktualisiert Status
    ▼
PostgreSQL: invoices.status = 'BEZAHLT'
```

**Wichtig:** `payment_worker.py` (in `src/workers/`) ist der Camunda-seitige Worker, der den Auftrag **in die Queue schreibt**. `payment.py` (dieses Modul) ist der Consumer, der den Auftrag **aus der Queue liest** und die Datenbank aktualisiert.

## Funktionsweise

1. **Verbindung**: Stellt eine Verbindung zum RabbitMQ-Broker (Port 5672) und zur PostgreSQL-Datenbank her.
2. **Subscription**: Abonniert die Queue `zahlungs_auftraege` (durable=True).
3. **Verarbeitung**: Für jede Nachricht wird `rechnungs_nummer` extrahiert und ein `UPDATE invoices SET status = 'BEZAHLT'` ausgeführt.
4. **Acknowledgement**: Nach erfolgreichem DB-Update wird die Nachricht mit `basic_ack` aus der Queue entfernt.

## Technische Details

- **Queue**: `zahlungs_auftraege` (durable — übersteht RabbitMQ-Neustart)
- **DB Connection Pool**: `psycopg2.pool.SimpleConnectionPool` (min/max per `DB_POOL_MIN`/`DB_POOL_MAX` env var)
- **Fehlerbehandlung**: Bei DB-Fehler wird `rollback()` aufgerufen und die Verbindung an den Pool zurückgegeben
- **SQL**: Parametrisierte Abfragen (kein SQL-Injection-Risiko)

## Starten

```bash
python src/payment_system/payment.py
```

Voraussetzung: RabbitMQ und PostgreSQL laufen (Docker), gRPC Server läuft (damit die `invoices`-Tabelle existiert).
