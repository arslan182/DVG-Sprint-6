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


async def initiate_payment(
    rechnungs_nummer: str,
    betrag: float,
    waehrung: str,
):
    print(f"[Payment Worker] Zahlung für: {rechnungs_nummer}")

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue="zahlungs_auftraege", durable=True)

        zahlungs_daten = {
            "rechnungsnummer": rechnungs_nummer,
            "betrag": float(betrag),
            "waehrung": waehrung
        }

        channel.basic_publish(
            exchange="",
            routing_key="zahlungs_auftraege",
            body=json.dumps(zahlungs_daten),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()

        print(f"[Payment Worker] Auftrag gesendet: {rechnungs_nummer}")
        return {"zahlung_erfolg": True, "zahlung_nachricht": f"Zahlungsauftrag für {rechnungs_nummer} gesendet"}

    except Exception as e:
        print(f"[Payment Worker] Fehler: {e}")
        raise BusinessError(error_code="rabbitmq-fehler", msg=f"RabbitMQ nicht erreichbar: {e}")


async def main():
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
