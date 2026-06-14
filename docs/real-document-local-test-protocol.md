# Real Document Local Test Protocol

## Purpose

This protocol defines a safe, local-only way to test 1-3 anonymized real
Vietnamese business documents after the synthetic fixture workflow is already
passing.

The goal is to validate OCR and extraction behavior beyond synthetic fixtures
using documents that have been stripped of identifying information. This is not
a production OCR accuracy claim, and it is not a replacement for privacy,
legal, customer, or security review.

## Allowed Document Types

Only use anonymized examples of these Vietnamese business document types:

- invoice
- receipt
- delivery note
- payment slip
- purchase order

## Prohibited Content

Do not use documents that contain any of the following content:

- CCCD/CMND
- passports
- faces
- health data
- bank account numbers
- QR codes that encode real invoice or payment data
- real customer names
- real phone numbers
- real email addresses
- real addresses
- real tax codes unless masked
- signatures or stamps if they identify a real person or company

If any prohibited content cannot be confidently removed, do not test with that
document.

## Required Anonymization

Before testing, mask or replace every identifying field, including:

- company name
- customer name
- tax code
- address
- phone number
- email
- bank account
- QR code
- document number
- any unique identifier
- signatures or stamps if identifying

Use fake replacements such as:

- `CONG TY TNHH DEMO OCR`
- `CÔNG TY TNHH DEMO OCR`
- `KHÁCH HÀNG DEMO`
- `MST 0000000000`
- `DEMO-INV-REAL-001`
- `Dia chi demo`
- `Địa chỉ demo`

Anonymization must happen before the file enters this repository, the backend
upload flow, OCR, or any evaluation script.

## Storage Rule

Real or anonymized test files must stay local only.

Recommended ignored path:

```text
storage/dev/private_samples/
```

Rules:

- do not place private samples in tracked repo paths
- do not commit private samples
- do not commit OCR output containing unmasked real data
- delete private samples after testing if no longer needed

## Execution Commands

Baseline mock evaluation:

```powershell
cd backend
python -m app.evaluation.run --engine mock
python -m app.evaluation.run --engine mock --diagnostics
```

Optional PaddleOCR commands, only if the local virtual environment exists and
has PaddleOCR/PaddlePaddle installed:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.evaluation.run --engine paddle --diagnostics
.\.venv\Scripts\python.exe -m app.evaluation.run --engine ppocrv6 --diagnostics
```

Real-document testing may require a separate local-only script or a manual
upload flow if the current evaluation dataset does not include private samples.
Do not add private samples to `data/eval/` or `data/samples/`.

## Reporting Rules

Generated reports stay local under:

```text
storage/dev/eval_reports/
```

Rules:

- do not commit generated reports
- do not paste raw OCR text publicly if it contains unmasked real data
- summarize only anonymized metrics and failure patterns
- never publish private sample images or PDFs

## Acceptance Criteria Before Testing

Testing can proceed only when all of these are true:

- all files are anonymized
- files are local-only
- files are stored under ignored paths
- `git status` shows no private files staged
- the safety scan passes
- a reviewer confirms no real sensitive data remains

## Safety Checklist

Before testing:

- confirm anonymization
- confirm no QR code, bank account, phone number, address, or tax code remains
- confirm no CCCD/CMND, passport, or face remains
- confirm the file path is ignored
- run `git status`

After testing:

- run `git status --short --ignored`
- run the safety scan
- delete private samples if not needed
- do not commit generated reports

Suggested local safety scans:

```powershell
git status --short --ignored
rg "CCCD|CMND|real customer|khách hàng thật|MST|tax code|bank|QR|phone|email|address" docs README.md .gitignore
```

Also run the repository secret/path scan requested by the reviewer before
committing. Policy and prohibition mentions in documentation are acceptable.
Real data is not acceptable.
