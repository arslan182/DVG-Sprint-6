import os
import pika
import json
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "invoice_db")
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secretpassword")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))

RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER     = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")

# Connection pool shared across all message callbacks.
_db_pool: pool.SimpleConnectionPool | None = None


def _get_pool() -> pool.SimpleConnectionPool:
    """Returns the shared DB connection pool, creating it on first call."""
    global _db_pool
    if _db_pool is None:
        _db_pool = pool.SimpleConnectionPool(
            DB_POOL_MIN, DB_POOL_MAX,
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    return _db_pool


def update_invoice_status(rechnungs_nummer):
    """Sets the invoice status to BEZAHLT in the database."""
    db_pool = _get_pool()
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE invoices SET status = 'BEZAHLT' WHERE rechnungs_nummer = %s",
                (rechnungs_nummer,)
            )
            conn.commit()
        print(f"[DB] Status fuer {rechnungs_nummer} auf BEZAHLT gesetzt.")
    except Exception as e:
        conn.rollback()
        print(f"[DB] Fehler: {e}")
    finally:
        db_pool.putconn(conn)


def callback(ch, method, properties, body):
    """Processes one payment message from the queue and acknowledges it."""
    data = json.loads(body)
    r_nr = data.get("rechnungsnummer")

    print(f"[Payment] Empfangen: Rechnung {r_nr}")

    update_invoice_status(r_nr)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    """Connects to RabbitMQ and starts consuming payment orders."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    ))
    channel = connection.channel()
    channel.queue_declare(queue="zahlungs_auftraege", durable=True)
    channel.basic_consume(queue="zahlungs_auftraege", on_message_callback=callback)

    print("[Payment] Wartet auf Nachrichten...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
