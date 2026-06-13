# Plan: Milestone 7 Real OCR Diagnostics

## Goal
Add an opt-in evaluation diagnostics report so real OCR failures can be inspected
without changing extraction behavior or claiming accuracy improvements.

## Scope
- In: backend evaluation CLI flag, diagnostics markdown report, focused tests,
  and README documentation.
- Out: extraction rule optimization, preprocessing changes, customer documents,
  auth, RAG, SaaS features, frontend redesign, and production accuracy claims.

## Steps
1. Add tests for failed-sample diagnostic report content.
2. Add a diagnostics markdown writer and wire `--diagnostics` into evaluation.
3. Include OCR text preview data in evaluation document results.
4. Run verification commands and keep generated reports untracked.

## Verification
- Backend: `cd backend && pytest`
- Evaluation: `cd backend && python -m app.evaluation.run --engine mock`
- Diagnostics: `cd backend && python -m app.evaluation.run --engine mock --diagnostics`
