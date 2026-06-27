import asyncio
import json
import os
import pika
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
from pyzeebe.errors import BusinessError

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER     = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")

# Persistent RabbitMQ connection and channel shared across all jobs.
_mq_connection: pika.BlockingConnection | None = None
_mq_channel: pika.adapters.blocking_connection.BlockingChannel | None = None


def _get_mq_channel():
    """Returns a shared RabbitMQ channel, reconnecting if the connection is closed."""
    global _mq_connection, _mq_channel
    if _mq_connection is None or _mq_connection.is_closed:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        _mq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        _mq_channel = _mq_connection.channel()
        _mq_channel.queue_declare(queue="zahlungs_auftraege", durable=True)
    return _mq_channel


async def initiate_payment(
    rechnungs_nummer: str,
    betrag: float,
    waehrung: str,
):
    """Publishes a payment order to the RabbitMQ queue.

    The message is durable so it survives a broker restart.
    Raises BusinessError if RabbitMQ is unreachable.
    """
    print(f"[Payment Worker] Zahlung fuer: {rechnungs_nummer}")

    try:
        mq_channel = _get_mq_channel()

        zahlungs_daten = {
            "rechnungsnummer": rechnungs_nummer,
            "betrag": float(betrag),
            "waehrung": waehrung
        }

        mq_channel.basic_publish(
            exchange="",
            routing_key="zahlungs_auftraege",
            body=json.dumps(zahlungs_daten),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f"[Payment Worker] Auftrag gesendet: {rechnungs_nummer}")
        return {"zahlung_erfolg": True, "zahlung_nachricht": f"Zahlungsauftrag fuer {rechnungs_nummer} gesendet"}

    except Exception as e:
        print(f"[Payment Worker] Fehler: {e}")
        raise BusinessError(error_code="rabbitmq-fehler", msg=f"RabbitMQ nicht erreichbar: {e}")


async def main():
    """Connects to Camunda and registers the initiate-payment task handler."""
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    worker.task(task_type="initiate-payment")(initiate_payment)

    print(f"[Payment Worker] Cluster: {CAMUNDA_CLUSTER_ID}")
    print("[Payment Worker] Wartet auf Jobs...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
