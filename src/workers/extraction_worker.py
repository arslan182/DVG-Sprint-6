"""
Sprint 6 – AI Extraction Worker
Camunda Task: ki-extraktion

Ablauf:
  1. Camunda picked den Task "ki-extraktion"
  2. Worker liest den PDF-Pfad aus den Prozessvariablen
  3. Schickt die PDF-Datei an den n8n Webhook
  4. n8n extrahiert per Google Gemini die Rechnungsdaten
  5. Worker gibt die extrahierten Variablen an Camunda zurück
  6. Camunda zeigt die Daten im User Task "Extrahierte Daten prüfen" an
"""

import asyncio
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


async def ki_extraktion(**kwargs):
    """
    Camunda Service Task: ki-extraktion

    Erwartete Prozessvariablen:
      - rechnung_pdf_pfad (String): Lokaler Pfad zur PDF-Datei
                                    z.B. "rechnungen/RE-2026-001.pdf"
      - rechnungs_nummer  (String, optional): Rechnungsnummer als Fallback

    Zurückgegebene Variablen:
      - rechnungs_nummer          (String)
      - lieferant                 (String)
      - betrag                    (Number)
      - waehrung                  (String)
      - datum                     (String, YYYY-MM-DD)
      - eingangskanal             (String)
      - rechnungspositionen       (String, JSON-kodiertes Array)
      - ki_extraktion_erfolgreich (Boolean)
      - ki_extraktion_zeitstempel (String)
    """
    pdf_pfad         = kwargs.get("rechnung_pdf_pfad", "")
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")

    print(f"[ki-extraktion] Starte für {rechnungs_nummer}, PDF: {pdf_pfad}")

    if not pdf_pfad or not os.path.isfile(pdf_pfad):
        print(f"[ki-extraktion] WARNUNG: PDF nicht gefunden: {pdf_pfad}")
        print(f"[ki-extraktion] Überspringe AI-Extraktion, Felder bleiben leer.")
        return {
            "ki_extraktion_erfolgreich": False,
            "ki_extraktion_fehler": f"PDF nicht gefunden: {pdf_pfad}",
        }

    print(f"[ki-extraktion] Sende PDF an n8n: {N8N_WEBHOOK_URL}")

    async with httpx.AsyncClient(timeout=N8N_TIMEOUT_SECONDS) as client:
        with open(pdf_pfad, "rb") as f:
            pdf_bytes = f.read()

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

    import json
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
    }


async def main():
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
