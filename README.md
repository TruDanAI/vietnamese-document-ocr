# Vietnamese Document OCR + Review + Export

Working vertical skeleton for a Vietnamese business document OCR workflow.

This is the first MVP slice. It is intentionally not a chatbot, not RAG, and not
a full SaaS product.

## Scope

Current flow:

```text
Upload file
-> create document + page record
-> store original file under storage/dev/uploads
-> normalize image uploads or render PDF pages to storage/dev/pages
-> run OCR through an adapter
-> store OCR blocks with bbox + confidence
-> extract structured fields with simple rules
-> review/edit extracted fields
-> approve document
-> export JSON, CSV, or XLSX
```

Out of scope for this milestone:

- RAG/vector search
- Fanpage/Zalo/chatbot integrations
- billing or multi-tenant SaaS
- real CCCD/PII processing
- production OCR accuracy claims

The default OCR engine is `mock`, so the app works without PaddleOCR. A
PaddleOCR adapter exists behind `OCR_ENGINE=paddle` or `OCR_ENGINE=paddleocr`,
but PaddleOCR setup is optional and not required for the main demo.

## Repository Layout

```text
backend/   FastAPI API, SQLite database, OCR/extraction/export services, tests
frontend/  Next.js review UI
storage/   local dev uploads and exports
data/      safe synthetic sample documents
docs/      project notes placeholder
```

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

Default backend settings:

```text
DATABASE_URL=sqlite:///./data/dev.db
STORAGE_DIR=../storage/dev
OCR_ENGINE=mock
```

### Mock OCR Mode

Mock mode is the default and is the expected path for local development:

```powershell
$env:OCR_ENGINE="mock"
uvicorn app.main:app --reload
```

Mock OCR returns deterministic synthetic blocks. It is useful for testing the
pipeline, review UI, correction logs, and exports without installing any OCR
runtime.

### PaddleOCR Mode

PaddleOCR is optional. Install it only when you want to test real OCR locally:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install paddleocr
$env:OCR_ENGINE="paddle"
uvicorn app.main:app --reload
```

Notes:

- Official PaddleOCR docs recommend installing the `paddleocr` package from
  PyPI for local inference.
- PaddleOCR may install large dependencies and model files on first use.
- Windows setups can fail because of PaddlePaddle/PaddleOCR wheel, Python,
  CPU/GPU, or native dependency differences. Keep `OCR_ENGINE=mock` as the
  fallback.
- This milestone does not tune PP-OCRv6 model selection. The adapter is a spike
  path, not a production OCR guarantee.

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000/documents
```

If your backend runs somewhere else:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## API Examples

Upload:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/upload" `
  -F "file=@../data/samples/invoice-synthetic.png"
```

List documents:

```powershell
curl.exe "http://127.0.0.1:8000/documents"
```

Run OCR and extraction:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/{document_id}/ocr-runs"
```

View extracted fields:

```powershell
curl.exe "http://127.0.0.1:8000/documents/{document_id}/fields"
```

Edit a field:

```powershell
curl.exe -X PATCH "http://127.0.0.1:8000/extracted-fields/{field_id}" `
  -H "Content-Type: application/json" `
  -d "{\"normalized_value\":\"CONG TY TNHH MINH AN - REVIEWED\",\"corrected_by\":\"reviewer\"}"
```

Approve:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/{document_id}/review/approve"
```

Export JSON:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/{document_id}/exports" `
  -H "Content-Type: application/json" `
  -d "{\"format\":\"json\"}"
```

Export CSV:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/{document_id}/exports" `
  -H "Content-Type: application/json" `
  -d "{\"format\":\"csv\"}"
```

Export XLSX:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/{document_id}/exports" `
  -H "Content-Type: application/json" `
  -d "{\"format\":\"xlsx\"}"
```

## Sample Documents

Safe synthetic samples live under `data/samples/`:

- `invoice-synthetic.png`
- `invoice-synthetic.pdf`
- `receipt-synthetic.png`
- `delivery-note-synthetic.png`

These files do not contain real customer, citizen ID, tax, invoice, or private
business data.

## Evaluation Dataset

Evaluation fixtures live under `data/eval/`:

```text
data/eval/
  invoice/
    invoice-synthetic.sample.json
  receipt/
    receipt-synthetic.sample.json
  delivery_note/
    delivery-note-synthetic.sample.json
  expected/
    invoice-synthetic.expected.json
    receipt-synthetic.expected.json
    delivery-note-synthetic.expected.json
```

Each `*.sample.json` declares:

```json
{
  "sample_id": "invoice-synthetic",
  "document_type": "invoice",
  "source_file": "../../samples/invoice-synthetic.png",
  "expected_file": "../expected/invoice-synthetic.expected.json"
}
```

Each expected JSON contains:

```json
{
  "fields": {
    "supplier_name": "CONG TY TNHH MINH AN",
    "tax_code": "0312345678",
    "document_number": "HD-2026-001",
    "document_date": "12/06/2026",
    "subtotal": "1000000",
    "vat_amount": "100000",
    "total_amount": "1100000",
    "currency": "VND",
    "notes": "Du lieu demo, khong phai thong tin that"
  }
}
```

## Run Evaluation

Mock mode:

```powershell
cd backend
python -m app.evaluation.run --engine mock
```

PaddleOCR mode:

```powershell
cd backend
python -m pip install paddleocr
python -m app.evaluation.run --engine paddle
```

Reports are written to:

```text
storage/dev/eval_reports/
```

The runner writes:

- JSON report: machine-readable full field comparisons.
- Markdown report: quick human-readable summary.

The frontend also has a small report list at:

```text
http://localhost:3000/evaluations
```

### How To Read Metrics

- `exact_match_accuracy`: strict value match after trimming only.
- `normalized_match_accuracy`: field-aware comparison. Money removes dots,
  commas, spaces, and currency symbols; dates normalize to ISO format; tax codes
  remove spaces/dashes; currency maps `VNĐ` to `VND`; text ignores accents,
  case, and repeated spaces.
- `missing_field_count`: expected value exists but extraction returned empty.
- `wrong_field_count`: extraction returned a value, but normalized comparison
  failed.
- document pass/fail: all expected fields pass normalized comparison.

### Current Mock Baseline

Current synthetic dataset baseline after Milestone 3 rules:

```text
Documents passed: 3/3
Exact match accuracy: 100.00%
Normalized match accuracy: 100.00%
Missing fields: 0
Wrong fields: 0
```

The key rule improvement in this milestone is treating `Thành tiền` /
`Thanh tien` as a subtotal-like value for delivery-note style documents. Without
that alias, the delivery-note subtotal fixture would be the first known miss.

## Demo Workflow

1. Start backend.
2. Start frontend.
3. Open `http://localhost:3000/documents`.
4. Upload `data/samples/invoice-synthetic.png` or `data/samples/invoice-synthetic.pdf`.
5. Open the document detail page.
6. Click `Run OCR`.
7. Review extracted fields.
8. Edit one field and click `Save`.
9. Click `Approve`.
10. Export JSON, CSV, or XLSX and download the result.

## Tests

```powershell
cd backend
pytest
```

Expected current result:

```text
7 passed
```

Frontend verification:

```powershell
cd frontend
npm audit --omit=dev
npm run build
```

## Known Limitations

- Mock OCR returns deterministic demo blocks; it does not inspect the uploaded
  file content.
- Image uploads are normalized to PNG. PDF uploads are rendered to PNG pages.
- Extraction is rule-based and only handles a narrow set of invoice, receipt,
  and delivery-note labels.
- XLSX export is intentionally simple and only includes metadata plus extracted
  fields.
- PaddleOCR mode is optional and may need local dependency troubleshooting.
- Evaluation results in mock mode measure pipeline correctness, not real OCR
  accuracy, because mock OCR emits deterministic synthetic text.
- The current dataset is too small to claim production accuracy.
- Known weak fields for real OCR are likely `supplier_name`, `notes`, and
  monetary fields when table layout splits labels and values across lines.
- No authentication or multi-user workflow yet.
- No PII workflow. Do not upload real CCCD or sensitive customer documents.
- No RAG, vector database, chatbot, Fanpage, or Zalo integration.

## Next Recommended Milestone

- Expand the synthetic evaluation dataset to 20-30 files across receipts,
  invoices, delivery notes, and price-list-like documents.
- Run PaddleOCR mode on those samples and document installation/runtime issues.
- Add document-type-specific extraction templates.
- Add correction-rate reporting from real review edits.
- Improve multi-page review UX only after evaluation shows it matters.
