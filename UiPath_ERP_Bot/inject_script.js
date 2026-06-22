// UiPath Inject JS Script – ERP Rechnungserfassung
// Target: https://anhe0003.github.io/this-and-that/ERP_Rechnungserfassung.html
//
// Called by UiPath with invoice data from Camunda:
//   input.rechnungs_nummer    → invoiceNumber field
//   input.lieferant           → customerName field
//   input.datum               → invoiceDate (YYYY-MM-DD)
//   input.eingangskanal       → invoiceNotes field
//   input.betrag              → fallback total when no line items are present
//   input.rechnungspositionen → JSON array of line items

function (element, input) {

  // Reset the form if the ERP page provides a newInvoice function
  if (typeof newInvoice === 'function') { newInvoice(); }

  // Fill in the invoice header fields
  document.getElementById('invoiceNumber').value  = input.rechnungs_nummer || '';
  document.getElementById('customerName').value   = input.lieferant || '';
  document.getElementById('invoiceNotes').value   = 'Eingangskanal: ' + (input.eingangskanal || 'Email');

  // Date arrives as YYYY-MM-DD from Camunda, which matches the date input format
  if (input.datum) {
    document.getElementById('invoiceDate').value = input.datum;
  } else {
    document.getElementById('invoiceDate').value = new Date().toISOString().split('T')[0];
  }

  // Parse line items — the value may arrive as a JSON string or already as an array
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

  // Clear existing rows before filling in new data
  document.getElementById('itemsBody').innerHTML = '';
  itemRowCounter = 0;

  // Use the ERP's addItemRow if available, otherwise build the row manually
  function safeAddItemRow() {
    if (typeof addItemRow === 'function') {
      addItemRow();
    } else {
      var tbody = document.getElementById('itemsBody');
      var tr = document.createElement('tr');
      tr.innerHTML = '<td><input class="desc" type="text"></td>' +
                     '<td><input class="qty" type="number" value="1"></td>' +
                     '<td><input class="unit" type="text" value="Stk."></td>' +
                     '<td><input class="price" type="number" value="0"></td>' +
                     '<td><span class="total">0</span></td>';
      tbody.appendChild(tr);
    }
  }

  if (positionen.length > 0) {
    positionen.forEach(function (pos) {
      safeAddItemRow();
      var rows = document.querySelectorAll('#itemsBody tr');
      var row  = rows[rows.length - 1];
      row.querySelector('.desc').value  = pos.beschreibung || '';
      row.querySelector('.qty').value   = pos.menge        || 1;
      row.querySelector('.unit').value  = pos.einheit      || 'Stk.';
      row.querySelector('.price').value = pos.einzelpreis  || 0;
      row.querySelector('.qty').dispatchEvent(new Event('input', { bubbles: true }));
    });
  } else {
    safeAddItemRow();
    var rows = document.querySelectorAll('#itemsBody tr');
    var row  = rows[rows.length - 1];
    row.querySelector('.desc').value  = 'Rechnungsbetrag';
    row.querySelector('.qty').value   = 1;
    row.querySelector('.price').value = input.betrag || 0;
    row.querySelector('.qty').dispatchEvent(new Event('input', { bubbles: true }));
  }

  if (typeof recalculateTotals === 'function') { recalculateTotals(); }
  if (typeof saveCurrentInvoice === 'function') { saveCurrentInvoice(); }
}
