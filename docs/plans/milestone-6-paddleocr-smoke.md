# Plan: Milestone 6 PaddleOCR Smoke Verification

## Goal

Install and verify the real PaddleOCR path using synthetic image/PDF smoke
samples only.

This milestone must not claim production OCR accuracy or confirmed PP-OCRv6
support unless explicit package/API model selection is verified.

## Implementation Result

- Local environment: Python 3.12.0 on Windows 11, CPU-only PaddlePaddle.
- Installed locally in ignored `backend/.venv`: `paddleocr==3.7.0`,
  `paddlex==3.7.1`, and `paddlepaddle==3.3.0`.
- Generic PaddleOCR smoke ran on `data/samples/smoke-demo-invoice.png` and
  `data/samples/smoke-demo-invoice.pdf`; both returned 20 OCR blocks with text
  and polygons.
- Explicit PP-OCRv6 mode was verified through
  `PaddleOCR(lang="vi", ocr_version="PP-OCRv6")`.
- Runtime metadata for explicit mode:
  `engine_name=ppocrv6`,
  `model_name=PP-OCRv6_medium_det+PP-OCRv6_medium_rec`.
- Evaluation smoke results on the existing 9-sample synthetic dataset:
  generic PaddleOCR passed 2/9 documents with 41.98% exact and normalized
  accuracy; explicit PP-OCRv6 passed 2/9 documents with the same metrics.
- The first Windows CPU run failed with a PaddlePaddle 3.3.0 oneDNN/PIR
  inference error. The adapter now sets
  `PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=0` before importing PaddleOCR unless the
  caller already set a value.

## Requirement Check

- Affected workflow: developers can run the default mock path as before, then
  optionally run a real PaddleOCR smoke check on fake Vietnamese business
  documents when local dependencies are installed.
- Affected layers: backend OCR/evaluation workflow, docs, and synthetic sample
  data only.
- Out of scope: dependency lock changes, frontend changes, real documents,
  customer data, CCCD/CMND, auth, RAG, SaaS features, production accuracy
  claims, model weights, and generated local artifacts.
- Proof of success: mock still passes, PaddleOCR runs on synthetic image/PDF
  pages, OCR blocks include text and bboxes where available, and any extraction
  imperfections or runtime limits are documented honestly.

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
- Included `data/samples/smoke-demo-invoice.png` and
  `data/samples/smoke-demo-invoice.pdf`.

## Verification Plan

The mock path must continue to pass:

```powershell
cd backend
pytest
python -m app.evaluation.run --engine mock
```

Run Paddle smoke verification only when PaddleOCR dependencies are installed.
The generic Paddle path uses `PaddleOCR(lang="vi")`.

PP-OCRv6 is enabled only through the verified explicit
`PaddleOCR(lang="vi", ocr_version="PP-OCRv6")` API. It remains experimental and
is not the default engine.

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

## Follow-up Notes

- Do not commit `backend/.venv`, model caches, uploads, page renders, databases,
  or evaluation reports.
- Treat real PaddleOCR/PP-OCRv6 results as smoke output only until a larger
  synthetic dataset and repeatable accuracy baseline exist.
