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

Use **fixproof-public-netlify-test-evidence-2026-10-01.zip** for the next
deployment. Its SHA-256 is
**F39B196D78C2520DEA48121A65BC570AC7ADB0F1505C85FD282367284874EA19**.
The previously generated September 30 ZIP does not contain this case-level
table or workbook.
