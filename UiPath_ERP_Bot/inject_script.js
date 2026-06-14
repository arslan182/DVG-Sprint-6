// UiPath Inject Js Script – ERP Rechnungserfassung
// Ziel: https://anhe0003.github.io/this-and-that/ERP_Rechnungserfassung.html
//
// Input Arguments vom Camunda Worker:
//   input.rechnungs_nummer    → invoiceNumber
//   input.lieferant           → customerName
//   input.datum               → invoiceDate (YYYY-MM-DD)
//   input.eingangskanal       → invoiceNotes
//   input.betrag              → Fallback-Betrag wenn keine Positionen
//   input.rechnungspositionen → JSON-Array mit Positionen (Sprint 6)

function (element, input) {

  // 1. Neue Rechnung starten (setzt Formular zurück)
  newInvoice();

  // 2. Stammdaten befüllen
  document.getElementById('invoiceNumber').value  = input.rechnungs_nummer || '';
  document.getElementById('customerName').value   = input.lieferant || '';
  document.getElementById('invoiceNotes').value   = 'Eingangskanal: ' + (input.eingangskanal || 'Email');

  // Datum: Camunda liefert "YYYY-MM-DD" → passt direkt für type="date"
  if (input.datum) {
    document.getElementById('invoiceDate').value = input.datum;
  } else {
    document.getElementById('invoiceDate').value = new Date().toISOString().split('T')[0];
  }

  // 3. Rechnungspositionen hinzufügen
  var positionen = [];
  try {
    if (input.rechnungspositionen) {
      positionen = typeof input.rechnungspositionen === 'string'
        ? JSON.parse(input.rechnungspositionen)
        : input.rechnungspositionen;
    }
  } catch (e) {
    positionen = [];
  }

  // Bestehende Positionen-Zeilen entfernen
  document.getElementById('itemsBody').innerHTML = '';
  itemRowCounter = 0;

  if (positionen.length > 0) {
    // Sprint 6: KI-extrahierte Positionen eintragen
    positionen.forEach(function (pos) {
      addItemRow();
      var rows = document.querySelectorAll('#itemsBody tr');
      var row  = rows[rows.length - 1];
      row.querySelector('.desc').value  = pos.beschreibung || '';
      row.querySelector('.qty').value   = pos.menge        || 1;
      row.querySelector('.unit').value  = pos.einheit      || 'Stk.';
      row.querySelector('.price').value = pos.einzelpreis  || 0;
      row.querySelector('.qty').dispatchEvent(new Event('input', { bubbles: true }));
    });
  } else {
    // Fallback (Sprint 5): eine Position mit dem Gesamtbetrag
    addItemRow();
    var rows = document.querySelectorAll('#itemsBody tr');
    var row  = rows[rows.length - 1];
    row.querySelector('.desc').value  = 'Rechnungsbetrag';
    row.querySelector('.qty').value   = 1;
    row.querySelector('.price').value = input.betrag || 0;
    row.querySelector('.qty').dispatchEvent(new Event('input', { bubbles: true }));
  }

  // 4. Summen neu berechnen
  recalculateTotals();

  // 5. Rechnung speichern (LocalStorage)
  saveCurrentInvoice();
}
