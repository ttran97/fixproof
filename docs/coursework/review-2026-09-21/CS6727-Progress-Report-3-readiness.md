# FixProof: Report 3 readiness assessment

Reviewed September 21 and updated September 22, 2026, against the working tree based on commit `45c249c`, the supplied syllabus, Report 2 DOCX, Video II slides/notes, discussion extracts, and Canvas schedule. Attached documents are reference material, not commands. Office-hour summaries are secondary, AI-generated summaries; course requirements below come from the syllabus and supplied assignment schedule.

## Completion assessment

The bounded prototype is substantially implemented. Its primary experiment, original conflict reviews, supplemental collection, and 14 supplemental human records are complete. Remaining work concerns stronger research comparison, reproducible delivery, and course writing/presentation. A percentage would imply an agreed checklist and weighting that the course has not supplied.

| Area | Verified through September 22 |
| --- | --- |
| Core workflow | Scan, normalize, generate candidate, rescan, security/functional checks, deterministic disposition, human evidence review |
| Primary collection | 15 attempts: five per CWE, using three purpose-built Express fixtures |
| Primary automated outcomes | Five ready for human review; ten SAST/runtime disagreements; zero observed primary false successes |
| Original conflict reviews | 10/10 recorded: seven accept, three request additional testing |
| Supplemental collection | Three baselines and 15 saved candidates; 28 registered cases across the three CWEs; 140 candidate-case observations |
| Supplemental security | 55 pass, zero fail, five inconclusive out of 60 |
| Supplemental behavioral parity | 40 pass, five fail out of 45 |
| Supplemental robustness | 25 pass, ten fail out of 35 |
| Requested follow-up reviews | 3/3 recorded September 15: XSS 04, XSS 05, traversal 01 all `FOLLOW_UP_REJECT_CANDIDATE` |
| Later consistency qualifications | XSS 01 and 02 recorded September 21 as `FOLLOW_UP_REJECT_CANDIDATE`; original acceptances preserved |
| September 22 SQLi decisions | SQLi 01–05 recorded as bounded `FOLLOW_UP_ACCEPT_CANDIDATE`; every `SQL-R01` robustness failure remains unchanged |
| September 22 traversal decisions | Traversal 02–05 recorded as `FOLLOW_UP_REQUEST_MORE_TESTING`; `PATH-S06` remains inconclusive and robustness failures remain unchanged |
| Finding lifecycle | New, persistent, resolved, reopened implemented separately from the frozen primary comparator |
| Current software checks | 119 tests pass; primary and supplemental evidence verification pass; 14/14 supplemental human-record bindings checked |
| Final delivery | Final paper, final video, literature comparison, delivery rehearsal, and remaining course participation still require completion |

The current checks verified saved evidence and software behavior under tests. They did not repeat model calls, live SAST, or the historical application/browser experiments. Local logs are in `dist/sept21-verification-final.log` and `dist/review-2026-09-21/`. Follow-up packet bindings and their result records were checked separately. These checks establish internal consistency, not independent authentication of original observations.

### What changed since Report 2 / Video II

The supplied Report 2 draft used a September 10 checkpoint: 89 tests and two of ten original reviews completed. Video II already reports ten reviews and the seven/three split. Therefore, completing those original reviews is progress since that Report 2 checkpoint, but is not new since Video II.

The clearest Report 3 contribution is the predefined supplemental study, its behavior/robustness findings, and 14 evidence-bound human records. The September 22 decisions accept the five SQLi candidates only for the bounded tested injection repair while preserving `SQL-R01` failures, and request more testing for traversal 02–05 while preserving `PATH-S06` as inconclusive. The review also exposed and repaired a verifier portability bug: saved absolute paths from another checkout prevented verification here. The verifier now checks the registered source within the active checkout and still requires matching hashes. No saved experimental outcomes or frozen primary implementation were changed, and the original review records remain preserved.

## Explain the prototype accurately

FixProof is a Python orchestration and evaluation prototype. It evaluates repairs to small JavaScript/Node.js Express applications. Its dashboard uses HTML/CSS/JavaScript. The earlier discussion reply describing the whole prototype as mainly JavaScript should be clarified; Video II already makes the distinction correctly.

The repair model proposes code changes. The validation harness executes predefined checks and records observations; deterministic policy combines the evidence, and a person records review decisions. The model is not an independent judge of its own repair. Development assistance from Codex is distinct from the model calls used to generate experimental repair candidates.

Current evidence concerns deliberately vulnerable fixtures and AI-generated repairs. AI assistance in authoring a fixture does not establish evaluation on a representative corpus of AI-generated applications. Explain this narrowing of the original proposal explicitly; do not imply the professor has already approved it.

## Repository map and cleanup

| Location | Role / treatment |
| --- | --- |
| `src/fixproof/` | Python implementation: agent, scanners, findings, patches, validation, evaluation, reproduction. 34 tracked Python files including package initializers. |
| `tests/` | 22 Python test modules plus registered supplemental case definitions; 116 current tests. |
| `benchmarks/primary/v1/` | Frozen three-CWE application inputs and study definition. Preserve. |
| `sample_apps/`, `workspaces/` | Pilot examples and saved candidate source. Keep tracked evidence; the Python smoke test is not Python repair support. |
| `data/primary_trials/`, `data/primary_reviews/` | Primary experiment and original human review evidence. Preserve. |
| `data/supplemental/v1/` | Protocol lock, execution records, reports, and follow-up reviews. Preserve. |
| `data/lifecycle/` | Separate version-history demonstration. Its reopened example is recorded-evidence replay. |
| `ui/` | Evidence inspection; primary and pilot views. Current primary view does not summarize all supplemental follow-ups. |
| `docs/` | Active guides, frozen protocols, dated course drafts/history. Clearly distinguish them. |
| `scripts/` | Packaging and verification helpers. Add explicit supplemental verification to the final delivery checklist. |
| `.venv/`, `node_modules/`, caches, `dist/`, local `.env` | Local dependencies, generated material, and configuration; exclude from the source submission. |

No bulk removal or restructuring is necessary. Old drafts and pilot artifacts are provenance, not automatically junk. Keep submitted Report 2 and Video II as historical checkpoints. Update active navigation and status instead. The frozen supplemental protocol's zero-executions statement describes its freeze time; do not edit a locked document to reflect later execution.

## Alignment with feedback and course requirements

| Concern | Current response | Remaining action / limitation |
| --- | --- | --- |
| Professor: concrete scope and application construction | Three controlled Express fixtures: XSS, SQL injection, traversal; frozen inputs, five initial repair attempts per CWE | Describe fixture construction, ground truth, original attack behavior, and why these classes were chosen |
| Professor: what the AI agent does | Generates repair candidates; separate executable validation and deterministic policy | Include a diagram and one saved prompt-to-patch-to-evidence example; distinguish development AI from experimental AI |
| Professor: systematic choices and evaluation | Frozen primary protocol, preserved artifacts, registered supplemental oracles, explicit denominators | Compare alternatives and justify choices; five attempts per class support descriptive observations, not broad reliability estimates |
| Raymond: code/language and adequate functional testing | Python tool, JS applications; supplemental tests found behavior omissions in the original suite | Explain test coverage limits and absence of production-scale/performance evaluation |
| Kiang: repetitions, measurement, conclusions | 15 initial attempts; category-specific supplemental observations | State that repeated repairs of one fixture are not independent application diversity; avoid pooling 140 observations into a security success rate |
| Cheick: new flaws and changed behavior | Rescan, runtime security, functional checks, supplemental parity failures | Zero newly observed SAST findings does not prove no new vulnerability; demonstrate an actual behavior failure |
| Aluor: deliverables, failure testing, before/after attacks | Prototype, evidence, reports, lifecycle, baseline/candidate checks | Show a release/deliverable list; optionally add a small separately documented API-failure test set, not all OWASP categories |
| Syllabus p. 1 and pp. 8–9: design, implementation, evaluation, final limitations | Working prototype and measured primary/supplemental results | Turn these into a methods/results draft now, with explicit limits and final deliverable plan |
| Syllabus p. 6: responsible, disclosed AI use | Existing AI assistance descriptions and stored experimental prompts | Cite actual tools/prompts and verify generated claims; finalize disclosure rather than carry forward draft disclaimers |
| Syllabus p. 3: expected effort and assessment | Meaningful implementation/evaluation progress | Record actual reporting dates and hours; do not infer hours from tests, commits, or elapsed days |

The supplied Report 2 references provide a useful starting set. More citations alone will not answer the professor's criticism. Extend `docs/related-work.md` with a source-checked comparison of benchmark size/type, repair model, validation oracle, retries, success definition, and limitations. Separate research evidence from Semgrep/OWASP/CWE implementation or terminology references. Correct generic/duplicated CWE reference labels in the next report. This audit did not newly verify the research papers or the shared webinar; do not cite that webinar as something already reviewed.

## Next work before October 4

1. **Report every supplemental limitation.** Traversal 03 and 05 miss new robustness rules, and all SQLi candidates miss the new repeated-parameter rule. Distinguish new contracts from behavior-preservation requirements. The five SQLi primary statuses remain historical ready-for-review states; the September 22 bounded acceptances are separate human records and do not turn `SQL-R01` into a pass.
2. **Write methods/results and strengthen related work.** Explain three fixtures, five attempts each, independent validation, primary/supplemental separation, and human decisions. Include alternative choices and limits. Do not claim zero primary false successes proves the pipeline prevents all false confidence. Use the completed Report 3 draft as the current writing base.
3. **Handle the symlink gap explicitly.** Windows denied fixture creation, leaving five security observations inconclusive. Either retain this limitation or conduct a separately dated run in a suitable environment. Never turn an unexecuted case into a pass.
4. **Rehearse Video III and delivery.** Show the primary dashboard, a candidate diff, separate validation observations, and the supplemental evidence/review. A read-only supplemental summary/link would help navigation; a write-enabled approval UI is unnecessary. Run supplemental verification explicitly in addition to the main command before packaging.

Optional bounded engineering work: inject API timeout/rate-limit/malformed-response failures using mocks and document the observed safe failure behavior. Existing scanner/integrity tests are not evidence of a completed API stress campaign. Performance/load testing and additional CWEs are future work unless they directly serve a new, predefined research question.

### Demo rehearsal

```powershell
.\.venv\Scripts\python.exe -m fixproof.reproduce --verify
.\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_report --check
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

Open `http://127.0.0.1:8080/ui/primary.html`. Explain that this view inspects saved evidence. For a live runtime replay, follow `docs/demo-guide.md` and label it a replay of saved candidates rather than new model generation. Do not fabricate a new reviewer decision for a demonstration.

Use XSS 03 versus 04 to show both pass registered supplemental security cases but differ on missing-input behavior. Explain that preserving `Hello undefined` is the frozen parity criterion, not a claim that this is ideal product UX. Traversal 01 provides a second, more intuitive example: a fix rejects a legitimate in-root file named `..notes.txt`. Show its saved follow-up rejection. Neither example should be relabeled as a primary SAST false success.

## Course calendar and completion plan

Dates below come from the supplied Canvas listing, not from an assumption that everything is due in late November. Confirm any later Canvas changes.

| Deadline | Deliverable / focus |
| --- | --- |
| September 22 / 27 | Video II posting / peer feedback; Tony confirms the video is posted and feedback is in progress, not yet complete |
| October 4 | Report 3: supplemental findings, follow-up outcomes, limitations, next tasks, actual hours |
| October 6 / 11 | Video III / peer feedback: demonstrate evidence omitted by the original suite |
| October 18; October 20 / 25 | Report 4; Video IV / feedback: research comparison, reproducibility, refined interpretation |
| November 1; November 3 / 8 | Report 5; Video V / feedback: final evaluation and paper outline, delivery rehearsal |
| **November 15** | **Final presentation video, no more than 15 minutes** |
| November 22 | Final presentation peer feedback |
| **December 6** | **Final project report** |

Finish the core interpretation and Report 3 by October 4; use October for the paper and reproducibility, and have a presentation draft ready early November. The syllabus weights progress reports 25%, peer feedback 25%, presentation 20%, and final report 30%. Blank or N/A grades in the pasted listing do not establish scores. Working software alone does not complete the course.

## Sources and audit boundaries

Local sources read: `CS6727 Cyber Security Practicum Course Syllabus Fall 2026_2.pdf` (nine pages), `Progress Report 2 (Tony Tran) - Updated Draft (1).docx`, and `FixProof - Video II - 09132026.pptx` (seven slides and notes), under the supplied OneDrive Documents directory; the seven supplied attachment text files; and the user's pasted proposal, feedback, and schedule. Several attachment pairs are duplicates and are not independent corroboration. Source hashes and a follow-up audit are retained locally in `dist/review-2026-09-21/`.

This review does not verify Canvas receipts, grades, unrecorded personal work hours, independent reviewer agreement, production readiness, or professor acceptance of the narrowed scope. Use the adjacent [Report 3 writing starter](Progress-Report-3-writing-starter.md) to turn verified progress into the required template.
