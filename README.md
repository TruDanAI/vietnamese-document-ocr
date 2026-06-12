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
-> run OCR through an adapter
-> store OCR blocks with bbox + confidence
-> extract structured fields with simple rules
-> review/edit extracted fields
-> approve document
-> export JSON or CSV
```

Out of scope for this milestone:

- RAG/vector search
- Fanpage/Zalo/chatbot integrations
- billing or multi-tenant SaaS
- real CCCD/PII processing
- production OCR accuracy claims

The default OCR engine is `mock`, so the app works without PaddleOCR. A
PaddleOCR adapter stub exists behind `OCR_ENGINE=paddleocr`, but PaddleOCR setup
is not required for the skeleton.

## Repository Layout

```text
backend/   FastAPI API, SQLite database, OCR/extraction/export services, tests
frontend/  Next.js review UI
storage/   local dev uploads and exports
data/      sample data placeholder
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
  -F "file=@sample.txt"
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

## Demo Workflow

1. Start backend.
2. Start frontend.
3. Open `http://localhost:3000/documents`.
4. Upload any small demo file.
5. Open the document detail page.
6. Click `Run OCR`.
7. Review extracted fields.
8. Edit one field and click `Save`.
9. Click `Approve`.
10. Export JSON or CSV and download the result.

## Tests

```powershell
cd backend
pytest
```

Expected current result:

```text
2 passed
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
- PDF page rendering is not implemented yet. Milestone 1 creates one page record
  for each upload.
- Extraction is rule-based and only handles a narrow demo text shape.
- No Excel export yet; JSON and CSV are implemented first.
- No authentication or multi-user workflow yet.
- No PII workflow. Do not upload real CCCD or sensitive customer documents.
- No RAG, vector database, chatbot, Fanpage, or Zalo integration.

## Next Recommended Milestone

- Add real image/PDF preprocessing and page rendering.
- Add PaddleOCR installation notes and a verified adapter path.
- Add bbox overlay in the review UI.
- Add more field-level tests and correction-rate evaluation.
- Add Excel export after JSON/CSV flow is stable.
