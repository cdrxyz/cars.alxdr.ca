# Invoice Generation

Automated invoice system for Alexander Car Service: Google Form submission → PDF → Email → Drive.

## Architecture

```
Passenger Log Form (submission)
       ↓
Apps Script (onFormSubmit trigger on the responses spreadsheet)
       ↓
Invoice Template Doc ({{placeholders}} replaced with real data)
       ↓
Export as PDF → Email to customer (cc: cars@alxdr.ca)
       ↓
Save PDF + Doc copy to Invoices folder in Drive
```

## Prerequisites

- A Google account that owns the Passenger Log form and its linked spreadsheet
- The Invoice Template Doc and Invoices folder must already exist in Drive (they were created during initial setup)

## Setup

### 1. Open the Apps Script editor

1. Open the **Passenger Log (Responses)** spreadsheet:
   ```
   https://docs.google.com/spreadsheets/d/1MsP4YsBocM_wsWBDsWawkrfbQe3_6NS1CSoXMM-VPjA
   ```
2. Click **Extensions → Apps Script**
3. Delete any existing code in the editor (if present)
4. Copy the entire contents of `Code.gs` from this directory and paste it in
5. In the `CONFIG` object at the top, update **`HST_NUMBER`** with your Ontario HST registration number:
   ```javascript
   HST_NUMBER: '123456789 RT0001',  // Replace with your actual number
   ```
6. Click **Save** (💾)

### 2. Set up the trigger

1. In Apps Script, click the **clock icon** (⚙️ Triggers) in the left sidebar
2. Click **+ Add Trigger** (bottom right)
3. Configure:
   - Choose function: **`onFormSubmit`**
   - Event source: **From spreadsheet**
   - Event type: **On form submit**
4. Click **Save**
5. Authorize when prompted — sign in with the Google account that owns the form and grant the required permissions

### 3. Test

Run one of the test functions from the Apps Script editor:

- **`testInvoice()`** — Tests **with** a company name (Acme Corporation / Attn: John Smith)
- **`testInvoicePersonal()`** — Tests **without** a company name (just Jane Doe, personal invoice)

After running:
- Check the **Invoices folder** for the generated Doc and PDF:  
  `https://drive.google.com/drive/folders/1x6rXinHeEinNNQNLdO7PCYu7TFlKFCEE`
- Check **cars@alxdr.ca** for the email with the PDF attachment

## How It Works

### Form Fields

The Passenger Log form collects:

| Field | Purpose |
|---|---|
| Trip Date | Date on the invoice |
| Customer Name | Contact person (or sole recipient if no company) |
| **Company Name** *(optional)* | When provided, the invoice is billed to the company with Customer Name as "Attn:" |
| Customer Email | Invoice recipient |
| Amount Charged ($) | Base amount before HST |
| Distance (km) | Shown on invoice description |
| Number of Passengers | Shown on invoice description |
| Payment Terms | Net 30 / Net 15 / Due on Receipt / COD |
| HST (13%) Included? | Yes = HST back-calculated from total; No = HST added on top |
| Pick-up / Drop-off | Shown in service description |
| Notes | Additional invoice notes |

### Bill To Logic

- **Company Name provided** → Invoice shows:
  ```
  Bill To:
  Acme Corporation
  Attn: John Smith
  ```
- **No Company Name** → Invoice shows:
  ```
  Bill To:
  Jane Doe
  ```

### Invoice Numbers

Format: `ACS-YYYY-NNNN` — sequential within each calendar year, stored in Apps Script Properties.

### HST Calculation

- **"No" (HST not included)**: `Total = Subtotal + HST` — HST added on top
- **"Yes" (HST included)**: `Subtotal = Total ÷ 1.13`, `HST = Total - Subtotal` — amounts back-calculated

## Key Resource IDs

| Resource | ID |
|---|---|
| Template Doc | `1fzS9oFTUXMoJtOglcJ3CXs2mwk1oInRHBVFWFziCrpQ` |
| Invoices Folder | `1x6rXinHeEinNNQNLdO7PCYu7TFlKFCEE` |
| Passenger Log Form | `1zu-ffjGUiVzSkPLkm3IUEnWYs8qAjCdoMTh8CpoAu8s` |
| Responses Spreadsheet | `1MsP4YsBocM_wsWBDsWawkrfbQe3_6NS1CSoXMM-VPjA` |

## Customizing the Template

Edit the [Invoice Template Doc](https://docs.google.com/document/d/1fzS9oFTUXMoJtOglcJ3CXs2mwk1oInRHBVFWFziCrpQ) directly in Google Docs. You can change fonts, spacing, layout, and the logo — just **do not modify the `{{placeholder}}` text** or the script will fail to replace them.

Available placeholders: `{{invoice_number}}`, `{{date}}`, `{{due_date}}`, `{{company_name}}`, `{{customer_name}}`, `{{service_description}}`, `{{subtotal}}`, `{{hst_amount}}`, `{{total}}`, `{{payment_terms}}`, `{{notes}}`, `{{company_email}}`, `{{company_phone}}`, `{{company_address}}`, `{{hst_number}}`

## Troubleshooting

| Problem | Fix |
|---|---|
| Emails not sending | Check Apps Script executions log for errors; re-authorize if prompted |
| Wrong amounts | Verify HST calculation mode — "Yes" means HST is already in the charged amount |
| Trigger not firing | Go to Triggers → verify `onFormSubmit` is set on "From spreadsheet → On form submit" |
| `NOT_AUTHENTICATED` error | Re-authorize the script (Triggers → click the authorization link) |
| Invoice numbers resetting | Script Properties store the counter per year — check `PropertiesService.getScriptProperties()` |