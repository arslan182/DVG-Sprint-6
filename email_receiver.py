"""
Email Receiver – Hilfsserver für n8n Gmail-Workflow

n8n schickt nach dem Google Drive Upload den Drive-Link hierher.
Dieser Server liest die Camunda-Credentials aus der .env und startet
den Prozess über pyzeebe (gRPC) – gleiche Methode wie extraction_worker.py.

Starten:
    python email_receiver.py

Lauscht auf: http://localhost:8081/starte-prozess
"""

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from pyzeebe import ZeebeClient, create_camunda_cloud_channel

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION", "bru-2")


async def _publish_message(drive_url: str, dateiname: str, absender: str) -> None:
    """Veröffentlicht die Nachricht via pyzeebe (gRPC)."""
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    client = ZeebeClient(channel)
    await client.publish_message(
        name="Rechnung_per_Mail",
        correlation_key=dateiname,
        time_to_live_in_milliseconds=86400000,  # 24h
        variables={
            "rechnung_pdf_pfad": drive_url,
            "eingangskanal": "email",
            "absender": absender,
            "anhang_vorhanden": True,
        },
    )
    await channel.close()


def starte_camunda_prozess(drive_url: str, dateiname: str, absender: str) -> None:
    """Synchroner Wrapper für den async pyzeebe-Aufruf."""
    asyncio.run(_publish_message(drive_url, dateiname, absender))


class EmailReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/starte-prozess":
            self.send_response(404)
            self.end_headers()
            return

        laenge = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(laenge)

        try:
            daten = json.loads(body)
            drive_url  = daten["drive_url"]
            dateiname  = daten.get("dateiname", "rechnung.pdf")
            absender_raw = daten.get("absender", "unbekannt")
            # n8n kann ein Objekt {value:[{address,name}],...} oder einen String schicken
            if isinstance(absender_raw, dict):
                try:
                    absender = absender_raw["value"][0]["address"]
                except (KeyError, IndexError, TypeError):
                    absender = absender_raw.get("text", "unbekannt")
            else:
                absender = str(absender_raw)

            print(f"[Email-Receiver] Starte Prozess für: {dateiname} ({absender})")
            starte_camunda_prozess(drive_url, dateiname, absender)
            print(f"[Email-Receiver] Prozess erfolgreich gestartet!")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as e:
            print(f"[Email-Receiver] FEHLER: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "fehler": str(e)}).encode())

    def log_message(self, format, *args):
        pass  # Standard-Logging unterdrücken


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8081), EmailReceiverHandler)
    print("[Email-Receiver] Lauscht auf http://localhost:8081/starte-prozess")
    print(f"[Email-Receiver] Camunda Cluster: {CAMUNDA_CLUSTER_ID}")
    server.serve_forever()
