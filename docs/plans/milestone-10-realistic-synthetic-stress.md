# Plan: Realistic Synthetic OCR Stress Fixtures

## Goal
Add a small synthetic-only stress set for real OCR evaluation so PaddleOCR and
PP-OCRv6 smoke runs include invoice, receipt, and delivery-note layouts that are
closer to real capture conditions without using real documents or personal data.

## Scope
- In: three new `real_ocr` fixtures, generated synthetic sample files, mock OCR
  fixture coverage, tests, and documentation.
- Out: CCCD/CMND, real customer data, secrets, production accuracy claims, OCR
  default changes, and PP-OCRv6 status changes.

## Steps
1. Add focused evaluation tests for the new real OCR fixture metadata, filter
   counts, expected JSON, and sample-file references.
2. Add the fixture metadata, expected fields, and mock adapter text.
3. Generate mild-stress synthetic sample files with fake demo content only.
4. Update README files with counts, constraints, and interpretation guidance.
5. Run backend tests, mock evaluation, optional real OCR diagnostics, safety
   scan, and commit only relevant source/docs/test/sample files.

## Verification
- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Diagnostics: `cd backend && python -m app.evaluation.run --engine mock --diagnostics`
- Optional real OCR: PaddleOCR and PP-OCRv6 diagnostics only if local venv
  supports those engines.
