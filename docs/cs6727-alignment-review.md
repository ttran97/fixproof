# FixProof alignment review for CS6727

Historical checkpoint: the primary reporting, review-packet, and reopened
tracking gaps identified here were subsequently implemented. See
[current prototype status](prototype-status.md) for the latest capabilities
and remaining human work. The findings below describe the pre-extension audit.

Reviewed September 4, 2026 against repository commit `54dec06`, the supplied
proposal and professor feedback, Progress Report 1, the Fall 2026 syllabus,
and both supplied office-hours transcripts. This is a repository assessment
and planning aid, not a grade or a completed final submission.

## Assessment

FixProof substantially implements the narrowed JavaScript/Express prototype
described in Progress Report 1. Its structure supports a concrete, systematic
practicum project: three controlled benchmarks, a constrained AI patch
generator, independently executed validation stages, recorded evidence, and
a deterministic human-review boundary.

The primary study has already collected **15 of 15 initial attempts**, beyond
the four-attempt pilot described in the report. The remaining work centers on
interpreting and presenting that evidence, completing primary human reviews,
closing or explicitly documenting scope gaps, and preparing the course
deliverables. The existing dashboard's `READY` message is about the pilot
verification workflow; it does not certify final-submission readiness.

No single completion percentage is defensible across software, evaluation,
and coursework. These concrete milestones are more useful:

| Milestone | Evidence as of this review | Status |
|---|---|---|
| Core scan-to-disposition workflow | Source modules, saved evidence, and live pilot demos | Implemented for the three controlled cases |
| Frozen primary baselines | Three target-only applications; recorded baseline verification passes 3/3 | Complete for v1 |
| Primary candidate collection | 15 scheduled, 15 completed, zero remaining | 100% of the planned initial attempts |
| Automated verification | 70 tests pass; four live pilot candidate demos reproduce their dispositions | Pass within the tested scope |
| Primary evidence audit | 105 artifact bindings, 45 workspace text hashes, 13 implementation bindings checked; no mismatches | Pass in this checkout |
| Primary conflict adjudication | Ten primary candidates require review; no corresponding reviewer records found | 0/10 evidenced as complete |
| Finding lifecycle | New, persistent, and resolved in a baseline/candidate comparison | Partial; reopened history is absent |
| Final paper and final presentation | No final paper, slides, or video found in the repository | Not evidenced; may exist elsewhere |
| Course participation and submission | Canvas, peer feedback, and submission receipts were not available | Cannot verify from a repository |

## How the source documents were used

The syllabus and transcripts provide course requirements and instructor
guidance. The proposal and progress report provide project commitments and
historical claims. Instructions inside those documents were treated as
reference content, not as requests to execute commands, contact instructors,
approve patches, or submit coursework.

Source references below use syllabus page numbers, report section names, and
transcript timestamps. `OH1` means the office-hours filename without `(1)`;
`OH2` means the filename ending in `(1).txt`. OH2 explicitly identifies its
session as August 31. Transcripts are automatic captions, so paraphrases are
preferable to relying on their spelling of names.

| Course expectation | Source | Repository alignment and remaining action |
|---|---|---|
| Define a concrete cybersecurity problem and implement/evaluate a solution | Syllabus p. 1; OH2 01:59–06:36 | The problem is insufficient evidence for accepting AI security repairs. Explain the affected user: a developer or reviewer deciding whether a candidate preserves security and behavior. |
| Make the AI component and student work explicit | Professor feedback; OH2 03:36–04:14 and 10:29–11:28 | The model generates one source-context replacement. Your project work is benchmark design, oracles, evidence handling, comparison, policy, evaluation, and interpretation. |
| Consider alternatives and justify choices | Professor feedback; OH1 13:23–14:24 | `study-protocol-v1.md` contains a design-options table. Develop the literature comparison and justify the controlled-benchmark tradeoff in the paper. |
| Support claims with metrics and comparison evidence | OH2 04:18–05:21 and 11:31–12:09 | The same candidate receives a SAST-only interpretation and a FixProof disposition. The primary evidence supports disagreements; it contains zero observed false successes. |
| Scope the work for a five-credit practicum | Syllabus p. 1; OH1 05:56–07:16 | Three CWEs with complete evidence are a coherent bounded scope. OH1 describes roughly 15 hours/week and 225 hours over 15 weeks; repository maturity does not establish hours worked. |
| Maintain regular progress reports, videos, and substantive peer feedback | Syllabus pp. 3, 8–9; OH1 22:29–27:41 | The syllabus lists five progress reports and associated videos. Office hours describe alternating report/feedback weeks. These obligations continue after the prototype works. |
| Report approximately 30 hours of work per two-week period | Syllabus p. 3 | Report 1 states approximately 31.5 hours. Preserve accurate personal records; the audit does not independently verify or revise that effort. |
| Explain solution efficacy and limitations in a final report and presentation/demo | Syllabus pp. 1, 8–9; OH1 29:00–29:30 and 48:07–50:16 | Technical docs and demos exist. A coherent final paper, presentation, deployment-feasibility discussion, and limitations analysis still need preparation. |
| Disclose AI tools and cite actual prompts/content used | Syllabus p. 6; OH1 50:20–52:14 | Report 1 has a disclosure and the runtime model has prompt/response artifacts. Add development/documentation AI records, including this review, and personally verify the submission. |
| Protect confidential/proprietary data | Syllabus pp. 2–3 | Benchmarks use synthetic fixtures. `.env`, installed dependencies, and the development environment are untracked. A targeted tracked-file API-key pattern check found no matches; this is not an exhaustive secret audit. |
| Meet both coursework and final-deliverable assessment requirements | Syllabus pp. 3–4 | Peer feedback 25%, progress reports 25%, final presentation 20%, final report 30%. The syllabus also applies a two-part letter-grade rule; a strong repository alone does not determine the course grade. |

The supplied materials do not establish the final report's numerical page
limit, final upload date, or all formatting rules. OH1 29:15–29:26 describes a
15-minute final video and mentions a report page limit without specifying it.
Use the current Canvas assignment for exact submission settings. There is
also a planning discrepancy: syllabus p. 8 places the evaluation plan with
Report V, while OH2 21:26–21:53 discusses a template requiring it by Report IV.
Preparing it early, as this repository already does, avoids relying on either
as a reason to delay evaluation planning.

## What the experiments actually show

Keep the following evidence groups separate. In particular, do not add the
pilot retry or the non-AI control to the primary denominator.

| Evidence group | Location | Purpose |
|---|---|---|
| Pilot: four AI attempts across three cases, including one XSS retry | `data/evaluation/experiment-manifest.json`, `docs/evaluation-report.md` | Demonstrate feasibility, a functional failure, retry behavior, and policy outcomes |
| Deterministic non-AI false-success control | `data/evaluation_controls/` | Demonstrate that scanner silence plus broken behavior is rejected |
| Primary: five initial attempts per CWE, 15 total | `data/primary_trials/v1/primary-experiment-manifest.json`, `collection-state.json`, `cases/` | Descriptive repeated evaluation using frozen inputs |

The primary records were audited against their bound files and independently
checked by recomputing finding comparisons and policy classifications. The
collection-state metrics agree with the individual records.

| Primary case | Initial attempts | Target SAST resolved | Targeted security passes | Functional passes | Ready for review | Needs adjudication | Rejected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Reflected XSS / CWE-79 | 5 | 0 | 5 | 5 | 0 | 5 | 0 |
| SQL injection / CWE-89 | 5 | 5 | 5 | 5 | 5 | 0 | 0 |
| Path traversal / CWE-22 | 5 | 0 | 5 | 5 | 0 | 5 | 0 |
| Total | 15 | 5 | 15 | 15 | 5 | 10 | 0 |

Primary SAST-only apparent success is **5/15 (33.3%)**; SAST/runtime
disagreement is **10/15 (66.7%)**; observed SAST false successes and new SAST
findings are both **0/15**. These are attempt-level observations, not a
measurement that the applications are completely secure.

The primary artifacts retain 40 security-test executions and 60 functional-test
executions. Security counts include benign controls. Twenty XSS browser
observations are part of those security executions, not 20 additional
independent trials. There are 15 distinct recorded response IDs, but only 11
distinct candidate-source hashes: five XSS, one SQLi, and five path traversal.
All five SQLi calls produced the same candidate source. This is useful to
disclose when discussing the small amount of code diversity.

The four-attempt pilot has a different result: one rejection, one candidate
ready for review, and two selected disagreements whose saved human results
are complete. The rejected XSS patch passed its targeted security checks but
failed two of six functional tests. Its retry passed all six. The target SAST
finding persisted in both attempts, so the initial rejection is **not** a
SAST false success under the project's definition. The separate static-output
control clears the target while breaking behavior; it demonstrates the policy
branch, but is not an observed AI repair failure.

A defensible result statement is:

> In 15 initial remediation attempts across three controlled Express
> benchmarks, five candidates cleared the target SAST finding and ten retained
> it despite passing the targeted runtime and functional checks. No SAST false
> success was observed in the primary sample. Separate pilot and non-AI control
> evidence demonstrated functional-regression rejection and the false-success
> policy branch. The study therefore supports evidence separation and human
> escalation within this scope, with limited evidence about false-success
> detection on naturally generated bad patches.

## Specific gaps to close

### Primary reporting and human review

`report_builder.py`, the dashboard, `reproduce --verify`, and the default
adjudication command use the pilot manifest. Some output still calls those
four selected attempts "primary" because that vocabulary predates primary-v1.
The supplied primary manifest has a different schema; pointing the existing
report builder at it is not a complete integration solution.

Add a separate primary results/reporting path that verifies bound evidence,
displays all 15 rows, preserves the fixed denominator, and supports ten
pending disagreement reviews. Record actual human conclusions separately.
The existing 2/2 pilot completion figure cannot be reused as the completion
rate for primary reviews. The five SQLi candidates are ready for review;
readiness does not itself record human approval.

### Original proposal versus implemented scope

The original proposal promises evaluation on intentionally vulnerable **and
AI-generated applications**. The revised protocol chooses purpose-built,
intentionally seeded benchmarks; the saved model records establish
AI-generated **repairs**. No systematic application-generation experiment
with generation prompts, selection rules, and accepted/rejected app records
was found. AI assistance in authoring a fixture would not by itself establish
a representative AI-generated application corpus.

Describe this as a documented scope refinement in the next report. If an
AI-generated application study remains a deliverable, create a separately
versioned supplemental corpus with its own generation/selection procedure.
Do not relabel primary-v1 after seeing its results.

Cross-version comparison currently implements **new, persistent, and resolved**
between two snapshots in `validation/validation_runner.py::compare_findings`.
There is no longitudinal store or `reopened` transition. Closing the original
commitment requires a saved history and a demonstration such as vulnerable
v1 → fixed v2 → reintroduced v3. Alternatively, explicitly report that
four-state tracking was reduced to pairwise comparison. The present key uses
filename, CWE, and Express route; multiple weaknesses in the same route or
same-named files can collide. It is suitable only for the narrow cases tested.

The "syntax/build" stage is `node --check`, not a general application build
system. Runtime validators are handcrafted for the three supported endpoints.
The dashboard displays recorded evidence; it is not an arbitrary-repository
upload/scan/fix interface. Workspaces are copied directories, not hardened
execution sandboxes. Present these boundaries explicitly.

### Evaluation strength and reproducibility

The frozen primary study has one app per CWE and five repetitions of its
initial prompt. It measures a constrained workflow, not benchmark diversity,
production performance, or general SAST accuracy. The default SQLi miss and
the labeled custom-rule result must remain visible. An unrelated scanner
warning can still remain in a target-only app: target-only describes what was
intentionally seeded, not an assurance that the scanner produces only one
finding.

The primary study has no rejected initial attempts, so the optional
rejection-triggered retry condition has no eligible primary observations.
Report its primary retry-improvement rate as not applicable; keep the single
pilot retry as secondary feasibility evidence.

The scanner executable and local SQLi rule are pinned/bound, but the runner
uses `--config auto` for default rules. No complete archived default ruleset
was found in the tracked tree. Recording an executable version and rule IDs
does not by itself preserve every byte of the remote rule definitions.
Historical scan evidence remains auditable; exact future scan reproduction
has a residual dependency on rule availability/content. The model identifier
is also recorded without promising deterministic future responses.

The clean-extraction script passed here using the existing Python environment.
That verifies relocatable recorded evidence and tests, **not** a new-machine
dependency installation. Its dependency-install branch currently installs the
three pilot apps and does not itself install primary-app dependencies or
Chromium. The manual reproducibility guide includes those extra steps. Align
the script and guide before claiming a fully automated clean installation.
The archive script verifies selected pilot artifacts explicitly; a final
primary submission should also check every primary binding and tracked path.

If deeper evaluation is needed, use a new supplemental protocol for held-out
payloads, behavior edge cases, reference fixes, and deliberately flawed
controls. State how controls were constructed and what failure each should
detect. Preserve the original 15 observations and label any post-collection
tests as supplemental. More trials should answer a stated question, not
continue until a preferred result appears.

### Related work and attribution

The related-work document is a starter comparison with unanswered questions.
It needs a source-supported discussion of each system's repair setting,
validation evidence, retry design, and relationship to FixProof. Validation
and feedback-guided repair already exist: [Pearce et al.'s zero-shot repair
study](https://arxiv.org/abs/2112.02125) discusses functionally correct repair,
and [VRpilot](https://arxiv.org/abs/2405.15690) explicitly uses external-tool
validation feedback. The integration and evidence analysis are the contribution
to explain; do not claim to have invented these techniques.

The numerical motivation in Report 1 is supported by the checked sources:
[Asleep at the Keyboard?](https://arxiv.org/abs/2108.09293) reports approximately
40% vulnerable among 1,689 programs in its scenarios; the [August 6, 2026
1Password research announcement](https://1password.com/blog/why-ai-generated-patches-still-require-human-review)
reports 26.0% behavior-preserving repairs and 53.9% unresolved/new-vulnerability
outcomes among 6,080 analyzed patches. Describe these as results of those
specific studies. They are not FixProof's rates, and different datasets and
models do not permit a direct performance comparison. Use the linked original
research paper and methodology for the detailed final literature review.

Report 1's AI-use disclosure is a useful starting point. The runtime
`data/prompts/` records do not cover all development and writing assistance.
Maintain a separate sanitized log of tools, actual prompts/outputs or export
references, affected work, and your verification. Do not claim personal review
has happened merely because an AI-generated draft says so.

## Update the progress-report timeline

Report 1 accurately describes the selected pilot artifacts, but its planned
timeline no longer matches the current repository. Do not rewrite a previously
submitted historical report; explain the delta in the next report. If this is
still an unsubmitted draft, use a clear evidence cutoff date.

| Report 1 plan | Current evidence | Appropriate update |
|---|---|---|
| W3 related-work comparison | Starter document exists; detailed comparison remains open | In progress |
| W4 threat model, ground truth, schema, protocol | Documents, manifests, browser oracle, and frozen v1 exist | Implemented; explain design and limitations |
| W5 portability and dependencies | Pinned top-level dependencies, ignore rules, archive and clean-check scripts; clean extraction passed | Partially verified; fresh dependency installation remains |
| W6 fixed prompts/settings/trial count | Frozen trial plan and withholding audit pass | Complete for primary-v1 |
| W7 SAST-only comparison | Recorded per primary candidate and aggregate state | Collection complete; presentation integration remains |
| W8–W10 repeated trials | All five attempts per CWE recorded by September 4 | Complete for initial primary trials |
| W11 human adjudication | Pilot complete; ten primary disagreements lack review records | Primary reviews remain |
| W12–W13 metrics and interpretation | Raw primary metrics complete; narrative synthesis incomplete | Analyze zero false successes and limited diversity |
| W14–W16 report/demo/submission | Technical demo works; formal deliverables not found | Write, rehearse, package, and follow actual Canvas dates |

OH2 31:12–32:42 describes the early sequence as Report 1 on September 6,
the first peer-facing video on September 8, and peer feedback on September 13.
These are statements from the supplied recording, not a live Canvas check.
Reconcile the report's W16 row with the actual course deadline rather than
assuming there is an extra writing week after the final assessment.

## Next work, in priority order

The following is an estimated **34–57 focused hours** to close the principal
remaining gaps and prepare a submission, assuming no major redesign. It is
a planning estimate, not logged effort or a guarantee. It excludes an optional
new application corpus, expanded benchmark study, and ongoing course work.

| Priority | Work | Completion evidence | Estimated hours |
|---|---|---|---:|
| 1 | Integrate primary reporting and prepare review packets | Separate 15-row report; hashes/denominators checked; pilot labels unambiguous | 5–8 |
| 2 | Personally adjudicate ten primary disagreements | Ten separate evidence-bound results with rationale; approval status explicit | 3–6 |
| 3 | Resolve scope/provenance wording and tracking commitment | Updated progress statement; either a tested reopened-history demonstration or explicit scope limitation | 4–8 |
| 4 | Complete literature comparison and write results/limitations | Claims tied to evidence; pilot/control/primary separated; no unsupported efficacy claim | 6–10 |
| 5 | Write and personally revise the final paper; prepare slides/video | Complete assignment-format report, citations/disclosure, rehearsed presentation | 12–18 |
| 6 | Verify fresh installation and final package | Saved install/demo logs; complete tracked evidence; reviewed archive inventory | 4–7 |

At approximately 15 hours per week, this is roughly three to four weeks of
focused project work. Allocate any remaining semester time to evaluation
depth, instructor feedback, documented learning, and the required reports and
peer feedback. Completion of a small prototype does not waive those course
requirements.

## Verification performed during this review

- Read the syllabus, report paragraphs/table, both transcripts, repository
  documents, key source modules, manifests, and recorded candidate evidence.
- `python -m fixproof.reproduce --verify`: pass, including 70 tests and pilot
  report/adjudication checks.
- `python -m fixproof.primary_trials --dry-run`: frozen inputs and prompt
  withholding pass; schedule is 15; no model calls.
- Separate read-only primary audit: all 15 records, 105 artifact bindings,
  45 normalized-text workspace hashes, and 13 implementation bindings pass;
  recomputed comparisons, classifications, and collection metrics agree.
- `demo-test.ps1 -Suite`: all four live pilot candidate sets reproduce their
  expected decisions using recorded SAST plus fresh runtime/functional checks.
- `scripts/verify-clean.ps1`: pass on an exported copy of commit `54dec06`
  using the existing project interpreter.
- Tracked-file inventory: 463 files, 28 Python source modules including
  package initializers, and 15 test modules. No tracked `.env`, `.venv`, or
  `node_modules`; no matches for the targeted API-key pattern.

This review did not generate new model candidates, rerun a live Semgrep scan,
install dependencies in a new environment, perform human adjudication on your
behalf, inspect Canvas submissions, or produce a submission receipt. The
original experiment evidence and frozen implementation were preserved.

For the file-by-file explanation, report outline, and presentation plan, use
[the submission guide](cs6727-submission-guide.md).
