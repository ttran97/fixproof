# FixProof final deliverable staging folder

**Status:** Staging structure created October 1, 2026 and updated October 22
after the live public-reference and clean-package checks. This is not yet the
final submission package.

This folder stages the materials that may accompany the FixProof final report
and final presentation. The organization follows the course clarification:

- The professors should be able to understand the methodology, analysis,
  results, limitations, and conclusions from the final report alone.
- Supporting materials should still be organized and accessible in case the
  instructional staff wants to inspect them.
- The final presentation should demonstrate selected supporting artifacts, not
  walk through every file.
- Any shared link must work without an access request.

## Planned package

1. **01-final-report/** — self-contained final report and submission copy.
2. **02-final-presentation/** — final deck, script, and presentation-access
   information.
3. **03-supporting-materials/** — selected evidence, source-code access,
   reproducibility instructions, and sanitized public reference.
4. **04-manifest-and-checksums/** — release manifest, file sizes, hashes,
   versions, and verification results.
5. **FINAL-SUBMISSION-CHECKLIST.md** — final access, privacy, rendering, and
   submission checks.

## Current source artifacts

These remain in their working locations until they are final:

- Latest progress-report draft:
  **docs/coursework/review-2026-10-27/Progress Report 5 (Tony Tran) - TA
  Feedback Aligned October 27.docx**
- Partial final-report draft:
  **final-deliverable/01-final-report/FixProof Final Project Report - Partial
  Draft October 27.pdf**
- Student evidence workbook:
  **docs/coursework/review-2026-10-01/FixProof-15-candidate-test-evidence.xlsx**
- Current printable evidence appendix:
  **docs/coursework/review-2026-09-22/Video-III-15-candidate-evidence-appendix.pdf**
- Current public-reference source: **fixproof-public/**
- Reproducibility guidance: **docs/reproducibility.md**
- Live public validation and clean-package rehearsal:
  **docs/coursework/review-2026-10-22/**

References here are pointers, not final-package copies. Copying begins only
after an artifact is approved for release.

## Packaging boundary

Do not include local environments, credentials, caches, Office lock files,
browser profiles, temporary workspaces, debug logs, or unreviewed raw exports.
In particular, exclude **.env**, **.venv/**, **.pytest_cache/**,
**.codex-tmp/**, **debug.log**, and disposable verification copies.

The final report body should contain the evidence needed to understand the
project. The workbook, source code, appendix, dashboard, and raw evidence are
supporting materials rather than required reading.
