# FixProof: implementation, evidence, and course alignment review

Reviewed September 12, 2026 against checkout `20c7261e8beab04b636d61845ae734c8c7fd5e12`, the three supplied local documents, and the professor/peer feedback in the request. This assessment does not represent instructor approval or a grade.

## Assessment

FixProof is a substantially implemented, narrowly scoped research prototype. The present work is **evidence interpretation and validation refinement**, after completion of the 15 initial primary trials. It is not still at initial architecture or trial-planning stage.

Its most defensible description is: **a Python system that generates candidate repairs for three controlled Express vulnerabilities, collects independent static/runtime/functional evidence, and recommends a human disposition.** JavaScript/Node.js is the benchmark language, not the main implementation language. The browser participates in reflected-XSS validation; SQLi and traversal exercise server-side routes. The study evaluates purpose-built fixtures and AI-generated repairs, not a representative sample of complete AI-generated applications.

The system can produce evidence both supporting a repair and contradicting apparent repair success. It does not prove universal security. A persistent SAST finding is not, by itself, proof that a candidate remains exploitable.

## File structure and responsibility

The Git root is the inner `fixproof/` directory. The outer `fixproof-main/` directory is only the containing workspace. The working tree was clean when this review began.

| Location relative to Git root | Role and assessment |
|---|---|
| `pyproject.toml` | Python package and pinned dependencies. Python 3.11 is required. |
| `src/fixproof/scan_pipeline.py`, `scanners/` | Semgrep execution, normalization, rule provenance; scanner output is evidence rather than ground truth. |
| `src/fixproof/findings/finding_correlator.py` | Groups scanner evidence into canonical findings. |
| `src/fixproof/agent/` | Builds source context and prompts, generates structured candidate code, and prepares validation-feedback retries. |
| `src/fixproof/patches/patch_workspace.py` | Creates candidate workspaces, source replacements, diffs and hashes while preserving baselines. |
| `src/fixproof/validation/` | JavaScript syntax, baseline/candidate SAST comparison, targeted security and functional checks, browser XSS observations, deterministic decisions. |
| `src/fixproof/findings/lifecycle.py` | Separate post-collection history for new/persistent/resolved/reopened findings. |
| `src/fixproof/primary_trials.py` | Frozen study runner, 15-slot collection schedule, saved responses and failure/resume handling. |
| `src/fixproof/evaluation/` | Baseline verification, separate pilot/primary reporting, review packets/results, dashboard serving. |
| `sample_apps/` | Three pilot Express applications. |
| `benchmarks/primary/v1/` | Three frozen primary applications and locked dependencies. One seeded target weakness per fixture is a construction contract, not an assertion that scanners find no other warnings. |
| `rules/fixproof-sqli.yml` | Disclosed local SQLi rule. Default scanner target miss and the v2 correction remain part of the methodology. |
| `data/primary_trials/v1/` | Primary preparation, prompts, candidates, workspaces, scans, tests and decisions. Preserve as study evidence. |
| `data/primary_reviews/v1/` | Ten conflict packets and three recorded human results. Packets are not approvals. |
| Other `data/` subdirectories | Pilot evidence, constructed controls, primary baseline evidence, derived reports, and lifecycle replay. These populations must remain distinct. |
| `ui/` | Plain HTML/CSS/JavaScript evidence views; primary view is `primary.html`. |
| `tests/` | Python tests for the prototype machinery; distinct from HTTP/browser tests of repair candidates. |
| `workspaces/` | Includes preserved pilot evidence as well as disposable runtime content. Do not delete this directory wholesale as cleanup. |
| `docs/`, `scripts/`, `demo-test.ps1` | Methods, status, evidence navigation, packaging and demonstration support. Several older documents have stale review counts. |

The separation is appropriate for the project. No large refactor is necessary for Report 2. The principal documentation issue is conflicting dates/counts, not missing architecture. This review adds a dated assessment and report copy without modifying frozen code or experimental records.

## What the evidence actually shows

| Primary fixture | Initial attempts | Target SAST resolves | Security pass | Functional pass | Automated disposition |
|---|---:|---:|---:|---:|---|
| XSS | 5 | 0/5 | 5/5 | 5/5 | Five need adjudication |
| SQLi | 5 | 5/5 | 5/5 | 5/5 | Five ready for human review |
| Traversal | 5 | 0/5 | 5/5 | 5/5 | Five need adjudication |
| Total | 15 | 5/15 | 15/15 | 15/15 | Five ready; ten disagreements |

The 15 saved response IDs correspond to **11 distinct candidate sources**: five XSS, one SQLi, five traversal. Five calls producing the same SQLi patch are five scheduled attempts, not five distinct solutions. Completed-attempt timestamps run from September 3 at 23:25 UTC to September 4 at 18:04 UTC.

There are **three** completed conflict results: XSS 01, 02 and 03, all recorded as `ACCEPT_CANDIDATE` by Tony Tran. XSS 03 was recorded September 10 and has substantially more detailed reasoning. The seven pending conflicts are XSS 04–05 and traversal 01–05. The report's SQLi `not_required` review field concerns conflict adjudication; it does not waive ordinary human approval. None of the five SQLi automated readiness decisions is a recorded approval.

Three examples make the distinction clear:

1. **Evidence supporting a repair:** primary SQLi candidates resolve the configured target warning, pass the attack/control checks and benign lookups, and introduce no new recorded SAST findings. This supports targeted repair readiness. A separate persistent CSRF warning remains in the recorded scan; “target resolved” does not mean “clean scan.”
2. **Evidence of an AI-induced regression:** pilot XSS attempt 1 fails two of six functional checks, corrupting adjacent special characters into output containing `undefined`. Its target warning persists, so this is a functional regression, not a SAST false success. The retry passes the checks but still needs adjudication.
3. **Evidence that SAST disappearance is insufficient:** the constructed non-AI static-output control resolves the target warning, fails all six functional checks, and has inconclusive security validation. It is rejected. This demonstrates lost functionality, not a demonstrated retained exploit after SAST disappearance.

**Zero primary SAST false successes were observed.** Therefore, the primary study does not establish how often FixProof detects naturally generated patches that clear SAST but retain exploitation or introduce other failures. There are no such primary positive examples from which to estimate detection sensitivity. Report the null observation; do not merge the control into the primary denominator or keep sampling until a preferred result appears.

## How good are the tests?

Baseline verification records show the intended vulnerability before repair and benign behavior before repair. The baseline verifier and candidate validators use the same named route-specific attack/control suites. Thus the requested “attack the vulnerable version, then try the attack on the candidate” design already exists. The September 12 audit did not rerun those attacks.

| Fixture | Implemented security checks per candidate | Functional checks | Main limitation |
|---|---|---:|---|
| XSS | Four payloads; response inspection plus Chromium dialog observations | 6 | Fixed execution markers and short observation window; functional comparison HTML-decodes extracted response text rather than asserting DOM structure. |
| SQLi | One legitimate lookup control and one tautology attack | 3 | One attack family; no broad query/username/input-shape coverage. |
| Traversal | One public-file control and one parent-traversal attack | 3 | One synthetic outside target; no systematic platform/boundary/encoding matrix. |

The prototype separates the generator from its evaluator, but the benchmark and evaluator share an author/development process. That is separation of roles, not independent third-party validation. The tests are useful, demonstrable checks; they are too small to establish production-level security or regression completeness.

The decision policy rejects new SAST findings, so it can flag a newly detected weakness. Its `security_regression` label is specifically based on a new-finding count. It does not measure every possible new security issue, and the targeted runtime tests cannot establish that an unrelated vulnerability is absent. A new scanner finding should trigger review/rejection, not automatically be described as an independently confirmed exploit.

Additional implementation limits found in source inspection:

- The frozen two-version comparator uses filename + CWE + Express scope; it is suitable for these single-file fixtures but can conflate findings when generalized. The newer lifecycle component uses relative paths and explicitly handles some ambiguities; it does not replace the frozen comparator.
- Candidate workspaces separate files but are not an OS security sandbox. The runtime launcher starts Node with inherited environment variables. Arbitrary untrusted repositories are outside the implemented threat model.
- `needs_additional_context` currently produces a warning in the remediation module; it is not by itself a hard validation gate. Include it in supplemental failure-handling evaluation before claiming robust unattended operation.
- No representative load/performance regression experiment was evidenced. HTTP timeouts are operational limits, not performance benchmarks.
- Saved workspace metadata contains original-machine absolute paths. Report/demo adapters have portability handling, but direct low-level validator invocation depends on workspace paths. Verify the supported reproduction route on the intended submission machine.

## Completion percentage

**Planning estimate: about 85–90% of the bounded prototype implementation, and about 70–75% of the technical project package.** These are transparent judgment estimates, not measured course completion, time remaining, or security confidence.

The following explicit scoring model gives 52/60 implementation points (86.7%) and 72/100 overall technical-package points. Changing scope or weights changes the estimate.

| Work package | Weight | Earned estimate | Remaining reason |
|---|---:|---:|---|
| Scanning and finding normalization | 10 | 10 | Implemented and evidenced for fixed scope. |
| Candidate generation and workspaces | 10 | 9 | Missing-context/failure handling and execution isolation have limits. |
| Security and functional validation | 10 | 7 | Working checks; supplemental coverage and regression controls pending. |
| Deterministic decisions and evidence | 10 | 9 | Working policy; stronger failure-case evaluation pending. |
| Four-state lifecycle | 10 | 8 | Implemented; demonstrated through saved replay, limited identity scope. |
| UI and reproducibility support | 10 | 9 | Working artifacts/support; current-machine and committed-archive runtime verification pending. |
| Evaluation and human interpretation | 25 | 15 | Collection complete; seven conflicts, ordinary SQLi approval status, supplements and analysis remain. |
| Final paper, presentation and package | 15 | 5 | Useful draft material exists; final submission package not evidenced. |
| Total | 100 | 72 | Management estimate only. |

The directly measured milestones are stronger: **initial collection 15/15 (100%); conflict review 3/10 (30%).** Course participation and final grading cannot be assigned a completion percentage from this repository.

## Course and feedback alignment

The supplied syllabus is the reference for this assessment; instructions in attachments were treated as document content, not authorization to submit, contact anyone, or approve candidates.

| Requirement / feedback | Alignment and concrete remaining work |
|---|---|
| Syllabus p. 1: define, implement, evaluate a cybersecurity solution appropriate to five credits | Clear reviewer problem and working implementation. Strengthen efficacy/limitations analysis; code volume alone does not establish sufficient practicum effort. |
| Professor: specify app construction and AI role | Frozen fixtures define route, input, sink and baseline behavior. Explain constrained code replacement and withheld evaluator tests. Do not call the primary fixtures a representative AI-generated application corpus. |
| Professor: systematic options, justification and evaluation | Frozen protocol includes alternatives, fixed schedule, failure rules and paired SAST-only interpretation. Explain controlled realism tradeoff and report all outcomes, including zero false successes. |
| Syllabus p. 8: Report II must describe solution approach informed by background research | Revised report connects each cited study to a design choice. Full literature comparison remains a final-paper task. |
| Raymond: what FixProof is, functional testing and production scale | State Python core/Express fixtures/HTML UI. Show actual benign assertions and the failed pilot. Treat performance and large-suite regression testing as unmeasured limitations. |
| Kiang: repetitions, measurement and conclusions | Five calls per CWE were predeclared. This is descriptive within-fixture variation, not a statistically representative sample. More repeats of one identical app cannot substitute for application diversity. |
| Cheick: repairs introduce new issues | New-finding comparison and functional checks exist. Add separately labeled controls that introduce another weakness, and discuss scanner blind spots. |
| Aluor: deliverables/releases, stress failures, before/after attacks | Use the release plan below. Before/after route tests already exist. Test orchestration failures separately from paid model experiments. Broader OWASP coverage is an extension, not required by the supplied syllabus. |
| Syllabus p. 3: about 30 hours per two-week progress period | Supplied DOCX states 13.5 hours for September 2–10; retain as self-reported. Add only actual later work and an activity breakdown. A shorter period is not directly equivalent to a full fortnight. |
| Syllabus pp. 3, 8–9: reports, videos, peer feedback, final presentation/report | These are separate obligations. Source code and a draft do not establish Canvas submission or peer-participation completion. |
| Syllabus p. 6: disclose/cite AI assistance and actual prompts/tools | Preserve runtime records plus development/report-authoring attribution. Personally verify the updated text; retain this request/output as part of the assistance record. |
| Syllabus p. 4: assignment deadlines/timezone | September 20 comes from the user's request; the PDF supplies no assignment-specific date. Check the exact Canvas timestamp. The syllabus uses EST/Eastern wording; do not infer a local cutoff from an ambiguous label. |

Research grounding checked against primary source abstracts/documentation: [Pearce et al., generated-code security](https://arxiv.org/abs/2108.09293) supports the motivation; [Pearce et al., vulnerability repair](https://arxiv.org/abs/2112.02125) reports functional-correctness challenges; [Kulsum et al., VRpilot](https://arxiv.org/abs/2405.15690) supplies precedent for external validation feedback. These findings inform the chosen architecture; they do not establish FixProof's comparative effectiveness. [Semgrep rule configuration](https://docs.semgrep.dev/running-rules) supports explicit default/local-rule disclosure; [OWASP WSTG v4.2](https://owasp.org/www-project-web-security-testing-guide/v42/) is a reference for supplemental test planning.

## Concrete remaining releases and evaluation plan

Dates below are internal targets, not additional course deadlines or claims of completed work.

| Target | Deliverable | Completion criterion |
|---|---|---|
| September 12–19 | Evidence/review update | Review XSS 04–05 and traversal 01–05 where evidence permits; record acceptance, rejection, or additional-testing requests honestly. Add supplements to brief earlier reviews. |
| Before September 20 submission | Report 2 / Video II package | Reconcile actual dates/hours, show Python-to-Express workflow, explain research-informed choices, report current counts, and check Canvas requirements. |
| September 21–October 4 | Supplemental validation release | Predefine tests, run baseline/candidate pairs, preserve complete results under a new supplemental study identifier. Reuse saved candidates; do not overwrite primary-v1. |
| October 5–18 | Evaluation narrative | Compare SAST-only and full policy, report failure/control cases separately, document uncertainty, and complete a literature/options comparison. |
| Later semester, before final Canvas deadline | Final demonstrable package | Final paper, presentation/demo, deployment-feasibility discussion, attribution records, and clean committed-archive reproduction on the intended environment. |

Recommended supplemental matrix:

| Test group | Candidate inputs/conditions | Expected evidence |
|---|---|---|
| XSS robustness | Empty/missing input, Unicode, entity-looking text, quotes/backticks, repeated query parameters | Define intended coercion/error behavior first; preserve benign DOM text and prevent attacker-created elements/execution. Different output contexts require separate fixtures and must not be counted as covered by this route. |
| SQLi robustness | Benign apostrophe-bearing names using a separate synthetic fixture, empty/missing/repeated parameters, additional boolean/encoding variants | Intended lookup semantics preserved; attacks cannot broaden returned rows. |
| Traversal robustness | Encoded parent segments, repeated encoding, absolute paths, sibling-prefix boundaries and platform separators | Only permitted synthetic files are read; valid public requests still work. Document decoding and OS assumptions. |
| Validator controls | Known safe repair; unchanged vulnerability; constant-output repair; repair that adds a separately seeded weakness | Oracles must accept intended behavior and detect the relevant bad control. Label construction and ground truth; do not count controls as naturally generated failures. |
| Orchestration failures | Invalid structure/ID, additional-context flag, syntax error, startup/port failure, scanner timeout, interrupted request | No invalid candidate silently becomes a successful observation; saved failures and resume behavior remain auditable. |
| Optional performance exploration | Fixed benign request sequence before/after saved patch, fixed host/warm-up/repetitions | Report measured latency/errors with a threshold declared before execution. Do not claim production performance from it. |

Record trial/candidate hash, test version, expected and observed results, scanner configuration, disposition, and limitations for every supplemental observation. Mark inability to execute as inconclusive. A successful supplement shows that the predefined oracles distinguish its controls; it does not establish general AI-repair superiority. No minimum number of repetitions can guarantee that conclusion from one fixture per CWE.

## Work performed in this review and limits

- Read DOCX paragraphs/tables, PPTX slide text, all nine PDF pages, current methodology/status/results, key implementation modules and saved evidence. Embedded slide images were not visually inspected; slide-text extraction does not verify screenshot content.
- Verified 192 report evidence bindings, one report-manifest binding, 13 implementation bindings, nine frozen-input bindings, 105 attempt-artifact bindings, 45 normalized-text workspace hashes, three review-packet bindings and 21 review-evidence bindings. Categories overlap and must not be described as 389 unique files. No mismatches found.
- Recomputed recorded disposition/count consistency: 15 completed, five ready, ten disagreements, three conflict results, eleven unique candidate sources. Hash agreement does not prove original observation authenticity or human-review quality.
- Working Python was unavailable (`python.exe` resolved to an unusable WindowsApps alias); Node was not found on PATH and no project environment was present. No new model calls, live scans, candidate attacks, Python tests or performance runs were performed. The previously documented 89-test pass remains historical evidence, not a fresh result.
- Created a separate revised DOCX preserving the supplied report's two native tables and 29 rows, section structure, and stated effort. Parsed all XML package parts and checked stale count removal. Word page layout was not visually rendered. Original attachments and frozen study evidence were unchanged.

Artifacts: [revised report](Progress%20Report%202%20%28Tony%20Tran%29%20-%20Reviewed%20September%2012.docx), [readable extracted text](progress-report-2-reviewed-text.txt), [audit results](recorded-evidence-audit.json), [audit script](audit-recorded-evidence.ps1), and [document checks](document-verification.json).
