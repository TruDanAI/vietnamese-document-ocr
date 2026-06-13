# Plan: Real OCR Fixture Alignment

## Goal
Separate mock-only extraction regression fixtures from fixtures whose visible
image or PDF content matches expected JSON, so real OCR evaluations do not
compare PaddleOCR output against unrelated mock text.

## Scope
- In: eval fixture metadata, evaluation selection/reporting, diagnostics, tests,
  and documentation.
- Out: extraction rule optimization, OCR preprocessing changes, customer
  documents, auth, RAG, SaaS features, frontend redesign, and production
  accuracy claims.

## Steps
1. Add fixture metadata and tests that define mock-only skip behavior.
2. Update the evaluation runner, report summary, and diagnostics.
3. Update README and eval dataset docs.
4. Run backend tests, mock evaluation, diagnostics, optional real OCR smoke
   checks, and safety scan.

## Verification
- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Diagnostics: `cd backend && python -m app.evaluation.run --engine mock --diagnostics`
- Optional real OCR: Paddle/PP-OCRv6 commands if the local venv has PaddleOCR.
