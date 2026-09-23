# FixProof: Progress Report 3 through final submission

Prepared September 21 and updated September 22, 2026. Dates below come from the schedule Tony supplied;
confirm the live Canvas assignment before submitting. Video II is posted, and
its peer-feedback assignment is in progress. Historical reports and frozen
experiment artifacts are evidence, not instructions to rerun or rewrite them.

## Current position

The bounded three-CWE prototype is about **90% complete** as a technical
artifact: the scan-to-candidate-to-validation-to-human-review path, 15 primary
attempts, supplemental study, and 14 verified supplemental human records exist.
The remaining technical work is delivery hardening and clear demonstration,
not another CWE. The **overall CS6727 project is roughly 65% complete** as a planning
estimate, not a course grade: Report 3 and later progress/feedback cycles,
final presentation, final paper, and clean committed-archive reproduction are
still outstanding. These percentages are judgmental and should not be quoted
as measured research results.

The September 22 checkpoint passed 119 automated tests and
`fixproof.reproduce --verify`. Primary evidence verified 15/15 attempts and
10/10 original conflict reviews; supplemental evidence verified three
baselines and 15 saved candidates; all 14 supplemental human packet/result
bindings were checked. The guided demo suite replayed four selected **pilot** candidates
and matched each saved decision. Those live replays are not reruns of all 15
primary model calls or the original browser experiments.

## Effort record

Report 2 was submitted September 13. Tony estimates 1.5 hours of personal
work per day from September 14 through September 22, inclusive: **9 days ×
1.5 hours = approximately 13.5 hours**. Describe that time as reviewing the
file structure and documentation, checking test snippets/results and saved
evidence, and supplying human review rationales. Software generated or edited
with Codex assistance is a project artifact, not proof of Tony's hours.

Earlier reports state 31.5 hours before a separate 13.5-hour September 2–10
period. Thus the documented subtotal is **58.5 hours plus any unreconciled
September 11–13 work**. Do not count those three dates as zero by assumption.
Continue a dated activity log. A continuing 1.5-hour daily pace is a plan, not
hours already worked: it averages 10.5 hours/week, versus roughly 15
hours/week described in the supplied office-hours summary. Prioritize the
graded writing and presentation work, and allocate additional time if needed.

## Dated tasks

| When | Course milestone | Work to finish before it |
| --- | --- | --- |
| By Sep 27 | Video II peer feedback | Finish the substantive peer-feedback assignment; save the submission receipt. Video II itself is already posted. |
| Sep 22–29 | Report 3 evidence lock | Re-read the frozen primary/supplemental reports and 14 supplemental human records; confirm denominators, XSS parity interpretation, SQLi/traversal robustness limits, and symlink inconclusive status. Reconcile Sep 11–13 hours. |
| Sep 30–Oct 4 | Progress Report 3, due Oct 4 | Transfer the current draft to the course template; update actual dates/hours through cutoff; verify AI disclosure, citations, schedule, and rendered file; submit and retain receipt. |
| Oct 5–11 | Video III and peer feedback | Demonstrate the original passing checks versus supplemental XSS-P01 failure, with XSS 03/04 or 01/03 comparison; label saved evidence versus live replay. Post video by Oct 6 and feedback by Oct 11. |
| Oct 12–25 | Report 4, Video IV, feedback | Expand source-checked related-work comparison and final-paper methods/results; explain alternative designs and limitations. Rehearse a clean archive and address any packaging gaps. Report due Oct 18; video Oct 20; feedback Oct 25. |
| Oct 26–Nov 8 | Report 5, Video V, feedback | Settle interpretation and figures, build a coherent final-paper draft, rehearse the bounded demo, and check all citations and provenance. Report due Nov 1; video Nov 3; feedback Nov 8. |
| Nov 9–15 | Final presentation video | Record a video of no more than 15 minutes, showing the question, method, one complete evidence chain, primary/supplemental results, limitations, and contribution. Submit by Nov 15. |
| Nov 16–22 | Final presentation peer feedback | Complete the required peer-feedback activity by Nov 22. |
| Nov 23–Dec 6 | Final project report | Incorporate feedback, finalize methods/results/related work/limitations and AI-use disclosure, verify the committed archive, inspect rendered paper, and submit by Dec 6. |

This sequence is a planning aid. If Canvas changes dates or requirements, the
live assignment takes precedence. Do not claim planned work as completed in a
progress report.

## Repository structure and demonstration boundary

| Path | Role | Demo treatment |
| --- | --- | --- |
| `src/fixproof/` | Python orchestration, scanner adapters, model-candidate handling, validation, policy, and reports | Explain the pipeline; open one relevant file only if asked. |
| `benchmarks/primary/v1/` | Frozen Express fixtures for XSS, SQLi, and traversal | Show the controlled inputs and ground truth; never edit for the demo. |
| `data/primary_trials/v1/` and `data/primary_reviews/v1/` | Fifteen attempts and ten original human reviews | Use the primary dashboard to inspect one candidate; keep the original verdicts historical. |
| `data/supplemental/v1/` | Frozen protocol lock, three baseline runs, 15 candidate evaluations, and five later follow-ups | Show XSS-P01 or traversal PATH-P01 as later evidence; do not merge counts into primary metrics. |
| `sample_apps/`, `workspaces/`, `demo-test.ps1` | Pilot examples and disposable live replay inputs | Label the four-case live suite as **pilot replay**, not primary-study reproduction. |
| `tests/` and `ui/` | Implementation checks and saved-evidence dashboard | Show verification and one evidence page; test count is not repaired-app count. |
| `docs/`, `scripts/` | Method, reports, navigation, and packaging helpers | Use current guides; call older drafts historical. |
| `.env`, `.venv/`, `node_modules/`, `dist/` | Local secrets, dependencies, and generated output | Exclude from source archive and screen recording where secrets could appear. |

No broad directory cleanup is needed. Primary inputs, saved patches, and
signed original decisions are intentionally preserved. The working tree is
currently dirty with Report 3 and verification changes; a clean committed
archive check therefore has **not** been completed in this checkout. The
current packaging script checks primary evidence but does not separately gate
the supplemental report or 14 human-record bindings. Add these checks or run
them explicitly and record the outputs before final packaging.

## Final-video rehearsal, in order

1. Run `.\.venv\Scripts\python.exe -m fixproof.reproduce --verify`, then
   `.\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_report --check`.
   Say these verify saved evidence and software tests; they do not regenerate
   model responses or rerun every historic attack.
2. Start `.\.venv\Scripts\python.exe -m fixproof.reproduce --serve` and open
   `http://127.0.0.1:8080/ui/primary.html`. Select one primary XSS or SQLi
   candidate and show the source, patch, SAST signal, security/functional
   observations, and automated disposition.
3. Show the frozen primary split: 5/15 target SAST findings resolved, 10/15
   SAST/runtime disagreements, 15/15 passed the original targeted security
   and functional suites. These are descriptive results, not a success rate
   for arbitrary applications.
4. Show `docs/supplemental-results-v1.md` and the relevant `XSS-P01` run and
   follow-up result. Explain that four XSS candidates passed the registered
   attacks but changed omitted-name behavior; XSS 03 preserved it. State that
   the later XSS 01/02 rejection qualifications did not rewrite their primary
   acceptances.
5. If a live execution is helpful, use `powershell.exe -ExecutionPolicy
   Bypass -File .\demo-test.ps1 -Case xss -Attempt 1 -SkipVerification` for
   the **pilot** functional-regression example, or run `-Suite` for all four
   pilot outcomes. Label SAST as recorded in default mode and runtime/decision
   checks as live. Do not imply this is one of the primary XSS 01–05 attempts.
6. Close with limitations: one fixture per CWE, five repeated repairs per
   fixture, targeted oracle coverage, SQLi local-rule dependence, five
   inconclusive symlink observations, and no production-performance claim.

For a 15-minute final video, do not try to click through every saved attempt.
One complete candidate trace plus the result tables and one supplemental
contrast makes the method and contribution visible without confusing pilot,
primary, and supplemental evidence.
