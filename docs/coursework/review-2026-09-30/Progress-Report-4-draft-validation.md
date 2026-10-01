# Progress Report 4 working-draft validation

Validated October 1, 2026 against the current FixProof repository, the
student-facing evidence report, and the updated local public-reference package.
The live Netlify deployment has not yet been replaced with this October 1
version.

## Generated files

- `Progress Report 4 (Tony Tran) - Student Evidence Aligned October 1.docx`
- `Progress Report 4 (Tony Tran) - Student Evidence Aligned October 1.pdf`
- `Progress-Report-4-working-draft.md`
- `Progress-Report-4-next-steps.md`

## Evidence checks

- Primary evidence: 15/15 initial attempts verified; 10/10 original conflict
  reviews complete.
- Supplemental evidence: three baselines and 15 saved candidates verified.
- Supplemental human records: 14/14 complete; zero pending.
- The full suite, including seven extension-run tests and five extension-human-
  review tests, passed 131/131 tests in a clean local clone using the configured
  Python 3.11.9 interpreter. The seven focused extension-run tests also pass
  under Python 3.12.3 in WSL2. Open Office
  lock files were excluded by the clean clone without modifying the user's
  working documents.
- Primary values in the draft match the verified report: 5/15 target-SAST
  resolution, 15/15 primary security-suite passes, 15/15 primary
  functional-suite passes, and 10/15 SAST/runtime disagreements.
- Supplemental values match the registered results: security 55 pass, zero
  fail, five inconclusive; parity 40 pass and five fail; robustness 25 pass and
  10 fail; 140 observations total.
- The updated local public JSON contains 15 candidate records, the same primary
  and supplemental-v1 summaries and 14 prior later records, and five separate
  PATH-S06 qualifications.
- The student export reconciles 15 candidate rows, 100 primary runtime cases,
  140 supplemental-v1 cases, five separate PATH-S06 extension cases, and 29
  human records. The Excel workbook, six CSV tables, and public JSON use the
  same counts.

## Document checks

- The DOCX contains the problem, solution, completed work, remaining Report 4
  work, next-report tasks, issues, methodology, timeline, evaluation, report
  outline, references, evidence index, verification note, and AI disclosure.
- The October 1 PDF contains seven pages and five tables. Table rows are
  configured not to split across pages, and header rows repeat when a table
  continues.
- The generated package contains no mojibake.
- The Markdown report source distinguishes completed work from planned work. It
  now reports the completed PATH-S06 extension but does not claim that peer
  feedback, a second fixture, or the broader clean-package audit has already
  occurred.
- The report preserves primary-v1 and supplemental-v1 and does not relabel any
  failure or inconclusive observation.
- The older September 30 DOCX/PDF files predate the student evidence report and
  should not be submitted. The separately named October 1 DOCX/PDF contain the
  current results, 131-test count, five extension qualifications, and
  case-level evidence reconciliation; they still require Tony's actual hours
  and received peer feedback.

## PATH-S06 execution validation

- `path-s06-extension-v1` was frozen before candidate execution and binds its
  protocol, one-case definition, focused runner, package files, baseline, and
  five candidate sources by SHA-256.
- WSL2 executed the case in disposable Linux-native workspaces using native
  Node.js 24.19.0 and npm 11.17.0. Python 3.12.3 orchestrated the standard-
  library-only runner; this differs from the project's declared Python 3.11
  range and is explicitly disclosed.
- The vulnerable baseline returned HTTP 200 and disclosed the controlled
  outside marker, so the baseline gate passed.
- All five candidates returned HTTP 200 and disclosed the marker: zero pass,
  five fail, zero inconclusive.
- Run verification recomputed every result binding and candidate count.
  Before/after tree fingerprints confirm that primary-v1 and supplemental-v1
  did not change.
- Tony approved five separate `FOLLOW_UP_REJECT_CANDIDATE` qualifications after
  reviewing all five records and manually reproducing Traversal 02. The
  extension follow-up verifier reports 5/5 complete; only Traversal 02 claims a
  manual reproduction.
- The sanitized public export now contains 15 candidates, the unchanged 140
  supplemental-v1 observations and 14 supplemental-v1 human records, plus a
  separate five-failure/five-qualification PATH-S06 extension summary.
- Local browser validation passed with 15 rows in each matrix, five extension
  metrics/qualifications, candidate detail checks, privacy checks, and no page
  or unexpected console errors.
- The rebuilt 15-candidate appendix includes 10 original, 14 supplemental-v1,
  and five PATH-S06 extension rationales across 19 PDF pages.
- A versioned Netlify upload package is ready at
  `fixproof-public-netlify-test-evidence-2026-10-01.zip`. Its SHA-256 is
  `F39B196D78C2520DEA48121A65BC570AC7ADB0F1505C85FD282367284874EA19`.
  The live site is intentionally not claimed as updated until Tony uploads and
  validates this package.

## Student evidence report validation

- The seven-sheet Excel workbook contains a guide, 15-candidate summary, 100
  primary cases, 140 supplemental-v1 cases, five PATH-S06 extension cases,
  count reconciliation, and 29 human records.
- Primary case rows reconcile to 40 security and 60 functional observations;
  all 100 passed their registered primary oracles.
- Supplemental-v1 rows reconcile to 60 security, 45 parity, and 35 robustness
  observations: 120 pass, 15 fail, and five inconclusive.
- Extension rows remain separate and reconcile to zero pass, five fail, and
  zero inconclusive.
- Public browser validation passed pagination and candidate, layer, result, and
  case-search filters. The selected export omits local-user paths, transient
  loopback ports, OpenAI response identifiers, and credential variable names.
- The full unit-test suite passed 131/131 tests after the reporting update.

## Required updates before submission

1. Replace the effort checkpoint with Tony's actual dates and hours.
2. Add the Video III feedback summary and dispositions after feedback is
   received.
3. Deploy the updated static package only when Tony chooses to update Netlify,
   then validate the live URL.
4. Record the broader clean-package verification result after it is performed.
5. Confirm the live Canvas deadline, remove the early-draft status note, change
   the report date, and inspect the final Word/PDF rendering.
