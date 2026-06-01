import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel

load_dotenv()

CAMUNDA_CLIENT_ID     = os.getenv("CAMUNDA_CLIENT_ID")
CAMUNDA_CLIENT_SECRET = os.getenv("CAMUNDA_CLIENT_SECRET")
CAMUNDA_CLUSTER_ID    = os.getenv("CAMUNDA_CLUSTER_ID")
CAMUNDA_REGION        = os.getenv("CAMUNDA_REGION")


async def rechnung_erfassen(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    eingangskanal    = kwargs.get("eingangskanal", "unbekannt")

    print(f"[rechnung-erfassen] {rechnungs_nummer} via {eingangskanal}")

    return {
        "erfassung_zeitstempel": datetime.now().isoformat(),
        "rechnung_status": "erfasst",
    }


async def automatische_validierung(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "")
    lieferant        = kwargs.get("lieferant", "")
    betrag           = kwargs.get("betrag", None)
    waehrung         = kwargs.get("waehrung", "")
    datum            = kwargs.get("datum", "")

    print(f"[automatische-validierung] Prüfe: {rechnungs_nummer}")

    fehler = []

    if not rechnungs_nummer:
        fehler.append("Rechnungsnummer fehlt")
    if not lieferant:
        fehler.append("Lieferant fehlt")
    if betrag is None or float(betrag) <= 0:
        fehler.append("Betrag ungültig oder fehlt")
    if waehrung not in ("EUR", "USD", "CHF", "GBP"):
        fehler.append(f"Währung ungültig: {waehrung}")
    if not datum:
        fehler.append("Datum fehlt")

    if fehler:
        print(f"[automatische-validierung] Fehler: {fehler}")
        return {
            "validierung_erfolgreich": False,
            "validierung_fehler": ", ".join(fehler),
        }

    print(f"[automatische-validierung] {rechnungs_nummer} OK")
    return {
        "validierung_erfolgreich": True,
        "validierung_fehler": "",
    }


async def compliance_check(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = float(kwargs.get("betrag", 0))
    waehrung         = kwargs.get("waehrung", "EUR").upper()

    schwellenwerte = {
        "EUR": 10000,
        "USD": 11000,
        "CHF": 10800,
        "GBP": 8700,
    }

    schwellenwert        = schwellenwerte.get(waehrung, 10000)
    compliance_notwendig = betrag > schwellenwert

    print(f"[compliance-check] {rechnungs_nummer}: {betrag} {waehrung} (Schwellenwert: {schwellenwert})")

    return {
        "compliance_notwendig": compliance_notwendig,
        "compliance_schwellenwert": schwellenwert,
    }


async def send_request_email(**kwargs):
    rechnungs_nummer   = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    lieferant          = kwargs.get("lieferant", "Unbekannter Lieferant")
    validierung_fehler = kwargs.get("validierung_fehler", "Fehlende Angaben")

    print(f"[send-request-email] Anfrage an '{lieferant}' für {rechnungs_nummer}")
    print(f"[send-request-email] Fehlende Infos: {validierung_fehler}")

    return {
        "email_gesendet": True,
        "email_zeitstempel": datetime.now().isoformat(),
    }


async def rechnung_archivieren(**kwargs):
    rechnungs_nummer = kwargs.get("rechnungs_nummer", "UNBEKANNT")
    betrag           = kwargs.get("betrag", 0)
    waehrung         = kwargs.get("waehrung", "EUR")

    print(f"[rechnung-archivieren] {rechnungs_nummer}, {betrag} {waehrung}")

    return {
        "archiviert": True,
        "archivierungs_zeitstempel": datetime.now().isoformat(),
    }


async def main():
    channel = create_camunda_cloud_channel(
        client_id=CAMUNDA_CLIENT_ID,
        client_secret=CAMUNDA_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION,
    )
    worker = ZeebeWorker(channel)

    worker.task(task_type="rechnung-erfassen")(rechnung_erfassen)
    worker.task(task_type="automatische-validierung")(automatische_validierung)
    worker.task(task_type="compliance-check")(compliance_check)
    worker.task(task_type="send-request-email")(send_request_email)
    worker.task(task_type="rechnung-archivieren")(rechnung_archivieren)

    print(f"[Auto Workers] Cluster: {CAMUNDA_CLUSTER_ID}")
    print("[Auto Workers] Wartet auf Jobs...")

    await worker.work()


if __name__ == "__main__":
    asyncio.run(main())
