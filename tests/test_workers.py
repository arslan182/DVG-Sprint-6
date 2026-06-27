import asyncio
import pytest


class TestRechnungErfassen:
    def test_gibt_zeitstempel_zurueck(self):
        from src.workers.auto_workers import rechnung_erfassen
        result = asyncio.run(rechnung_erfassen(
            rechnungs_nummer="R-001",
            eingangskanal="email"
        ))
        assert result["rechnung_status"] == "erfasst"
        assert "erfassung_zeitstempel" in result

    def test_funktioniert_ohne_variablen(self):
        from src.workers.auto_workers import rechnung_erfassen
        result = asyncio.run(rechnung_erfassen())
        assert result["rechnung_status"] == "erfasst"


class TestAutomatischeValidierung:
    def test_gueltige_rechnung(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is True
        assert result["validierung_fehler"] == ""

    def test_fehlende_rechnungsnummer(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Rechnungsnummer fehlt" in result["validierung_fehler"]

    def test_ungueltige_waehrung(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="XYZ",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Betrag" not in result["validierung_fehler"]

    def test_negativer_betrag(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=-100,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False


class TestSendRequestEmail:
    def test_gibt_email_gesendet_zurueck(self):
        from src.workers.auto_workers import send_request_email
        result = asyncio.run(send_request_email(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            validierung_fehler="Betrag fehlt"
        ))
        assert result["email_gesendet"] is True
        assert "email_zeitstempel" in result

    def test_funktioniert_ohne_variablen(self):
        from src.workers.auto_workers import send_request_email
        result = asyncio.run(send_request_email())
        assert result["email_gesendet"] is True


class TestRechnungArchivieren:
    def test_gibt_archiviert_zurueck(self):
        from src.workers.auto_workers import rechnung_archivieren
        result = asyncio.run(rechnung_archivieren(
            rechnungs_nummer="R-001",
            betrag=1234.56,
            waehrung="EUR"
        ))
        assert result["archiviert"] is True
        assert "archivierungs_zeitstempel" in result

    def test_funktioniert_ohne_variablen(self):
        from src.workers.auto_workers import rechnung_archivieren
        result = asyncio.run(rechnung_archivieren())
        assert result["archiviert"] is True


class TestKiExtraktion:
    def test_pdf_nicht_gefunden(self):
        from src.workers.extraction_worker import ki_extraktion
        result = asyncio.run(ki_extraktion(
            rechnung_pdf_pfad="/nicht/vorhanden.pdf",
            rechnungs_nummer="R-001"
        ))
        assert result["ki_extraktion_erfolgreich"] is False
        assert "PDF nicht gefunden" in result["ki_extraktion_fehler"]

    def test_leerer_pdf_pfad(self):
        from src.workers.extraction_worker import ki_extraktion
        result = asyncio.run(ki_extraktion(
            rechnung_pdf_pfad="",
            rechnungs_nummer="R-001"
        ))
        assert result["ki_extraktion_erfolgreich"] is False

    def test_ohne_variablen(self):
        from src.workers.extraction_worker import ki_extraktion
        result = asyncio.run(ki_extraktion())
        assert result["ki_extraktion_erfolgreich"] is False


class TestAutomatischeValidierungGrenzfaelle:
    def test_betrag_null(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=0,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Betrag" in result["validierung_fehler"]

    def test_fehlender_lieferant(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="",
            betrag=1000,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Lieferant fehlt" in result["validierung_fehler"]

    def test_fehlendes_datum(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=1000,
            waehrung="EUR",
            datum=""
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Datum fehlt" in result["validierung_fehler"]

    def test_mehrere_fehler(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="",
            lieferant="",
            betrag=0,
            waehrung="XYZ",
            datum=""
        ))
        assert result["validierung_erfolgreich"] is False
        fehler = result["validierung_fehler"]
        assert "Rechnungsnummer fehlt" in fehler
        assert "Lieferant fehlt" in fehler

    def test_alle_waehrungen(self):
        from src.workers.auto_workers import automatische_validierung
        for waehrung in ("EUR", "USD", "CHF", "GBP"):
            result = asyncio.run(automatische_validierung(
                rechnungs_nummer="R-001",
                lieferant="Test GmbH",
                betrag=1000,
                waehrung=waehrung,
                datum="2026-06-01"
            ))
            assert result["validierung_erfolgreich"] is True
