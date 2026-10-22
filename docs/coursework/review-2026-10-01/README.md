# FixProof student test-evidence report

This report lets students trace the candidate-level matrices to the recorded
payloads, requests, responses, outputs, and case outcomes.

## Recommended files

- **FixProof-15-candidate-test-evidence.xlsx** is the primary offline report.
- **student-evidence-csv/** contains one CSV for each major worksheet.
- **FixProof-student-evidence-validation.json** records source hashes, output
  hashes, reconciled counts, and validation checks.
- The public static site exposes the same information through
  **test-evidence.html** and **data/student-test-evidence.json**.

## Workbook structure

1. **Guide** — explains the evidence layers and denominators.
2. **Candidate Summary** — shows the 15 candidate-level SAST, primary,
   supplemental, human-review, and PATH-S06 extension columns.
3. **Primary Cases** — 100 rows: 40 security and 60 functional observations.
4. **Supplemental Cases** — 140 frozen rows: 60 security, 45 behavioral
   parity, and 35 robustness observations.
5. **PATH-S06 Extension** — five separate WSL2 security observations.
6. **Count Reconciliation** — explains candidate-level versus case-level
   denominators.
7. **Human Decisions** — 10 original reviews, 14 supplemental-v1 follow-ups,
   and five PATH-S06 extension qualifications.

## Interpretation boundary

- Primary-v1, supplemental-v1, and the PATH-S06 extension are separate layers.
- The five extension failures do not replace the five inconclusive PATH-S06
  entries in supplemental-v1.
- SAST, runtime security, behavioral parity, robustness, and human decisions
  answer different questions and must not be combined into one production
  success rate.
- Primary request targets are derived only from the recorded route, parameter,
  and payload. Supplemental and extension request targets come from recorded
  evidence with transient loopback ports omitted.
- Generated absolute-path payloads are privacy-sanitized in the student export;
  the recorded results are unchanged.

## Netlify package

Use **fixproof-public-netlify-path-s06-2026-10-21-v2.zip** for the next
deployment. Its SHA-256 is
**F60F2EE42640849C2BD9E89CCE014BD1113B31BF2A4928DD6D47163646B777D0**.
It contains the case-level table, workbook, five separate PATH-S06 extension
failures, and five extension human qualifications. The October 1 and September
30 packages are retained as superseded local artifacts. The first October 21
ZIP is also superseded because Windows `Compress-Archive` stored nested entries
with backslashes, causing Netlify JSON requests to return HTTP 404. Version 2
uses forward-slash archive paths and passed an extracted-package browser test.
Do not describe the live site as updated until version 2 has been uploaded and
checked.
