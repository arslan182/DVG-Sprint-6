import os
import grpc
from concurrent import futures
import psycopg2
from dotenv import load_dotenv
from . import invoice_pb2
from . import invoice_pb2_grpc

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "invoice_db")
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secretpassword")


def _connect() -> psycopg2.extensions.connection:
    """Opens and returns a new database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


class RechnungService(invoice_pb2_grpc.RechnungServiceServicer):
    def __init__(self):
        """Opens the database connection and ensures the invoices table exists."""
        self.conn = _connect()
        self._create_table()

    def _ensure_connection(self):
        """Reconnects if the current connection is closed or broken."""
        try:
            if self.conn.closed or self.conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                self.conn.rollback()
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            print("[DB] Verbindung unterbrochen – reconnect...")
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = _connect()

    def _create_table(self):
        """Creates the invoices table if it doesn't exist yet."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    rechnungs_nummer VARCHAR(50) PRIMARY KEY,
                    lieferant VARCHAR(100),
                    betrag DOUBLE PRECISION,
                    waehrung VARCHAR(10),
                    datum DATE,
                    status VARCHAR(20)
                );
            """)
            self.conn.commit()

    def SpeichereMetadaten(self, request, context):
        """Inserts or updates an invoice record. Returns success/failure in the response."""
        status_name = invoice_pb2.RechnungsStatus.Name(request.status)

        self._ensure_connection()

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO invoices (rechnungs_nummer, lieferant, betrag, waehrung, datum, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rechnungs_nummer) DO UPDATE
                    SET status = EXCLUDED.status;
                """, (
                    request.rechnungs_nummer,
                    request.lieferant,
                    request.betrag,
                    request.waehrung,
                    request.datum,
                    status_name
                ))
                self.conn.commit()

            print(f"[DB] Rechnung {request.rechnungs_nummer} gespeichert.")
            return invoice_pb2.RechnungResponse(erfolg=True, nachricht="In DB gespeichert")

        except Exception as e:
            print(f"[DB] Fehler: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return invoice_pb2.RechnungResponse(erfolg=False, nachricht=str(e))


def serve():
    """Starts the gRPC server on port 50051. Exits if the DB connection fails."""
    try:
        servicer = RechnungService()
    except Exception as e:
        print(f"[gRPC Server] Datenbankverbindung fehlgeschlagen: {e}")
        return
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    invoice_pb2_grpc.add_RechnungServiceServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("[gRPC Server] Läuft auf Port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
