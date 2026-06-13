# Evaluation Dataset

Safe synthetic OCR/extraction evaluation samples.

The current dataset has 9 synthetic samples:

- 3 invoice variants
- 3 receipt variants
- 3 delivery-note variants

Each `*.sample.json` contains:

- `sample_id`
- `document_type`
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
The Milestone 4 variants reuse safe synthetic image placeholders in mock mode;
the mock OCR adapter emits deterministic fake text based on `sample_id`.
