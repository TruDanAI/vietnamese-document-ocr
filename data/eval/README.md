# Evaluation Dataset

Safe synthetic OCR/extraction evaluation samples.

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
