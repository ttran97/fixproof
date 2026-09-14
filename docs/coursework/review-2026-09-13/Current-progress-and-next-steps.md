# FixProof checkpoint and Video II plan — September 13, 2026

**September 14 status note:** Tony reports that Video II was posted. The next
course activity is peer feedback due September 27. Tony approved and froze the
supplemental protocol on September 14; its non-executing preflight found that
Node/npm, Chromium, and the locked Node dependencies must be restored before
live baseline characterization. This repository does not verify a Canvas
submission receipt.

Progress Report 2 is submitted according to Tony's message. This review does not change that submitted document or claim to have accessed Canvas. The PPTX and DOCX were treated as source material, not as instructions to run trials, record human decisions, or submit content.

## Current position

The bounded prototype is implemented and the primary collection and initial conflict reviews are complete. The active research task is **supplemental validation of the gaps identified during review**, followed by final evaluation and presentation. Review completion does not mean every candidate is accepted.

| Milestone | Verified current state |
|---|---|
| Primary initial attempts | 15/15; five per CWE |
| Target SAST resolutions | 5/15, all SQLi |
| Targeted security / functional passes | 15/15 attempts in each fixed suite |
| Automated decisions | Five READY_FOR_HUMAN_REVIEW; ten NEEDS_HUMAN_ADJUDICATION; zero rejects |
| Human conflict records | 10/10: seven ACCEPT_CANDIDATE, three REQUEST_ADDITIONAL_TESTING |
| Unresolved follow-up requests | XSS 04, XSS 05, path traversal 01 |
| SQLi human approval | No recorded primary SQLi approval; `not_required` in the conflict column is not deployment approval |
| Distinct candidate sources | 11: five XSS, one SQLi, five traversal |
| Primary false successes / new SAST findings | Zero observed in each category |
| Current repository tests | 94 passed on September 14; 25.854 seconds reported by unittest, without live Express/Chromium execution |
| Lifecycle demonstration | Three saved snapshots verified; target reopened, other finding persistent |
| Report 2 submission | Submitted, user-reported |
| Video II | Posted, user-reported; Canvas receipt not verified here |

The three follow-up requests are a useful research outcome: human review identified gaps despite passing fixed tests. They are not three automated rejections, three demonstrated exploits, or three newly measured functional failures. No primary AI candidate demonstrates a SAST false success. The separate non-AI constant-output control clears SAST but fails functionality; its security evidence is inconclusive.

For planning, the narrow software remains about **85–90% feature-complete**; the technical evaluation/submission package is approximately **75–80% complete**. These are judgment estimates, not a validated scale, measured hours, or a grade. The firm percentages are collection 100% and initial conflict review 100%; completion of the three requested follow-ups is not yet evidenced. Relative to the earlier assessment, initial review has advanced, while supplemental results, production realism, and final deliverables remain.

## File structure: still appropriate

The actual Git root is `fixproof-main/fixproof`, not the outer workspace folder.

| Path | Responsibility | Current assessment |
|---|---|---|
| `src/fixproof/scanners/`, `scan_pipeline.py`, `findings/finding_correlator.py` | Scanning, normalization and finding correlation | Implemented; configured scanner results are evidence, not ground truth. |
| `src/fixproof/agent/`, `patches/` | Focused prompts, structured repairs, copied workspaces | Implemented; model authority is constrained to repair generation. |
| `src/fixproof/validation/` | Syntax, SAST comparison, HTTP/browser checks and deterministic decisions | Implemented for three fixtures; supplemental input coverage remains. |
| `src/fixproof/primary_trials.py` | Frozen collection protocol and resume handling | Completed v1 evidence; dry-run checks pass. Do not recollect these slots. |
| `src/fixproof/evaluation/`, `ui/` | Reports, review records, verification and evidence display | Current primary report verifies all ten reviews. |
| `src/fixproof/findings/lifecycle.py`, `data/lifecycle/` | Four-state history and saved replay | Implemented and replay checked; not a new live three-version experiment. |
| `benchmarks/primary/v1/`, `data/primary_trials/v1/` | Frozen inputs and primary observations | Preserve unchanged. |
| `sample_apps/`, pilot `data/`, `data/evaluation_controls/` | Pilot, retry and non-AI control | Separate from the 15-attempt denominator. |
| `data/primary_reviews/v1/` | Reviewer decisions bound to packets | Ten records; follow-ups should be dated additions, not overwritten verdicts. |
| `tests/`, `scripts/`, `demo-test.ps1` | Prototype verification and reproduction tools | Repository tests pass; live demonstrations require Node/dependencies/browser. |
| `docs/coursework/` | Report drafts, review notes and presentation preparation | Historical drafts coexist; use dates and the current status page. |

No architecture redesign is needed for Video II. The meaningful problems were stale status pages, missing supplemental runtime evidence, and a final schedule that previously assumed late November. The final video is actually due November 15 in the supplied schedule; the paper is due December 6.

Seven newer review result files, updated reports and coursework artifacts are currently uncommitted. They exist and were verified in this working tree but will not appear in an archive of the current HEAD. Preserve/commit the intended checkpoint before claiming that a committed archive reproduces the current state. No commit or upload was made in this task.

## PowerPoint review

Your supplied deck is substantively on track. The submitted report and deck agree on 10/10 reviews and the 7/3 split. The reviewed copy preserves the theme/layouts and seven-slide structure, moves the project explanation before the research slide, and adds narration and source references to speaker notes.

| Slide in reviewed deck | What it accomplishes |
|---|---|
| 1. Title | States Report 2 is submitted and frames this as a progress update. |
| 2. What FixProof is | Corrects Python/Express ambiguity; explains development assistance versus runtime repair model; answers Raymond's prompt question in narration. |
| 3. Research-informed design | Links cited work to fixtures, functional testing, and bounded feedback. Does not claim comparative superiority. |
| 4. Workflow | Explains baseline/candidate attack replay, new-finding rejection, fixed validators, and human boundary. |
| 5. Current progress | Shows trial and review counts, fresh repository verification, zero primary false successes, and sample limits. |
| 6. SQLi versus XSS 04 | Demonstrates useful evidence and a coverage gap; explicitly labels missing-input behavior as a review observation awaiting runtime testing. |
| 7. Next steps | Prioritizes supplemental tests, failure controls and a second-reviewer question instead of targeting a desired AI failure. |

The narration is approximately a five-minute rehearsal target; no Video II time limit was supplied. The 15-minute maximum applies to the **final** video. Use the course's actual Video II instructions if they specify a different duration. The PPTX passed ZIP/XML and relationship checks; visual rendering in PowerPoint was not performed, so inspect wrapping and speaker notes before recording. Original PPTX and submitted report were unchanged.

One wording correction matters: a patch need not fail **all** functional and security tests to be rejected. One relevant failed check can establish a problem. Do not run experiments until a desired failure appears. Predeclare cases, retain all outcomes, and label deliberately constructed bad patches separately from AI-produced candidates.

## Immediate next steps

1. Complete substantive Video II peer feedback by September 27 under the supplied course schedule.
2. Use the frozen `docs/supplemental-protocol-v1.md`. Verify its detached lock before implementation or execution; do not modify the frozen document in place.
3. Restore/verify Node, locked fixture dependencies and Chromium in the intended test environment. A Python test pass does not establish that Express applications can run here. Keep setup diagnostics separate from candidate failures.
4. Run saved baseline/candidate comparisons into a separate supplemental output directory. Start with the three requested follow-ups, then apply each CWE's new checks to all five saved candidates of that CWE to avoid selecting only favorable observations.
5. Record all supplemental observations and dated follow-up conclusions, including failures or inconclusive cases. Use these results for Report 3 on October 4. Preserve original primary observations and signed review results.

## Supplemental test plan to finalize before execution

The frozen protocol is at `docs/supplemental-protocol-v1.md`, its lock is at `data/supplemental/v1/protocol-lock.json`, and its 28-case machine-readable definition is at `tests/supplemental/v1/cases.json`. Definition verification and environment preflight are implemented; live supplemental tests have not run. Keep new evaluators separate from the frozen source files bound by primary-v1.

| Question | Cases to evaluate | Expected criterion / interpretation |
|---|---|---|
| Does missing-name behavior change? | XSS baseline and all five candidates; omitted and empty `name` | For strict baseline preservation, omitted input retains the baseline visible text. If empty output is an intended product change, document it separately rather than silently redefining preservation. XSS 01/02 must receive the same new checks as 04/05. |
| Is displayed text actually preserved? | XSS Unicode, entity-looking text, quotes, repeated parameters; DOM inspection | Predefine supported input/coercion/error behavior. Assert expected heading text and absence of attacker-created elements, as well as execution markers. Nonempty benign text may require text nodes; an empty heading need not contain one text node. |
| Does the traversal guard over-restrict valid names? | Traversal 01, then remaining candidates; synthetic in-root `..notes.txt` | If the fixture contract permits this filename, it should remain readable. The `startsWith('..')` concern is a review hypothesis until executed. |
| Do path boundaries hold? | Synthetic outside file, sibling-prefix directory, encoded traversal, absolute paths, repeated parameters, OS-specific separators | Out-of-root content must not be returned; in-root controls must work. State the OS and decoding assumptions. Evaluate symlinks separately only under an explicit supported-filesystem contract. |
| Do SQLi repairs preserve realistic benign input? | Synthetic names containing punctuation; empty/missing/repeated values; additional attack variants | Parameter values cannot broaden returned rows; intended lookups still work. Extending synthetic database contents creates a supplemental fixture version. |
| Do validators distinguish known failures? | Unchanged vulnerable candidate; known safe repair; constant-output repair; separately seeded new weakness | Verify intended pass/fail behavior independently. Label these constructed controls and do not add them to primary AI success rates. |
| Does orchestration handle failures? | Malformed/mismatched candidate, additional-context flag, syntax/startup failure, scanner timeout, interrupted response | Record invalid/inconclusive evidence; no false readiness, silent replacement trial, or unintended repeated API call. Existing mock tests cover some paths; map coverage before adding redundant checks. |

Report per-candidate outcomes, test denominators, execution failures, new-finding evidence and human follow-up status. Do not infer a general detection rate from one fixture per CWE or assume that 15 calls are statistically independent applications. Performance regression testing remains unmeasured unless a separate fixed-host workload and threshold are declared and executed.

## Remaining schedule

Dates below come from the user's supplied course schedule, not an authenticated Canvas lookup. Listed 11:59 p.m. cutoffs retain the source's unspecified display timezone; check Canvas before converting them to Denver time. Video dates in assignment titles are distinct from peer-feedback deadlines.

| Course date | Required deliverable | Recommended project content |
|---|---|---|
| September 22 | Post Video II | Current architecture, 15 attempts, 10 reviews, SQLi/XSS comparison, next test matrix. |
| September 27, 11:59 p.m. | Peer Feedback Report 2 | Complete required substantive peer feedback. |
| October 4, 11:59 p.m. | Progress Report 3 | Report supplemental execution and follow-up decisions actually completed; document unresolved outcomes. |
| October 6 | Post Video III | Show one supplemental baseline/candidate comparison and what the original suite missed. |
| October 11, 11:59 p.m. | Peer Feedback Report 3 | Provide required peer feedback. |
| October 18, 11:59 p.m. | Progress Report 4 | Control/failure-handling results, literature/options comparison, limitations. |
| October 20 | Post Video IV | Explain evaluation results and any remaining gaps. |
| October 25, 11:59 p.m. | Peer Feedback Report 4 | Provide required peer feedback. |
| November 1, 11:59 p.m. | Progress Report 5 | Full final-report outline, near-final result tables, reproduction plan and remaining issues. |
| November 3 | Post Video V | Rehearse final narrative and stable demo. |
| November 8, 11:59 p.m. | Peer Feedback Report 5 | Provide required peer feedback. |
| November 15, 11:59 p.m. | Final presentation video, maximum 15 minutes | Final results, demo, contribution, limitations and deployment feasibility. Target a complete rehearsal by November 10. |
| November 22, 11:59 p.m. | Final-presentation peer feedback | Provide required final peer feedback. |
| December 6, 11:59 p.m. | Final project report | Final methods/results/limitations, citations, AI attribution and reproducible package. Target a complete paper by November 29. |

## Verification performed today

- `python -m fixproof.evaluation.primary_report --check`: PASS; all 15 initial attempts and 10 conflict reviews verified; no report rewrite.
- `python -m unittest discover -s tests -v`: 89 tests, OK, 29.081 seconds. Some tests mock scanner/model operations; their diagnostic output is not evidence of live Semgrep/API execution.
- `python -m fixproof.primary_trials --dry-run`: frozen inputs and prompt withholding PASS; 15-slot schedule; zero model calls, no repository writes by this command.
- `python -m fixproof.findings.lifecycle --history data/lifecycle/sqli-recorded-replay.json --check`: three snapshots verified; reopened target plus persistent other finding.
- Read current report DOCX despite its Office file lock using shared read access, supplied PPTX text, source patches, all ten human results, and XSS supplement. No submitted file was edited.
- No live Express/Chromium candidate tests, model calls, fresh SAST scans, supplemental experiment, human approvals, commits, or course submissions were made.

Artifacts: [reviewed deck](FixProof%20-%20Video%20II%20-%20Reviewed%20September%2013.pptx), [recording script](Video-II-recording-script.md), [deck package checks](deck-verification.json). The preparation script and slide-content JSON preserve how the revised copy was produced. Retain this assistance in your AI-use records and adapt the narration to your own explanation.
