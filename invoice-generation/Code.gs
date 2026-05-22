// =============================================================================
// Alexander Car Service — Invoice Generator
// Triggered by: Passenger Log form submission
// Flow: Form submit → Fill template → Export PDF → Email to customer (if provided) → Save to Drive
// =============================================================================

var CONFIG = {
  // --- Drive IDs ---
  TEMPLATE_DOC_ID: '1fzS9oFTUXMoJtOglcJ3CXs2mwk1oInRHBVFWFziCrpQ',
  INVOICE_FOLDER_ID: '1x6rXinHeEinNNQNLdO7PCYu7TFlKFCEE',

  // --- Company Details ---
  COMPANY_NAME: 'Alexander Car Service',
  COMPANY_EMAIL: 'cars@alxdr.ca',
  COMPANY_PHONE: '(519) 577-8582',
  COMPANY_ADDRESS: 'Waterloo, Ontario, Canada',

  // --- Invoice Settings ---
  INVOICE_PREFIX: 'ACS',
  CURRENCY: 'CAD'
};

// =============================================================================
// MAIN: Triggered on Passenger Log form submission
// =============================================================================
function onFormSubmit(e) {
  if (!e || !e.namedValues) {
    Logger.log('No form data received.');
    return;
  }

  var formValues = e.namedValues;

  // --- Extract Passenger Log form fields (must match exact form labels) ---
  var tripDate       = getFormValue(formValues, 'Trip Date');
  var customerName   = getFormValue(formValues, 'Customer Name');
  var companyName    = getFormValue(formValues, 'Company Name');
  var customerEmail  = getFormValue(formValues, 'Customer Email');
  var customerPhone  = getFormValue(formValues, 'Customer Phone');
  var amountCharged  = getFormValue(formValues, 'Amount Charged ($)');
  var distance       = getFormValue(formValues, 'Distance (km)');
  var passengers     = getFormValue(formValues, 'Number of Passengers');
  var paymentTerms   = getFormValue(formValues, 'Payment Terms');
  var pickUp         = getFormValue(formValues, 'Pick-up Location');
  var dropOff        = getFormValue(formValues, 'Drop-off Location');
  var notes          = getFormValue(formValues, 'Notes') || '';

  // --- Parse amounts ---
  // HST is always included in the amount charged — no separate line needed
  var total = parseFloat(String(amountCharged).replace(/[^0-9.]/g, '')) || 0;
  var formattedTotal = formatCurrency(total);

  // --- Generate invoice number ---
  var invoiceNumber = getNextInvoiceNumber();

  // --- Format dates ---
  var dateObj = tripDate ? new Date(tripDate) : new Date();
  var formattedDate = Utilities.formatDate(dateObj, 'America/Toronto', 'MMMM d, yyyy');
  var dueDate = calculateDueDate(dateObj, paymentTerms);

  // --- Build service description ---
  var serviceLines = [];
  if (pickUp && dropOff) {
    serviceLines.push(pickUp + ' \u2192 ' + dropOff);
  } else if (pickUp) {
    serviceLines.push('From: ' + pickUp);
  } else if (dropOff) {
    serviceLines.push('To: ' + dropOff);
  }
  if (distance) {
    serviceLines.push('Distance: ' + distance + ' km');
  }
  if (passengers) {
    serviceLines.push('Passengers: ' + passengers);
  }
  var serviceDescription = serviceLines.join('\n') || 'Passenger transportation service';

  // --- Build Bill To block ---
  // If Company Name is provided, invoice is addressed: "Company Name / Attn: Customer Name"
  // If no Company Name, just: "Customer Name"
  var billToName, billToLine2;
  if (companyName) {
    billToName = companyName;       // {{company_name}} → Company Name
    billToLine2 = 'Attn: ' + customerName;  // kept separate for template
  } else {
    billToName = customerName;      // {{company_name}} → Customer Name
    billToLine2 = '';               // no Attn line needed
  }

  // --- Build replacement map ---
  var replacements = {
    '{{invoice_number}}': invoiceNumber,
    '{{date}}': formattedDate,
    '{{due_date}}': dueDate,
    '{{customer_name}}': customerName,
    '{{customer_email}}': customerEmail,
    '{{customer_phone}}': customerPhone,
    '{{company_name}}': billToName,
    '{{service_description}}': serviceDescription,
    '{{total}}': formattedTotal,
    '{{payment_terms}}': paymentTerms || 'Net 30',
    '{{notes}}': notes,
    '{{company_email}}': CONFIG.COMPANY_EMAIL,
    '{{company_phone}}': CONFIG.COMPANY_PHONE,
    '{{company_address}}': CONFIG.COMPANY_ADDRESS
  };

  // --- Process template ---
  try {
    var pdfBlob = generateInvoicePDF(replacements, billToLine2, invoiceNumber);

    // Only send email if customer email was provided
    if (customerEmail) {
      sendInvoiceEmail(customerEmail, customerName, companyName, invoiceNumber, pdfBlob, customerPhone);
      Logger.log('Invoice ' + invoiceNumber + ' sent to ' + customerEmail);
    } else {
      Logger.log('Invoice ' + invoiceNumber + ' generated (no customer email provided — skipped sending)');
    }
  } catch (error) {
    Logger.log('Error: ' + error.message);
    // Notify company about the failure
    MailApp.sendEmail({
      to: CONFIG.COMPANY_EMAIL,
      subject: '\u26A0\uFE0F Invoice Generation Failed \u2014 ' + invoiceNumber,
      body: 'Invoice could not be sent.\n\nError: ' + error.message +
            '\n\nCustomer: ' + customerName +
            (customerEmail ? ' (' + customerEmail + ')' : '') +
            (companyName ? '\nCompany: ' + companyName : '') +
            '\nInvoice #: ' + invoiceNumber +
            '\n\nPlease process manually.'
    });
  }
}

// =============================================================================
// Generate PDF from template
// =============================================================================
function generateInvoicePDF(replacements, billToLine2, invoiceNumber) {
  // Copy template
  var templateDocId = CONFIG.TEMPLATE_DOC_ID;
  var copyTitle = 'Invoice ' + invoiceNumber;
  var copy = DriveApp.getFileById(templateDocId).makeCopy(copyTitle);
  var copyDocId = copy.getId();

  // Open copy and replace placeholders
  var doc = DocumentApp.openById(copyDocId);
  var body = doc.getBody();

  // Replace all standard placeholders FIRST
  for (var placeholder in replacements) {
    body.replaceText(placeholder, replacements[placeholder]);
  }

  // Handle the Bill To section:
  // Template has: {{company_name}}\nAttn: {{customer_name}}
  // If companyName was provided: company_name is already replaced, and
  //   {{customer_name}} is replaced. "Attn:" line stays — perfect.
  // If no companyName: we need to collapse "Attn: John" into just "John"
  //   and remove the extra line, so it shows only the customer name.
  if (!billToLine2) {
    // No company — remove "Attn: " prefix, leaving just the customer name
    body.replaceText('Attn:\\s*', '');
  }

  // Handle empty customer email — remove the line cleanly
  if (!replacements['{{customer_email}}'] || replacements['{{customer_email}}'].trim() === '') {
    body.replaceText('{{customer_email}}', '');
  }

  // Handle empty customer phone — remove the line cleanly
  if (!replacements['{{customer_phone}}'] || replacements['{{customer_phone}}'].trim() === '') {
    body.replaceText('{{customer_phone}}', '');
  }

  // Handle empty notes — remove the line cleanly
  if (!replacements['{{notes}}'] || replacements['{{notes}}'].trim() === '') {
    body.replaceText('{{notes}}', '');
  }

  doc.saveAndClose();

  // Move to Invoices folder
  var folder = DriveApp.getFolderById(CONFIG.INVOICE_FOLDER_ID);
  DriveApp.getFileById(copyDocId).moveTo(folder);

  // Export as PDF
  var pdfExportUrl = 'https://docs.google.com/document/d/' + copyDocId + '/export?format=pdf';
  var response = UrlFetchApp.fetch(pdfExportUrl, {
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }
  });

  var pdfBlob = response.getBlob().setName(copyTitle + '.pdf');

  // Keep the Docs copy in the folder too (useful for re-edits)
  // Uncomment the next line to delete the Docs copy and keep only the PDF:
  // DriveApp.getFileById(copyDocId).setTrashed(true);

  return pdfBlob;
}

// =============================================================================
// Send invoice email
// =============================================================================
function sendInvoiceEmail(customerEmail, customerName, companyName, invoiceNumber, pdfBlob, customerPhone) {
  var displayName = companyName || customerName;
  var subject = 'Invoice ' + invoiceNumber + ' \u2014 ' + CONFIG.COMPANY_NAME;
  var body = [
    'Dear ' + customerName + ',',
    '',
    'Please find attached Invoice ' + invoiceNumber + ' from ' + CONFIG.COMPANY_NAME + '.',
    '',
    'If you have any questions regarding this invoice, please don\'t hesitate to contact us at ' + CONFIG.COMPANY_EMAIL + ' or ' + CONFIG.COMPANY_PHONE + '.',
    '',
    'Payment may be made by e-Transfer to ' + CONFIG.COMPANY_EMAIL + '.',
    '',
    'Thank you for choosing Alexander Car Service.',
    '',
    'Best regards,',
    CONFIG.COMPANY_NAME,
    CONFIG.COMPANY_PHONE,
    CONFIG.COMPANY_EMAIL
  ].join('\n');

  MailApp.sendEmail({
    to: customerEmail,
    cc: CONFIG.COMPANY_EMAIL,
    subject: subject,
    body: body,
    attachments: [pdfBlob]
  });
}

// =============================================================================
// Invoice number generator (sequential, resets yearly)
// =============================================================================
function getNextInvoiceNumber() {
  var props = PropertiesService.getScriptProperties();
  var currentYear = new Date().getFullYear();
  var storedData = JSON.parse(props.getProperty('invoiceCounter') || '{}');

  var lastYear = storedData.year || 0;
  var lastNumber = storedData.number || 0;

  var newNumber;
  if (currentYear !== lastYear) {
    newNumber = 1;
  } else {
    newNumber = lastNumber + 1;
  }

  props.setProperty('invoiceCounter', JSON.stringify({
    year: currentYear,
    number: newNumber
  }));

  return CONFIG.INVOICE_PREFIX + '-' + currentYear + '-' + padZero(newNumber, 4);
}

function padZero(num, length) {
  var str = String(num);
  while (str.length < length) { str = '0' + str; }
  return str;
}

// =============================================================================
// Utility functions
// =============================================================================
function formatCurrency(amount) {
  return '$' + amount.toFixed(2) + ' ' + CONFIG.CURRENCY;
}

function calculateDueDate(invoiceDate, paymentTerms) {
  var date = invoiceDate ? new Date(invoiceDate) : new Date();
  var days;

  switch (paymentTerms) {
    case 'Net 15': days = 15; break;
    case 'Net 30': days = 30; break;
    case 'Due on Receipt': days = 0; break;
    case 'COD': days = 0; break;
    default: days = 30;
  }

  if (days > 0) {
    date.setDate(date.getDate() + days);
    return Utilities.formatDate(date, 'America/Toronto', 'MMMM d, yyyy');
  }
  return 'Due on Receipt';
}

function getFormValue(values, key) {
  var val = values[key];
  if (Array.isArray(val)) return val[0] || '';
  return val || '';
}

// =============================================================================
// Manual test — run from Apps Script editor
// =============================================================================
function testInvoice() {
  // Test 1: Invoice WITH company name, email, and phone
  var mockValuesWithCompany = {
    'Trip Date': ['2026-05-18'],
    'Customer Name': ['John Smith'],
    'Company Name': ['Acme Corporation'],
    'Customer Email': ['billing@acmecorp.com'],
    'Customer Phone': ['(416) 555-0199'],
    'Amount Charged ($)': ['275.00'],
    'Distance (km)': ['85'],
    'Number of Passengers': ['1'],
    'Payment Terms': ['Net 30'],
    'Pick-up Location': ['Waterloo, ON'],
    'Drop-off Location': ['Toronto Pearson International Airport'],
    'Notes': ['Round trip — executive sedan service']
  };
  var mockEvent = { namedValues: mockValuesWithCompany };
  onFormSubmit(mockEvent);
}

// Test 2: Invoice WITHOUT company name or email (personal customer)
function testInvoicePersonal() {
  var mockValuesPersonal = {
    'Trip Date': ['2026-05-19'],
    'Customer Name': ['Jane Doe'],
    'Company Name': [''],
    'Customer Email': [''],
    'Customer Phone': [''],
    'Amount Charged ($)': ['150.00'],
    'Distance (km)': ['45'],
    'Number of Passengers': ['2'],
    'Payment Terms': ['Due on Receipt'],
    'Pick-up Location': ['Kitchener, ON'],
    'Drop-off Location': ['Hamilton, ON'],
    'Notes': ['']
  };
  var mockEvent = { namedValues: mockValuesPersonal };
  onFormSubmit(mockEvent);
}