# Plan: Local Private Document Harness

## Goal

Add a local-only command-line harness for smoke testing 1-3 anonymized Vietnamese business documents without adding private samples, changing OCR defaults, or making production accuracy claims.

## Scope

- In: backend evaluation CLI, local report generation, tests, README/protocol docs.
- Out: real documents, frontend changes, auth, RAG, SaaS workflows, OCR default changes, production accuracy claims.

## Steps

1. Add tests for empty input handling, supported-file discovery, OCR preview privacy behavior, temp output writing, no expected JSON requirement, and fake OCR adapter use.
2. Implement the smallest `app.evaluation.private_samples` CLI using existing preprocessing, OCR adapter, and extraction rules.
3. Update README and the local real-document protocol with command examples and safety reminders.
4. Run backend tests, mock evaluation, empty harness checks, diff checks, and safety scans.

## Verification

- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Harness: `cd backend && python -m app.evaluation.private_samples --engine mock`
- Safety: reviewer-requested path/secret and policy-term scans.
