# Plan: Milestone 6 PaddleOCR Smoke Verification

## Goal

Install and verify the real PaddleOCR path using synthetic image/PDF smoke
samples only.

This milestone must not claim production OCR accuracy or confirmed PP-OCRv6
support unless explicit package/API model selection is verified.

## Requirement Check

- Affected workflow: developers can run the default mock path as before, then
  optionally run a real PaddleOCR smoke check on fake Vietnamese business
  documents when local dependencies are installed.
- Affected layers: backend OCR/evaluation workflow, docs, and future synthetic
  sample data only.
- Out of scope: PaddleOCR installation in this planning PR, dependency changes,
  generated samples, README edits, backend/frontend code changes, real
  documents, customer data, CCCD/CMND, auth, RAG, SaaS features, production
  accuracy claims, model weights, and generated local artifacts.
- Proof of success: a later implementation PR shows mock still passes, PaddleOCR
  runs on at least one synthetic image/PDF page, OCR blocks include text and
  bboxes where available, and any extraction imperfections or PP-OCRv6 limits
  are documented honestly.

## Environment Check Commands

Run these before choosing any dependency or model-selection approach:

```powershell
python --version
python -c "import platform; print(platform.platform())"
python -c "import importlib.util; print(importlib.util.find_spec('paddleocr') is not None)"
python -c "import importlib.util; print(importlib.util.find_spec('paddle') is not None)"
```

If `paddle` is installed, check CPU/GPU availability:

```powershell
python -c "import paddle; print('compiled_with_cuda:', paddle.is_compiled_with_cuda()); print('device:', paddle.device.get_device())"
```

Record the Python version, OS/platform, PaddleOCR install status,
PaddlePaddle/Paddle install status, and whether the environment is CPU-only or
GPU-capable.

## Dependency Approach

- Inspect the official PaddleOCR installation docs first.
- Prefer a docs-based local install instruction or a local/dev optional extra.
- Do not pin PaddleOCR or PaddlePaddle versions blindly.
- Do not commit downloaded model weights.
- Do not make PaddleOCR required for the default mock workflow.
- Keep `OCR_ENGINE=mock` as the default development and evaluation path.

## Synthetic Smoke Samples

- Use only fake Vietnamese business document images/PDFs.
- Do not use CCCD/CMND.
- Do not use real invoices.
- Do not use customer data.
- Do not use personal data.
- Use fake names like `CÔNG TY TNHH DEMO OCR`.
- Use fake tax code `MST 0000000000`.
- Include at least one image and one PDF page in the future implementation.
- Future synthetic smoke samples should live under `data/samples/` with clear
  smoke/demo names.

## Verification Plan

The mock path must continue to pass:

```powershell
cd backend
pytest
python -m app.evaluation.run --engine mock
```

Run Paddle smoke verification only when PaddleOCR dependencies are installed.
The Paddle path should use the existing generic PaddleOCR adapter unless a
documented package/API path requires a narrow follow-up change.

Enable PP-OCRv6 only if explicit PP-OCRv6 selection is verified through the
installed package/API. If explicit selection cannot be verified, document
PP-OCRv6 honestly as not verified and keep `OCR_ENGINE=ppocrv6` unsupported.

## Success Criteria

Milestone 6 implementation will be considered successful when:

- Mock remains the default OCR engine.
- The PaddleOCR adapter runs on at least one synthetic image/PDF page.
- OCR blocks are produced with text and bboxes where available.
- Extraction imperfections are documented.
- README clearly separates mock eval, generic PaddleOCR smoke, and PP-OCRv6
  status.

## Out of Scope

- Auth.
- RAG.
- SaaS features.
- Production accuracy claims.
- Real documents.
- CCCD/CMND.
- Customer data.
- Frontend redesign.
- DB schema changes unless absolutely necessary.
- Committed model weights.
- Generated DBs/uploads/page images/cache files.

## Follow-up Implementation Notes

Implementation should happen in a later PR after this planning PR is merged.
That later PR should keep changes narrow, avoid real documents or generated
artifacts, and update README only after the actual PaddleOCR smoke result is
verified.
