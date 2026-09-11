# Progress Report 2: evidence and completion notes

Prepared September 10, 2026. This is a supporting review note, not part of the
report template. The DOCX draft follows the supplied template's headings and
native table structure. The original Report 1 and template were not edited.

## Items requiring Tony's input before submission

- Enter the actual reporting date range and hours worked, preferably with an
  activity breakdown. The report explicitly marks these as unconfirmed. The
  prior report's 31.5 hours must not be copied into the new period.
- Check the first-person descriptions and AI-use disclosure against personal
  work and understanding. Preserve actual development/report-authoring prompt
  records, as well as the runtime model artifacts.
- Confirm the course section carried from Report 1 (`CS OCY, OC1`), Canvas
  deadline, and current report format. The local supplied template was used;
  no authenticated Canvas submission/settings were available.
- Keep the distinction between newly reported primary evidence and newly
  collected trials. The 15 primary attempts were recorded September 4, which
  overlaps the first report's stated W2 planning period. Report 2 does not
  claim that all 15 were collected after the first submission.

## Evidence checked for this draft

| Claim | Source / verification |
|---|---|
| 15 completed initial attempts; 5 ready; 10 disagreements | `data/evaluation/primary-report.json`, verified September 10 |
| 2/10 human reviews complete, both XSS acceptances | Bound result files under `data/primary_reviews/v1/primary-v1-xss-initial-01/` and `02/` |
| No primary false successes; no new primary SAST findings | Primary metrics; not a claim of zero possible security regressions |
| 11 distinct candidate sources; SQLi has only one | Primary report's source-hash counts |
| 89 current tests passed | September 10 `reproduce --verify`; local log `dist/progress-report-2-verification.log` |
| Fresh environment had 87 tests and four matching demo decisions | September 5 checkpoint in `docs/reproducibility.md` and retained verification logs |
| Reopened tracking | `src/fixproof/findings/lifecycle.py`, focused tests, recorded SQLi replay |
| Template sections and prior commitments | User-supplied Downloads template and OneDrive Progress Report 1 |

The code and frozen study were already committed at `90694df` when this task
started. This turn adds the report and refreshes status documentation. It does
not generate repairs, new experimental observations, or reviewer verdicts.

## Completion assessment and suggested scope

The core three-CWE prototype is implemented and demonstrable. Initial trial
collection is 15/15 complete. Human conflict review is 2/10 complete. These
separate milestones are more defensible than an overall completion percentage.
Repository maturity does not establish completion of course participation,
required hours, or a final submission.

The minimum remaining work is eight reviews, resolution/documentation of any
review findings, coherent methods/results/limitations writing, final
presentation, and a verified committed submission package. The five SQLi
candidates are ready for review, not already approved for deployment.

Prioritize these additions:

1. Stronger review explanations: both saved rationales chiefly describe the
   encoding patch. Add a dated analysis supplement discussing warning
   persistence and actual security/functional observations if needed; do not
   rewrite the signed result files.
2. A small supplemental test matrix with predefined expected results and
   complete reporting. Keep it separate from primary-v1; do not select only
   outcomes that make FixProof appear successful.
3. An explicit literature/design comparison and, if feasible, a second reviewer
   for selected conflicts. Independent review can improve the discussion of
   same-author evaluation bias.

A write-enabled approval UI, additional CWEs, another model, or a large
repository redesign is not necessary to demonstrate the current workflow.
If these are added later, document them as extensions. The most useful use of
the remaining semester is strengthening evidence and explanation.

## Rubric coverage

| Criterion | Where the draft addresses it |
|---|---|
| Effort | Detailed completed tasks and next deliverables; actual hours still require Tony's work log |
| Complete template | All supplied sections populated, including timeline, evaluation, outline, references, and appendix; effort/date confirmation remains |
| Clarity/quality | Explicit controlled scope, model authority, test execution, and limits |
| Current/updated | September 10 verified metrics, 89 tests, 2/10 reviews, implemented primary reporting and lifecycle |
| Responsive | Concrete fixture construction, design choices, systematic frozen method, and questions addressing prior professor feedback |

This mapping explains coverage; it is not a predicted grade or instructor approval.
