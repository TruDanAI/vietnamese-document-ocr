# Plan: Expand Real OCR Fixtures

## Goal
Increase the synthetic real-OCR-compatible evaluation subset from 2 fixtures to
at least 5 fixtures while keeping mock evaluation as the full deterministic
regression suite.

## Scope
- In: add one invoice, one receipt, and one delivery-note synthetic fixture with
  visible fake Vietnamese text, expected JSON, mock adapter text, tests, and docs.
- Out: real customer documents, CCCD/CMND data, extraction-rule optimization,
  production accuracy claims, and broad fixture generator work.

## Steps
1. Add focused tests for the new fixture counts, filtering behavior, skipped
   counts, and metadata alignment.
2. Add the smallest fixture files and deterministic mock OCR text needed for
   mock evaluation to keep passing.
3. Update documentation for the expanded synthetic-only real OCR subset.
4. Run the requested verification commands and safety scan.

## Verification
- Backend: `pytest`
- Evaluation: `python -m app.evaluation.run --engine mock`
- Diagnostics: `python -m app.evaluation.run --engine mock --diagnostics`
- Optional real OCR: PaddleOCR and PP-OCRv6 diagnostics only if the local venv
  has PaddleOCR installed.
