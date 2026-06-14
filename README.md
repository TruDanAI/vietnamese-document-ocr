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

The default OCR engine is `mock`, so the app works without PaddleOCR. A generic
PaddleOCR adapter exists behind `OCR_ENGINE=paddle` or `OCR_ENGINE=paddleocr`,
but PaddleOCR setup is optional and not required for the main demo. PP-OCRv6 is
available only as an experimental smoke engine behind `OCR_ENGINE=ppocrv6`
after the local PaddleOCR/PaddlePaddle install exposes explicit
`ocr_version="PP-OCRv6"` selection.

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

### OCR Engine Modes

Supported engine values:

| Mode | Status | Metadata | Intended use |
| --- | --- | --- | --- |
| `mock` | Default | `engine_name=mock`, `model_name=mock_synthetic` | Deterministic local development and extractor regression checks. |
| `paddle` / `paddleocr` | Optional | `engine_name=paddle`, `model_name=paddleocr_lang_vi_auto` unless the package exposes a clearer name | Generic PaddleOCR smoke testing after local installation. |
| `ppocrv6` | Optional experimental | `engine_name=ppocrv6`, `model_name=PP-OCRv6_medium_det+PP-OCRv6_medium_rec` | Explicit PP-OCRv6 smoke testing after local installation. |

Do not treat mock evaluation as OCR accuracy. Mock mode emits deterministic
synthetic text and measures the extraction/reporting pipeline.

### Mock OCR Mode

Mock mode is the default and is the expected path for local development:

```powershell
$env:OCR_ENGINE="mock"
uvicorn app.main:app --reload
```

Mock OCR returns deterministic synthetic blocks. It is useful for testing the
pipeline, review UI, correction logs, and exports without installing any OCR
runtime. Evaluation reports record `model_name=mock_synthetic`.

### PaddleOCR Mode

PaddleOCR is optional. Install it only when you want to smoke test real OCR
locally:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install paddleocr
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
$env:OCR_ENGINE="paddle"
uvicorn app.main:app --reload
```

Notes:

- Official PaddleOCR docs recommend installing the `paddleocr` package from
  PyPI for local inference.
- The Windows CPU smoke run for this branch used `paddleocr==3.7.0` and the
  official PaddlePaddle CPU wheel command above, which installed
  `paddlepaddle==3.3.0`.
- PaddleOCR may install large dependencies and model files on first use.
- Windows setups can fail because of PaddlePaddle/PaddleOCR wheel, Python,
  CPU/GPU, or native dependency differences. Keep `OCR_ENGINE=mock` as the
  fallback.
- The adapter sets `PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=0` before importing
  PaddleOCR unless the caller already set it. The first Windows CPU run hit a
  PaddlePaddle 3.3.0 oneDNN/PIR inference error without that setting.
- The adapter calls `PaddleOCR(lang="vi")` and lets the installed package choose
  its default Vietnamese OCR models. Evaluation metadata records this as
  `model_name=paddleocr_lang_vi_auto` unless the package exposes a clearer model
  name at runtime.
- This path is a smoke baseline only, not a production OCR accuracy guarantee.

### PP-OCRv6 Status

PP-OCRv6 is an optional experimental smoke path, not the default engine and not
an accuracy baseline. The locally verified API is:

```python
PaddleOCR(lang="vi", ocr_version="PP-OCRv6")
```

In `paddleocr==3.7.0`, that resolves to the medium PP-OCRv6 detection and
recognition models for Vietnamese/Latin text. Evaluation metadata records:

```text
engine_name=ppocrv6
model_name=PP-OCRv6_medium_det+PP-OCRv6_medium_rec
```

Run it only after installing PaddleOCR and PaddlePaddle locally:

```powershell
cd backend
python -m app.evaluation.run --engine ppocrv6
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
- `invoice-demo-diacritics.png`
- `invoice-stress-demo.png`
- `smoke-demo-invoice.png`
- `smoke-demo-invoice.pdf`
- `smoke-demo-invoice-accented.png`
- `smoke-demo-invoice-accented.pdf`
- `receipt-demo-diacritics.png`
- `receipt-stress-demo.png`
- `receipt-synthetic.png`
- `delivery-note-demo-diacritics.png`
- `delivery-note-stress-demo.png`
- `delivery-note-synthetic.png`

These files do not contain real customer, citizen ID, tax, invoice, or private
business data. The `smoke-demo-*` files are fake PaddleOCR smoke inputs only;
they are not evaluation accuracy fixtures.

## Evaluation Dataset

Evaluation fixtures live under `data/eval/`:

```text
data/eval/
  invoice/
    invoice-demo-diacritics.sample.json
    invoice-alt-labels.sample.json
    invoice-split-values.sample.json
    invoice-stress-demo.sample.json
    invoice-synthetic.sample.json
  receipt/
    receipt-demo-diacritics.sample.json
    receipt-discount.sample.json
    receipt-marketplace.sample.json
    receipt-stress-demo.sample.json
    receipt-synthetic.sample.json
  delivery_note/
    delivery-note-demo-diacritics.sample.json
    delivery-note-split-sender.sample.json
    delivery-note-stress-demo.sample.json
    delivery-note-synthetic.sample.json
    delivery-note-warehouse.sample.json
  expected/
    invoice-demo-diacritics.expected.json
    invoice-alt-labels.expected.json
    invoice-split-values.expected.json
    invoice-stress-demo.expected.json
    invoice-synthetic.expected.json
    receipt-demo-diacritics.expected.json
    receipt-discount.expected.json
    receipt-marketplace.expected.json
    receipt-stress-demo.expected.json
    receipt-synthetic.expected.json
    delivery-note-demo-diacritics.expected.json
    delivery-note-split-sender.expected.json
    delivery-note-stress-demo.expected.json
    delivery-note-synthetic.expected.json
    delivery-note-warehouse.expected.json
```

The current dataset has 15 synthetic samples: 5 invoices, 5 receipts, and 5
delivery notes. Some variants reuse safe synthetic image placeholders while mock
OCR emits deterministic variant text by `sample_id`.

Each sample declares an `eval_mode`:

- `mock_only`: extractor regression fixture for deterministic mock OCR. Real
  OCR engines skip these by default because the expected JSON may not match the
  visible image/PDF text.
- `real_ocr`: visible image/PDF content matches expected JSON. PaddleOCR and
  PP-OCRv6 use only these fixtures by default.

Current real OCR-compatible fixtures:

- `delivery-note-demo-diacritics`
- `delivery-note-stress-demo`
- `delivery-note-synthetic`
- `invoice-demo-diacritics`
- `invoice-stress-demo`
- `invoice-synthetic`
- `receipt-demo-diacritics`
- `receipt-stress-demo`

Current mock-only fixtures:

- `invoice-alt-labels`
- `invoice-split-values`
- `receipt-discount`
- `receipt-marketplace`
- `receipt-synthetic`
- `delivery-note-split-sender`
- `delivery-note-warehouse`

The `*-stress-demo` fixtures are synthetic-only OCR stress samples. They use
fake demo entities, mild lower contrast, smaller text, slight rotation, a narrow
receipt layout, and table-like rows. They are intended to reveal preprocessing
and extraction weaknesses, not to claim production OCR accuracy.

For future local-only testing with 1-3 anonymized real Vietnamese business
documents, follow `docs/real-document-local-test-protocol.md`. Do not commit
private samples or generated OCR output from those tests.

Milestone 11 added small rule-based robustness fixes for those stress samples:
accent-insensitive label comparison, conservative fuzzy matching for mildly
corrupted Vietnamese labels, adjacent block label/value extraction, guarded
document-number handling for `Số` / `So` variants, payable-total preference
when subtotal labels are also present, and supplier fallback that skips invoice,
receipt, and delivery-note title lines when a better candidate exists.

In a local synthetic-only smoke run on 14/06/2026, PaddleOCR and experimental
PP-OCRv6 diagnostics passed all 8 `real_ocr` fixtures, including the 3 stress
fixtures. This remains a synthetic evaluation result only. It does not use real
customer documents and is not a production OCR accuracy claim.

Each `*.sample.json` declares:

```json
{
  "sample_id": "invoice-synthetic",
  "document_type": "invoice",
  "eval_mode": "real_ocr",
  "source_file": "../../samples/invoice-synthetic.png",
  "expected_file": "../expected/invoice-synthetic.expected.json"
}
```

Each expected JSON contains:

```json
{
  "fields": {
    "supplier_name": "CONG TY TNHH MINH AN",
    "tax_code": "0000000000",
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
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m app.evaluation.run --engine paddle
```

PP-OCRv6 mode:

```powershell
cd backend
python -m pip install paddleocr
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m app.evaluation.run --engine ppocrv6
```

Real OCR engines evaluate only the 8 synthetic `real_ocr` fixtures by default,
skip the remaining 7 `mock_only` fixtures, and report the skipped sample count.
To force a diagnostic run across every fixture, use:

```powershell
python -m app.evaluation.run --engine paddle --include-mock-only
```

Use that flag only when you intentionally want to compare real OCR output
against mock-only expectations.

PP-OCRv6 mode is verified only for the local package/API combination documented
above. Do not record it as an OCR baseline unless the command actually runs in
your environment.

Reports are written to:

```text
storage/dev/eval_reports/
```

The runner writes:

- JSON report: machine-readable full field comparisons.
- Markdown report: quick human-readable summary.
- OCR metadata: `engine` and `model_name` at the report and document level.

### Real OCR Diagnostics

Add `--diagnostics` to write a failed-sample diagnostic report:

```powershell
cd backend
python -m app.evaluation.run --engine mock --diagnostics
.\.venv\Scripts\python.exe -m app.evaluation.run --engine paddle --diagnostics
.\.venv\Scripts\python.exe -m app.evaluation.run --engine ppocrv6 --diagnostics
```

Diagnostic reports are written to:

```text
storage/dev/eval_reports/<timestamp>-<engine>-diagnostics.md
```

Generated evaluation and diagnostic reports are local artifacts ignored by git
and should not be committed. Diagnostics show failed samples, OCR text previews,
expected vs extracted fields, and simple failure categories. They explain why a
run failed but do not improve accuracy by themselves. Stress-fixture failures
should guide future preprocessing and extraction improvements. Diagnostics also
list skipped mock-only fixtures for real OCR engines. Real PaddleOCR and
PP-OCRv6 results remain smoke/evaluation aids until later extraction and
preprocessing milestones.

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

Current synthetic dataset baseline after Milestone 4 rules:

```text
Documents passed: 15/15
Exact match accuracy: 100.00%
Normalized match accuracy: 100.00%
Missing fields: 0
Wrong fields: 0
```

Milestone 4 added synthetic coverage for split labels and values, spaced tax
codes, alternate receipt and delivery-note number/date labels, extra total
labels such as `Cần thanh toán` / `Tong phai tra`, and a guard so `Total` does
not match inside `Subtotal`.

This is an extractor regression baseline, not a real OCR benchmark. PaddleOCR
and PP-OCRv6 smoke results should be reported separately from the mock baseline.
Mock 15/15 and real OCR document counts should not be compared directly unless
the same fixture set is evaluated in both runs.

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
35 passed
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
- Extraction is rule-based and only handles the synthetic invoice, receipt, and
  delivery-note labels covered by the current fixtures.
- XLSX export is intentionally simple and only includes metadata plus extracted
  fields.
- PaddleOCR and PP-OCRv6 modes are optional and may need local dependency
  troubleshooting.
- PaddlePaddle 3.3.0 CPU inference hit a oneDNN/PIR error locally until
  `PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=0` was set before importing PaddleOCR.
  The adapter now sets that default unless the caller already chose a value.
- Evaluation results in mock mode measure pipeline correctness, not real OCR
  accuracy, because mock OCR emits deterministic synthetic text.
- The current 15-sample dataset is too small to claim production accuracy.
- Rule-based extraction can still miss `supplier_name`, `notes`, document
  numbers, and monetary fields when OCR omits the value text entirely, severely
  corrupts a label beyond the conservative variants covered here, or separates
  labels and values in layouts not represented by the synthetic fixtures.
- No authentication or multi-user workflow yet.
- No PII workflow. Do not upload real CCCD or sensitive customer documents.
- No RAG, vector database, chatbot, Fanpage, or Zalo integration.

## Next Recommended Milestone

- Expand the synthetic evaluation dataset from 15 to 20-30 files across receipts,
  invoices, delivery notes, and price-list-like documents.
- Run PaddleOCR mode on those samples and document installation/runtime issues.
- Add document-type-specific extraction templates.
- Add correction-rate reporting from real review edits.
- Improve multi-page review UX only after evaluation shows it matters.
