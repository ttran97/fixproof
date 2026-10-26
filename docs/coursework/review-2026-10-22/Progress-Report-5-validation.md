# Progress Report 5 validation

Validated October 23, 2026.

## Current files

- Source: `Progress-Report-5-working-draft.md`
- Submission draft: `Progress Report 5 (Tony Tran) - Feedback Aligned October 23.docx`
- Review rendering: `Progress Report 5 (Tony Tran) - Feedback Aligned October 23.pdf`

The October 22 draft is retained as an earlier working version. The
feedback-aligned October 23 DOCX is the current file.

## Response to prior feedback

The draft explicitly addresses the October 12 Progress Report 3 instructor
comment requesting code snippets and output as draft work. It now includes:

- a source-linked excerpt from `src/fixproof/primary_trials.py` showing Python
  invoking security validation, functional validation, and the deterministic
  decision engine;
- an excerpt from the frozen PATH-S06 summary showing zero candidate passes,
  five failures, and the HTTP 200/marker-disclosure fields for Traversal 02;
- an explanation that Python coordinates artifacts, validators measure, policy
  routes, and the human reviewer records a separate verdict and rationale; and
- a qualitative, claim-specific evidence-strength table. The report does not
  present repeated repairs of one fixture as statistical confidence or a
  production success rate.

## Evidence checks

The draft was reconciled against the current repository records:

- primary attempts: 15;
- primary target-SAST resolution: 5/15;
- primary security and functional suites: 15/15 candidates passed each;
- primary policy routing: five ready for human review and ten needing human
  adjudication;
- supplemental-v1: 140 observations, 120 pass, 15 fail, and five
  inconclusive;
- supplemental XSS security: 15/15 pass; one of five XSS candidates passed all
  nine supplemental cases;
- supplemental SQLi security: 15/15 pass and parity: 10/10 pass; all five SQLi
  candidates failed SQL-R01, and their candidate source hash has one unique
  value across five records;
- PATH-S06 extension: zero pass, five fail, and zero inconclusive; and
- public evidence: 100 primary rows, 140 supplemental-v1 rows, five extension
  rows, and 29 separately labeled human-decision records.

Primary-v1, supplemental-v1, and PATH-S06 extension denominators remain
separate. The website, manual presentation checks, and reproduction rehearsal
do not add experimental observations.

## Word and PDF rendering checks

Microsoft Word opened the current DOCX read-only and repaginated it:

- 7 pages;
- 3,627 Word-counted words;
- 396 paragraphs;
- 8 tables;
- 1 section;
- no comments;
- no revisions; and
- revision tracking disabled.

The Python and saved-output excerpts render in 8-point Consolas. The PDF was
exported from the same Word document and contains seven nonblank pages. No
`TODO`, `TBD`, `[Tony`, obsolete deployment-pending statement, or unreceived
peer-feedback claim was found.

## Required personal review before submission

1. Add Tony's actual hours if the live template requires them.
2. Replace the Peer Feedback IV in-progress statement with an
   adopt/defer/decline summary after that assignment is complete.
3. Confirm Report 5, Video V, peer-feedback, final-presentation, and final-report
   dates in Canvas.
4. Open the feedback-aligned DOCX in Word and approve the personal wording and
   page breaks.
5. Retain the Report 4, Video IV, and public-deployment submission evidence.
