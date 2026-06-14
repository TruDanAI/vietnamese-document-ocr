# Safe Synthetic Demo Documents

These files are generated demo documents for local testing only.

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

They do not contain real customer, citizen ID, tax, invoice, or private business
data. Use them to test upload, page rendering, OCR mock mode, review, export,
and optional PaddleOCR smoke runs. The `*-demo-diacritics.png` files are
synthetic-only real OCR fixtures with fake Vietnamese demo content; they are not
production accuracy evidence.

The `*-stress-demo.png` files are also fully synthetic. They add mild OCR stress
conditions such as smaller text, lower contrast, slight rotation, compact receipt
spacing, and table-like rows. Failures on these files are diagnostic signals for
future preprocessing and extraction work, not production accuracy claims.
