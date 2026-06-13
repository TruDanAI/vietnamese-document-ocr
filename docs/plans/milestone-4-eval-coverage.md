# Plan: Milestone 4 Synthetic Evaluation Coverage

## Goal

Expand the mock evaluation dataset before attempting real document support. The
new coverage should expose common rule-extraction gaps using clearly fake
Vietnamese business document variants.

## Scope

- In: six synthetic mock evaluation cases, expected field JSON, focused backend
  tests for any failing extraction patterns, small extraction-rule fixes, README
  baseline update.
- Out: real customer documents, CCCD/PII, authentication, RAG, SaaS features,
  frontend changes, and production OCR accuracy claims.

## Requirement Check

- User workflow changed: developers can run mock evaluation against a broader
  synthetic dataset before trying PaddleOCR or real scans.
- Layers changed: `data/eval`, mock OCR fixtures, backend extraction tests,
  extraction rules, and docs.
- Explicitly out of scope: product expansion beyond the current OCR/review/export
  MVP.
- Evidence: `pytest`, `python -m app.evaluation.run --engine mock`, and
  `git diff --check`.

## Steps

1. Add two invoice, two receipt, and two delivery-note synthetic fixtures.
2. Run mock evaluation and record field failures.
3. Add focused extraction tests for the failing label/value patterns.
4. Make the smallest rule updates needed to pass the synthetic baseline.
5. Update README with sample count, mock baseline, and limitations.
6. Prepare review notes.

## Verification

- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Hygiene: `git diff --check`
