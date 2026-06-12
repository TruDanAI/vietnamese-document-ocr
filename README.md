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
- No authentication or multi-user workflow yet.
- No PII workflow. Do not upload real CCCD or sensitive customer documents.
- No RAG, vector database, chatbot, Fanpage, or Zalo integration.

## Next Recommended Milestone

- Verify PaddleOCR on a small Vietnamese sample set and record install issues.
- Add field-level confidence and correction-rate reporting.
- Improve bbox overlay for multi-page PDFs.
- Add document-type-specific extraction templates.
- Add a small evaluation command for sample OCR/extraction fixtures.
