# Invoice Metadata Service – gRPC Server

Dieser Dienst speichert Rechnungsmetadaten dauerhaft in PostgreSQL. Er stellt einen gRPC-Endpunkt bereit, der vom `grpc_worker.py` (Camunda Worker) und vom `client.py` (Testclient) aufgerufen wird.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `invoice.proto` | Protobuf-Schnittstellendefinition (RechnungRequest, RechnungResponse, Status-Enum) |
| `server.py` | gRPC Server mit DB-Verbindung, Reconnect-Logik und SQL-Persistenz |
| `invoice_pb2.py` | Generierte Protobuf-Klassen |
| `invoice_pb2_grpc.py` | Generierter gRPC-Stub |

## Funktionsweise

1. **Start**: Verbindet sich mit PostgreSQL und erstellt die `invoices`-Tabelle falls nicht vorhanden
2. **Request**: Empfängt `RechnungRequest` (Nummer, Lieferant, Betrag, Währung, Datum, Status)
3. **SQL**: `INSERT INTO invoices ... ON CONFLICT DO UPDATE` — idempotent, kein Duplikat-Fehler
4. **Response**: Gibt `RechnungResponse(erfolg=True/False, nachricht=...)` zurück

## Technische Details

- **Port**: 50051 (gRPC, insecure)
- **Datenbank**: PostgreSQL via `psycopg2`
- **Reconnect-Logik**: `_ensure_connection()` prüft vor jedem Request ob die DB-Verbindung noch aktiv ist und reconnectet automatisch
- **Fehlerbehandlung**: Bei SQL-Fehler wird `rollback()` aufgerufen und `erfolg=False` zurückgegeben (kein Crash)
- **Thread-Pool**: 10 parallele Worker (`futures.ThreadPoolExecutor`)

## Tabellenschema

```sql
CREATE TABLE invoices (
    rechnungs_nummer VARCHAR(50) PRIMARY KEY,
    lieferant        VARCHAR(100),
    betrag           DOUBLE PRECISION,
    waehrung         VARCHAR(10),
    datum            DATE,
    status           VARCHAR(20)   -- OFFEN | BEZAHLT
);
```

## Starten

```bash
python -m src.invoice_metadata.server
```
