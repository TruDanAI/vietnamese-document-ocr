# Evaluation Dataset

Safe synthetic OCR/extraction evaluation samples.

Mock evaluation is an extractor regression check. It verifies that deterministic
synthetic OCR blocks still produce the expected structured fields; it does not
measure real OCR accuracy.

Each sample declares an `eval_mode`:

- `mock_only`: deterministic mock OCR / extraction regression fixture. Real OCR
  engines skip these by default because the expected JSON may describe mock
  adapter text rather than the visible image/PDF content.
- `real_ocr`: the visible image/PDF content matches the expected JSON. PaddleOCR
  and PP-OCRv6 evaluate only these fixtures by default.

The current dataset has 9 synthetic samples:

- 3 invoice variants
- 3 receipt variants
- 3 delivery-note variants

Real OCR-compatible fixtures:

- `invoice-synthetic`
- `delivery-note-synthetic`

Mock-only fixtures:

- `invoice-alt-labels`
- `invoice-split-values`
- `receipt-discount`
- `receipt-marketplace`
- `receipt-synthetic`
- `delivery-note-split-sender`
- `delivery-note-warehouse`

Each `*.sample.json` contains:

- `sample_id`
- `document_type`
- `eval_mode`
- `source_file`
- `expected_file`

Expected field JSON files live under `data/eval/expected/` and contain the
canonical values for:

- `supplier_name`
- `tax_code`
- `document_number`
- `document_date`
- `subtotal`
- `vat_amount`
- `total_amount`
- `currency`
- `notes`

No real CCCD, customer, tax, invoice, or private business data is included.
Several variants reuse safe synthetic image placeholders in mock mode; the mock
OCR adapter emits deterministic fake text based on `sample_id`. Those variants
remain useful for extraction regression but are not fair real OCR fixtures unless
their visible content is regenerated to match their expected JSON.

Evaluation reports include OCR metadata:

- `engine=mock`, `model_name=mock_synthetic` for deterministic mock runs.
- `engine=paddle`, `model_name=paddleocr_lang_vi_auto` for generic PaddleOCR
  runs unless the installed package exposes a clearer model name.

PP-OCRv6 is an optional smoke/experimental baseline only after the installed
PaddleOCR package exposes a verified explicit model-selection API. Do not add
real customer documents, CCCD/CMND samples, or generated OCR artifacts here.

Real OCR reports are smoke/evaluation aids only. Do not compare the mock 9/9
baseline directly with PaddleOCR or PP-OCRv6 unless all runs use the same
fixture set.
