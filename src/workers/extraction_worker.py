"""
AI Extraction Worker – Camunda Task: ki-extraktion

Picks up the "ki-extraktion" job from Camunda, sends the PDF to the n8n webhook,
and returns the Gemini-extracted invoice fields back to the process.
"""

import asyncio
import json
import os
import httpx
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/rechnungsextraktion"
)
N8N_TIMEOUT_SECONDS = int(os.getenv("N8N_TIMEOUT_SECONDS", "60"))


async def lade_pdf_bytes(pdf_pfad: str) -> bytes:
    """Lädt PDF-Bytes – entweder von Google Drive URL oder vom lokalen Dateisystem."""
    if pdf_pfad.startswith("http://") or pdf_pfad.startswith("https://"):
        print(f"[ki-extraktion] Lade PDF von URL: {pdf_pfad}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(pdf_pfad, follow_redirects=True)
            if response.status_code != 200:
                raise Exception(f"PDF-Download fehlgeschlagen: HTTP {response.status_code}")
            return response.content
    else:
        print(f"[ki-extraktion] Lese PDF lokal: {pdf_pfad}")
        with open(pdf_pfad, "rb") as f:
            return f.read()


async def ki_extraktion(**kwargs):
    """Sends the PDF to the n8n/Gemini webhook and returns extracted invoice data.

    Reads 'rechnung_pdf_pfad' from process variables (local path or Google Drive URL),
    posts the file to n8n, and maps the JSON response back to Camunda process variables.
    Returns ki_extraktion_erfolgreich=False if the PDF is missing.
    """
    pdf_pfad         = kwargs.get("rechnung_pdf_pfad", "")
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")

    print(f"[ki-extraktion] Starte für {rechnungs_nummer}, PDF: {pdf_pfad}")

    ist_url = pdf_pfad.startswith("http://") or pdf_pfad.startswith("https://")

    if not pdf_pfad or (not ist_url and not os.path.isfile(pdf_pfad)):
        print(f"[ki-extraktion] WARNUNG: PDF nicht gefunden: {pdf_pfad}")
        print(f"[ki-extraktion] Überspringe AI-Extraktion, Felder bleiben leer.")
        return {
            "ki_extraktion_erfolgreich": False,
            "ki_extraktion_fehler": f"PDF nicht gefunden: {pdf_pfad}",
            "anhang_vorhanden": False,
        }

    print(f"[ki-extraktion] Sende PDF an n8n: {N8N_WEBHOOK_URL}")

    async with httpx.AsyncClient(timeout=N8N_TIMEOUT_SECONDS) as client:
        pdf_bytes = await lade_pdf_bytes(pdf_pfad)

        response = await client.post(
            N8N_WEBHOOK_URL,
            content=pdf_bytes,
            headers={"Content-Type": "application/pdf"},
        )

        if response.status_code != 200:
            raise Exception(
                f"n8n Webhook Fehler: HTTP {response.status_code} – {response.text[:300]}"
            )

        data = response.json()
        print(f"[ki-extraktion] Extraktion erfolgreich: {data}")

    return {
        "rechnungs_nummer":          data.get("rechnungs_nummer", rechnungs_nummer),
        "lieferant":                 data.get("lieferant", ""),
        "betrag":                    float(data.get("betrag", 0)),
        "waehrung":                  data.get("waehrung", "EUR"),
        "datum":                     data.get("datum", ""),
        "eingangskanal":             data.get("eingangskanal", "Email"),
        "rechnungspositionen":       json.dumps(
                                         data.get("rechnungspositionen", []),
                                         ensure_ascii=False
                                     ),
        "ki_extraktion_erfolgreich": True,
        "ki_extraktion_zeitstempel": data.get("ki_extraktion_zeitstempel", ""),
        "anhang_vorhanden":          True,
    }


async def main():
    """Connects to Camunda and starts listening for ki-extraktion jobs."""
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    worker.task(task_type="ki-extraktion")(ki_extraktion)

    print(f"[Extraction Worker] Cluster:      {CAMUNDA_CLUSTER_ID}")
    print(f"[Extraction Worker] n8n Webhook:  {N8N_WEBHOOK_URL}")
    print("[Extraction Worker] Wartet auf Jobs...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
