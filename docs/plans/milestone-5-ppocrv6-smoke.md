# Plan: Milestone 5 PP-OCRv6 Smoke Baseline

## Goal

Add a small, safe OCR-engine baseline path that keeps mock OCR as the default,
documents PaddleOCR status clearly, and avoids claiming PP-OCRv6 support until
the installed PaddleOCR Python API can be verified.

Local inspection for this milestone found that the active Python environment
does not have the `paddleocr` package installed, so PP-OCRv6 model-selection
APIs could not be verified locally. This plan makes no production OCR accuracy
claim.

## Scope

- In: backend OCR adapter metadata, evaluation report metadata, smoke tests for
  engine selection and import failures, README/data-eval documentation.
- Out: real customer documents, CCCD/CMND/PII samples, production accuracy
  claims, frontend changes, auth, RAG, SaaS features, and committed OCR model
  weights or generated artifacts.

## Requirement Check

- User workflow changed: developers can see which OCR engine/model metadata was
  used in evaluation reports and get a clear failure if they try an unsupported
  PP-OCRv6 mode.
- Layers changed: backend OCR services, evaluation reports, tests, docs.
- Explicitly out of scope: replacing mock as the default or pretending
  PP-OCRv6 is selectable without verified package/API support.
- Evidence: focused adapter/evaluation tests, full backend tests, mock
  evaluation, and `git diff --check`.

## Steps

1. Add smoke tests for default engine, PaddleOCR import failure, unsupported
   PP-OCRv6 mode, and evaluation metadata.
2. Add adapter/report metadata without changing the local database schema.
3. Document current engine modes and PP-OCRv6 status.
4. Run verification commands.

## Verification

- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Optional PaddleOCR: only run if `paddleocr` is installed locally.
- Hygiene: `git diff --check`
