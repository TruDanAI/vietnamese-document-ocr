# Agent Instructions

This project is a Vietnamese document OCR, review, evaluation, and export MVP.
Keep changes small, local, and aligned with the current vertical slice:

- Backend: FastAPI, SQLite, local storage, OCR adapters, extraction rules, export
  writers, evaluation harness.
- Frontend: Next.js document review UI and evaluation report views.
- Default development path: `OCR_ENGINE=mock`; PaddleOCR is optional.

Do not add chatbot, RAG, fanpage, Zalo, SaaS, authentication, or PII workflows
unless the task explicitly asks for them.

## Working Rules

- Read the relevant README, module, and tests before editing.
- Do not commit secrets, real customer documents, CCCD data, invoices, tokens, or
  local database/storage artifacts.
- Prefer synthetic samples under `data/samples/` and expected fixtures under
  `data/eval/`.
- Preserve the simple MVP shape. Avoid new frameworks, services, queues, or
  abstractions unless they remove immediate complexity.
- Keep product code changes narrow. Update docs or fixtures when behavior changes.

## Requirement Check

Before implementation, write or confirm a short requirement note:

- What user workflow changes?
- Which layer changes: backend, frontend, data/eval, docs, or storage?
- What is explicitly out of scope?
- What evidence will prove the change works?

If the request is ambiguous, ask one focused question. Otherwise make a
reasonable assumption and state it before editing.

## Implementation Plans

For non-trivial work, create or update a short plan in `docs/plans/`:

```text
# Plan: <short title>

## Goal
<one paragraph>

## Scope
- In:
- Out:

## Steps
1. Add or update tests/fixtures.
2. Make the smallest implementation change.
3. Run verification commands.
4. Prepare review notes.

## Verification
- Backend:
- Frontend:
- Evaluation:
```

Small fixes can use an inline checklist instead of a plan file.

## Test-First Workflow

Use test-driven development for behavior changes:

1. Add or update a focused failing test or evaluation fixture.
2. Run the smallest relevant test command and confirm the failure is meaningful.
3. Implement the smallest change that passes.
4. Run the broader verification set before review.

Good default test targets:

```powershell
cd backend
pytest
python -m app.evaluation.run --engine mock
```

The frontend currently has no test script. For frontend changes, run:

```powershell
cd frontend
npm run build
```

## Debugging Workflow

When something fails:

- Reproduce with the smallest command or sample document.
- Capture the exact error and the command that produced it.
- Check configuration first: `OCR_ENGINE`, `DATABASE_URL`, `STORAGE_DIR`, and
  `NEXT_PUBLIC_API_BASE_URL`.
- Prefer deterministic mock OCR while debugging pipeline behavior.
- Add a regression test or fixture when the bug affects extraction, review,
  export, or evaluation results.

## Commit Workflow

Make small commits that each leave the repo in a working state:

- One behavior change per commit when possible.
- Keep docs/fixtures/test updates with the code they explain.
- Use imperative commit messages, for example:
  `Add delivery note subtotal extraction fixture`.
- Before committing, check:

```powershell
git status --short
git diff --check
```

Do not commit ignored local outputs from `storage/dev/`, `.env*`, virtualenvs,
SQLite databases, `node_modules/`, or `.next/`.

## Review Before Merge

Before asking for review, provide:

- Summary of the change and why it exists.
- Files changed by area: backend, frontend, data/eval, docs.
- Verification commands run, with pass/fail status.
- Known risks, limitations, or follow-up work.

Request review before merging to `main`, especially for API contracts,
extraction rules, evaluation metrics, export formats, or frontend review flows.

## Finish Branch Checklist

Before merge:

- `git status --short` shows only intentional changes.
- Backend changes pass `pytest`.
- Extraction/evaluation changes pass
  `python -m app.evaluation.run --engine mock`.
- Frontend changes pass `npm run build`.
- README or docs are updated if setup, workflow, or behavior changed.
- No secrets, real documents, PII, local DB files, or generated storage outputs
  are included.
