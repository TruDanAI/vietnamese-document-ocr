# Plan: Milestone 11b Extraction False-Positive Hardening

## Goal
Reduce false positives introduced by broader Milestone 11 label matching while preserving the synthetic stress-fixture robustness gains.

## Scope
- In: backend extraction rules, focused negative tests, and this implementation note.
- Out: real documents, OCR engine defaults, auth, RAG, SaaS features, frontend changes, and accuracy claims.

## Steps
1. Add negative extraction tests for document-number suffixes, metadata counters, adjacent unrelated values, weak payment totals, and supplier fallback.
2. Harden the existing rules with field-specific value validation and stricter fallback guards.
3. Run backend tests, mock evaluation, diagnostics, optional real OCR diagnostics, and the safety scan.
4. Commit only relevant source, test, and docs files.

## Verification
- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Diagnostics: `cd backend && python -m app.evaluation.run --engine mock --diagnostics`
- Optional real OCR: PaddleOCR and PP-OCRv6 diagnostics when the local venv supports them.

## Result
- Added negative coverage for document-number label suffixes, monetary metadata counters/rates, unrelated adjacent numeric blocks, later payment-status totals, and unsafe supplier fallback lines.
- Hardened document-number parsing to require real inline separators or validated adjacent values, and to reject suffix words and values without digits.
- Hardened amount extraction to require money-like values and standalone adjacent amount blocks.
- Preferred strong payable-total labels before weak `Total` / `Thanh toán` labels.
- Replaced substring-based supplier fallback ignores with structured title, metadata, label, and table-header guards.
- Local verification on 14/06/2026 kept mock evaluation at 15/15 and PaddleOCR / PP-OCRv6 synthetic real-OCR diagnostics at 8/8.
- No real documents were used, and no accuracy claim was added.
