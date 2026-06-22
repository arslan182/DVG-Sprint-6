import asyncio
import grpc
import sys
import os
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
from pyzeebe.errors import BusinessError

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invoice_metadata import invoice_pb2
from invoice_metadata import invoice_pb2_grpc

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = int(os.getenv("GRPC_PORT", 50051))


async def save_metadata(
    rechnungs_nummer: str,
    lieferant: str,
    betrag: float,
    waehrung: str,
    datum: str,
):
    """Sends invoice metadata to the gRPC server for storage in PostgreSQL.

    Raises BusinessError if the gRPC server is unreachable so Camunda
    can handle the incident.
    """
    print(f"[gRPC Worker] Speichere Metadaten: {rechnungs_nummer}")

    try:
        channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
        stub = invoice_pb2_grpc.RechnungServiceStub(channel)

        request = invoice_pb2.RechnungRequest(
            rechnungs_nummer=rechnungs_nummer,
            lieferant=lieferant,
            betrag=float(betrag),
            waehrung=waehrung,
            datum=datum,
            status=invoice_pb2.OFFEN
        )

        response = stub.SpeichereMetadaten(request)

        if response.erfolg:
            print(f"[gRPC Worker] Gespeichert: {response.nachricht}")
            return {"grpc_erfolg": True, "grpc_nachricht": response.nachricht}
        else:
            print(f"[gRPC Worker] Fehler: {response.nachricht}")
            raise Exception(f"gRPC Fehler: {response.nachricht}")

    except grpc.RpcError as e:
        print(f"[gRPC Worker] Nicht erreichbar: {e.details()}")
        raise BusinessError(error_code="grpc-fehler", msg=f"gRPC nicht erreichbar: {e.details()}")

    finally:
        channel.close()


async def main():
    """Connects to Camunda and registers the save-invoice-metadata task handler."""
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    worker.task(task_type="save-invoice-metadata")(save_metadata)

    print(f"[gRPC Worker] Cluster: {CAMUNDA_CLUSTER_ID}")
    print("[gRPC Worker] Wartet auf Jobs...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
