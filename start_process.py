"""
Dvg – Prozess starten

Verwendung:
  python start_process.py <pfad_zur_rechnung.pdf>

Beispiele:
  python start_process.py rechnung.pdf
  python start_process.py C:/Downloads/RE-2026-001.pdf
"""

import os
import sys
import asyncio
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
from dotenv import load_dotenv

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")

PROZESS_ID = os.getenv("CAMUNDA_PROCESS_ID", "Process_workflow_sprint6")


def get_pdf_pfad() -> str:
    """Returns the PDF path from the command-line argument or prompts the user."""
    if len(sys.argv) >= 2:
        pfad = sys.argv[1]
    else:
        pfad = input("Pfad zur Rechnung (PDF): ").strip().strip('"')

    pfad = os.path.abspath(pfad)

    if not os.path.isfile(pfad):
        print(f"FEHLER: Datei nicht gefunden: {pfad}")
        sys.exit(1)

    if not pfad.lower().endswith(".pdf"):
        print(f"WARNUNG: Datei ist keine PDF: {pfad}")

    return pfad


async def main():
    """Starts a new invoice process instance in Camunda with the given PDF path."""
    pdf_pfad = get_pdf_pfad()

    variablen = {
        "rechnung_pdf_pfad":    pdf_pfad,  # AI extracts all invoice data from this file
        # Fallback values in case extraction fails
        "eingangskanal":        "email",
        "rechnungs_nummer":     "UNBEKANNT",
        "lieferant":            "",
        "betrag":               0,
        "waehrung":             "EUR",
        "datum":                "",
        "rechnung_genehmigt":   True,
        "informationen_erhalten": True,
    }

    print("\n" + "=" * 55)
    print("  Dvg Sprint 6 – Prozess starten")
    print("=" * 55)
    print(f"\n  PDF:    {pdf_pfad}")
    print(f"  Prozess: {PROZESS_ID}")
    print()

    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )

    client = ZeebeClient(channel)
    instance = await client.run_process(
        bpmn_process_id=PROZESS_ID,
        variables=variablen,
    )

    print(f"Prozess gestartet!")
    print(f"Process Instance Key: {instance.process_instance_key}")
    print(f"Operate: https://{CAMUNDA_REGION}.operate.camunda.io/{CAMUNDA_CLUSTER_ID}/operate/processes/{instance.process_instance_key}")

    await channel.close()


if __name__ == "__main__":
    asyncio.run(main())
