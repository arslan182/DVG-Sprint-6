import grpc
import pika
import json
import os
import sys
from dotenv import load_dotenv

from invoice_metadata import invoice_pb2
from invoice_metadata import invoice_pb2_grpc

load_dotenv()

GRPC_HOST         = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT         = os.getenv("GRPC_PORT", "50051")
RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER     = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")

TEST_RECHNUNGS_NUMMER = os.getenv("TEST_RECHNUNGS_NUMMER", "R-TEST-001")
TEST_LIEFERANT        = os.getenv("TEST_LIEFERANT", "Test GmbH")
TEST_BETRAG           = float(os.getenv("TEST_BETRAG", "99.99"))
TEST_WAEHRUNG         = os.getenv("TEST_WAEHRUNG", "EUR")
TEST_DATUM            = os.getenv("TEST_DATUM", "2026-01-01")


def run():
    """Sends a test invoice via gRPC and then queues a payment via RabbitMQ."""
    channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
    stub = invoice_pb2_grpc.RechnungServiceStub(channel)

    request = invoice_pb2.RechnungRequest(
        rechnungs_nummer=TEST_RECHNUNGS_NUMMER,
        lieferant=TEST_LIEFERANT,
        betrag=TEST_BETRAG,
        waehrung=TEST_WAEHRUNG,
        datum=TEST_DATUM,
        status=invoice_pb2.OFFEN
    )

    try:
        response = stub.SpeichereMetadaten(request)
        print("gRPC Antwort vom Server:")
        print(f"Erfolg: {response.erfolg}, Nachricht: {response.nachricht}")

        if response.erfolg:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    credentials=credentials
                )
            )
            mq_channel = connection.channel()
            mq_channel.queue_declare(queue="zahlungs_auftraege", durable=True)

            zahlungs_daten = {
                "rechnungsnummer": request.rechnungs_nummer,
                "betrag": request.betrag,
                "waehrung": request.waehrung
            }

            mq_channel.basic_publish(
                exchange="",
                routing_key="zahlungs_auftraege",
                body=json.dumps(zahlungs_daten),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            print(f"RabbitMQ: Zahlungsauftrag fuer {request.rechnungs_nummer} gesendet.")
            connection.close()

    except grpc.RpcError as e:
        print(f"Fehler: gRPC Server nicht erreichbar ({e.details()})")
    except Exception as e:
        print(f"Allgemeiner Fehler: {e}")


if __name__ == "__main__":
    run()
