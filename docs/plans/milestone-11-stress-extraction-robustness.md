# Plan: Milestone 11 Stress Extraction Robustness

## Goal
Improve rule-based extraction robustness for synthetic stress fixtures where real OCR introduces mild label noise, accent loss, and adjacent label/value blocks.

## Scope
- In: backend extraction rules, focused rule tests, documentation of synthetic-only limitations.
- Out: auth, RAG, SaaS features, frontend redesign, real customer documents, production accuracy claims, and new sensitive data fixtures.

## Steps
1. Inspect PaddleOCR and PP-OCRv6 diagnostics for the three failing stress fixtures.
2. Add focused tests for noisy labels, split adjacent values, document-number guards, payable totals, and supplier fallback behavior.
3. Make the smallest extraction-rule changes needed to pass those tests.
4. Run backend tests, mock evaluation, diagnostics, optional real OCR diagnostics, and the safety scan.

## Verification
- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Diagnostics: `cd backend && python -m app.evaluation.run --engine mock --diagnostics`
- Optional real OCR: PaddleOCR and PP-OCRv6 diagnostics only if the local venv supports them.

## Result
- Added accent-insensitive and conservative fuzzy label matching while preserving extracted values.
- Added adjacent OCR-block value lookup for noisy label-only blocks.
- Added guarded document-number extraction for explicit labels and exact generic `Số` / `So` labels without treating tax codes, dates, or quantity headers as document numbers.
- Added payable-total matching for lost-accent labels such as `tong cong`, `thanh toan`, and mildly corrupted variants.
- Improved supplier fallback so document titles are skipped when a better supplier candidate is available.
- Local synthetic-only smoke diagnostics on 14/06/2026 improved PaddleOCR and PP-OCRv6 `real_ocr` fixture results from 5/8 to 8/8, with all 3 stress fixtures passing.
- No real customer documents were used, and this is not a production OCR accuracy claim.
