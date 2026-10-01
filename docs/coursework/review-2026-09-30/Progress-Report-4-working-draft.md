# Section: CS OCY, OC1

# FixProof: A Validation-Oriented System for AI-Generated Vulnerability Remediation

Tony Tran  
Progress Report 4 - Working Draft, October 1, 2026

Draft status: This is an early Report 4 checkpoint prepared after Progress Report 3 and Video III were posted. It records completed work through October 1, including the separately versioned PATH-S06 extension, five later human qualifications, and a student-facing request/response evidence report. Peer feedback, the broader clean-package audit, the live deployment of the October 1 public package, and the final effort total are not yet complete and are identified as planned work.

## Problem Statement:

AI coding tools can produce insecure code, while a proposed security repair can
leave a weakness exploitable or change intended application behavior.
Disappearance of a static-analysis warning alone is incomplete evidence of a
correct repair. Pearce et al. (2022) found approximately 40% of 1,689
Copilot-generated programs vulnerable within their selected security scenarios.
Existing work also studies LLM vulnerability repair and validation feedback
(Pearce et al., 2023; Kulsum et al., 2024). FixProof asks whether separately
recorded static, runtime-security, functional, policy, and human-review evidence
can reveal failed or behavior-changing patches that a SAST-only decision could
classify as successful.

The evaluated scope remains deliberately narrow: three purpose-built
JavaScript/Express applications with reflected XSS (CWE-79), SQL injection
(CWE-89), and path traversal (CWE-22). FixProof evaluates repeated AI-generated
repairs to these fixtures, not a representative corpus of applications or
production repositories. The 15 scheduled model calls are five repairs per
fixture, not 15 independent applications and not a production repair-success
estimate.

The project translates beyond the benchmark through its evidence structure,
not through the observed 5/15 SAST-resolution or 15/15 primary-suite values.
For another repository, FixProof would need repository-specific build and start
commands, scanner configuration, a target-finding mapping, security and benign
behavior oracles, and a documented human-review criterion. The transferable
part is the separation and preservation of these evidence channels and the rule
that the repair model cannot approve its own candidate.

## Solution Statement:

FixProof uses Python to orchestrate Semgrep CE scanning, finding normalization,
focused remediation prompts, candidate application in a copied workspace,
JavaScript syntax checks, SAST comparison, targeted security tests, and
functional tests. Deterministic policy routes each candidate to REJECT,
READY_FOR_HUMAN_REVIEW, or NEEDS_HUMAN_ADJUDICATION. The model receives a
frozen finding and focused source context and proposes code, but it cannot run
the scanner, application, browser, or tests and cannot approve or deploy the
candidate. Human conclusions remain separate records.

The design choices are deliberate. Minimal fixtures provide reproducible
vulnerability ground truth and benign-behavior expectations within the course
timeline, at the cost of production realism. A fixed model, prompt template,
tool setting, and five-call schedule hold generation conditions constant while
showing within-fixture variation. They do not provide independent application
samples or a model-to-model comparison. Semgrep provides a preserved static
signal, while targeted runtime and functional checks measure exploit behavior
and intended behavior separately. Copied workspaces preserve study inputs but
are not security sandboxes. Deterministic policy makes evidence handling
repeatable, and human review remains outside model authority.

Deliverables include the prototype, three versioned CWE fixtures, frozen
primary-v1 evidence, separately registered supplemental-v1 evidence, original
and later human records, a dashboard and CLI demonstration, reproducibility
documentation, the sanitized public evidence reference, course videos, and the
final report and presentation. The public website displays saved, sanitized
evidence; it performs no model calls, scans, application execution, approval,
or deployment.

## Completed Tasks (Since Progress Report 3):

- Submitted Progress Report 3 on September 28, ahead of its October 4 course
  deadline. The submitted report preserved primary and supplemental
  denominators, separated original reviews from later qualifications, and
  directly addressed the professor's concern about translating a small
  benchmark to the stated problem.
- Finalized and revalidated the nine-slide Video III deck and narration. The
  scope slide now explains the three fixtures, controlled model setup, and
  separated roles in plain language. The deck states that five calls per
  fixture means 15 repeated repairs of three applications, not 15 independent
  applications.
- Corrected the workflow figure so the policy paths are unambiguous: all
  automated outcomes enter the primary record; selected cases branch to human
  review; the verdict and rationale return to the record; and primary evidence
  plus later supplemental outcomes inform a separate follow-up without
  rewriting primary-v1.
- Rechecked the saved evidence on September 30. Primary verification reports
  15/15 initial attempts and 10/10 original conflict reviews complete.
  Supplemental verification reports three baselines and 15 saved candidates.
  The follow-up verifier reports 14/14 later human records complete.
- Posted Video III by September 30 and shared the sanitized evidence reference
  at https://fixproof.netlify.app/. The deployed reference presents 15
  candidate records, the primary and supplemental summaries, preserved human
  decisions, patch excerpts, the workflow diagram, and the PDF appendix. It is
  a read-only presentation layer rather than a test runner.
- Froze and executed `path-s06-extension-v1` in WSL2 to resolve the one
  environment-blocked supplemental security case. The extension reused the
  vulnerable baseline and five saved traversal candidates, made no model calls,
  and did not rerun SAST. The baseline disclosed the controlled outside-file
  marker through the in-root link. All five candidates also returned HTTP 200
  and disclosed the marker, yielding zero pass, five fail, and zero
  inconclusive candidate observations under the frozen rule.
- Preserved all experimental boundaries. Before/after tree fingerprints show
  that primary-v1 and supplemental-v1 were unchanged. The five original
  `PATH-S06` inconclusive observations remain part of supplemental-v1; the new
  outcomes are recorded only under `data/extensions/path-s06-v1/`.
- Ran the complete test suite from a clean local clone after adding the
  extension and human-record verifier. All 131 tests passed. This avoids false copy errors from open
  Office lock files while leaving the user's working documents untouched.
- Personally reviewed the frozen PATH-S06 protocol, baseline gate, run summary,
  and all five candidate records. I manually reproduced Traversal 02 in WSL2:
  normal file access returned HTTP 200, direct `../../` traversal returned HTTP
  400, and the in-root symlink request returned HTTP 200 with the controlled
  outside marker. I recorded five separate extension qualifications as
  `FOLLOW_UP_REJECT_CANDIDATE`. Traversal 01's rejection is reaffirmed;
  Traversal 02-05's earlier request-more-testing records remain preserved.
- Regenerated and browser-validated the sanitized public-reference source with
  a separate PATH-S06 extension layer. It retains the 140 supplemental-v1
  observations and 14 supplemental-v1 human records while adding five
  extension failures and five extension human qualifications. I also rebuilt
  the 15-candidate PDF appendix with all five extension rationales.
- Built and validated a student-facing case-evidence report so the summary
  counts can be traced to individual payloads and outcomes. The Excel workbook
  contains seven worksheets: a guide, the 15-candidate summary, 100 primary
  runtime cases, 140 supplemental-v1 cases, five separate PATH-S06 extension
  cases, count reconciliation, and 29 human-decision records. Each case row
  includes the recorded input or payload, effective request, expected
  contract, HTTP status, response or browser output, result, evaluation reason,
  and repository evidence path.
- Added a paginated and filterable request/response page to the sanitized
  public-reference source. Browser validation confirmed 15 candidate rows,
  245 case-evidence rows across the three preserved layers, and 29 human
  records. The public export omits transient loopback ports, local-user paths,
  OpenAI response identifiers, and credentials. The October 1 Netlify package is ready,
  but the deployed site must not be described as updated until that package is
  uploaded and checked live.

Effort checkpoint: Personal hours since the September 28 Report 3 submission
have not yet been reconciled. Before the October 18 submission, replace this
sentence with actual dates, activities, and hours from the personal work log.
Do not automatically extend the earlier 1.5-hours-per-day estimate unless it
matches the time actually worked.

## Remaining Work Before Progress Report 4 Submission:

- Retain the Video III submission receipt and complete Peer Feedback Report III
  by October 11. Summarize substantive feedback with a disposition of adopt,
  defer, or decline and a short reason. Peer comments inform project choices;
  they are not experimental observations.
- Report the completed extension separately. Do not add its five candidate outcomes to
  the 140 supplemental-v1 observations or replace those five original
  inconclusive outcomes. Disclose that Python 3.12.3 orchestrated the extension
  while the native application runtime matched the recorded Node.js 24.19.0
  and npm 11.17.0 versions.
- Audit the existing control and failure-handling evidence: structured model
  response validation, canonical-finding identity checking, startup and request
  timeouts, recorded infrastructure failures, and the deterministic non-AI
  false-success control. Keep that control outside the 15 AI-attempt
  denominator.
- Perform a clean-package reproducibility rehearsal. Verify primary evidence,
  supplemental evidence, all human-record bindings, the public-reference
  export, and the documented commands from a clean copy that excludes local
  environments, caches, credentials, and disposable logs.
- Upload the versioned October 1 Netlify package and validate the live test
  evidence page, filters, workbook download, appendix, and privacy boundary.
  Keep the September 30 package as a superseded local artifact.
- Reconcile actual hours, update this draft with received feedback and any new
  separately versioned results, inspect the rendered DOCX/PDF, confirm the live
  Canvas instructions, and submit Progress Report 4 by October 18 at 11:59 p.m.

## Tasks for the Next Project Report:

- Incorporate applicable Video III feedback and the completed Report 4 scope
  decision into the methods, limitations, and future-work sections.
- Post Video IV and complete its peer-feedback assignment according to the live
  Canvas schedule.
- Expand the source-checked related-work comparison across benchmark type,
  repair input, validation oracle, retry policy, success definition, and
  limitations. Keep research papers distinct from OWASP, CWE, and Semgrep
  technical references.
- Continue the final report using separate sections for primary-v1, pilot and
  non-AI controls, supplemental-v1, any later extension, and human review.
- Prepare a versioned release candidate and repeat the clean reproduction
  procedure before Progress Report 5.

## Questions I Have or Issues I Am Running Into:

The Windows execution gap for PATH-S06 is now closed by a separate WSL2
extension. Its vulnerable baseline and all five saved candidates returned the
controlled outside-file marker through the in-root symbolic link. This confirms
that a lexical `path.resolve` containment check did not establish containment
of the filesystem target followed by `fs.readFile`. The original Windows
outcomes remain inconclusive in supplemental-v1; the new extension is later,
separately versioned evidence.

The design must also avoid overstating the small benchmark. One fixture per
CWE, repeated calls, one distinct SQLi candidate source, targeted tests, and
same-host verification restrict generalization. Completing PATH-S06 closed a
known security uncertainty but did not add application diversity. A second
fixture would improve breadth but require new ground truth, oracles, and a
separate frozen protocol. Video III feedback will inform whether that breadth
belongs in this course project or future work.

Feedback requested: Does the separation between the frozen supplemental-v1
outcome and the later PATH-S06 extension make the change in evidence easy to
follow? For the remaining course work, would a clean reproduction by another
student or a second fixture add more useful confidence, and what evidence would
you expect from that step?

## Methodology Paragraph Summary:

Each controlled fixture defines an attacker-controlled input, target route,
vulnerable operation, synthetic data, baseline attack behavior, and
benign-behavior expectations. The frozen primary protocol uses five separate
initial repair calls per CWE. It holds the generator (gpt-5.2), prompt template
(1.0), and model tool access (none) constant while withholding evaluator ground
truth and test implementations from the repair prompt. The same saved
candidates receive syntax, Semgrep, targeted HTTP/browser security, and
functional checks. SAST-only interpretation and deterministic multistage policy
are compared on those same candidates. Primary attempts, pilot retries, the
non-AI false-success control, lifecycle replay, and supplemental tests retain
separate denominators.

Default Semgrep CE auto did not identify the SQL-injection target. Primary-v1
preserved that default miss and used a labeled, benchmark-focused
fixproof_controlled taint rule for repeatable before-and-after target
comparison. SQLi ground truth remained independent of SAST and was established
through the demonstrated runtime exploit. The five SQLi calls returned
identical candidate source; this duplication is reported as an observed model
outcome rather than five unique implementations.

Supplemental-v1 was fixed before candidate execution and compares each saved
candidate with its baseline using separate security, behavioral-parity, and
robustness oracles. It made no new model calls and did not rerun primary SAST.
Inconclusive execution is not a pass. Later human decisions qualify the result
without changing registered outcomes, original reviews, or primary metrics.
OWASP WSTG and Semgrep's run-rules documentation serve as technical references
for runtime-test organization and scanner configuration.

Pearce et al. (2022) motivate treating generated code as untrusted. Pearce et
al. (2023) examine zero-shot vulnerability repair and functional-correctness
challenges. Kulsum et al. (2024) study repair with external compiler,
sanitizer, and test feedback. FixProof does not claim that validation feedback
is new. Its bounded contribution is the auditable combination of separately
preserved static, runtime-security, functional, policy, and human evidence for
three Express weaknesses. Different datasets and success definitions prevent
direct comparison of success rates.

## Timeline:

| When | Description of Task | Status |
| --- | --- | --- |
| September 28 | Submit Progress Report 3; official deadline October 4 | Completed |
| September 29 | Finalize and validate Video III deck, script, workflow, and Q&A backup | Completed |
| By September 30 | Post Video III and share the sanitized evidence reference | Completed |
| October 1-11 | Collect Video III feedback and complete Peer Feedback Report III | In progress / planned |
| September 30 | Freeze and execute the separate PATH-S06 extension in WSL2; preserve primary-v1 and supplemental-v1 | Completed |
| September 30 | Personally review PATH-S06 evidence, reproduce Traversal 02, and record five separate later qualifications | Completed |
| October 1 | Build and validate the student evidence workbook, CSV tables, count reconciliation, and public request/response page | Completed |
| October 1-11 | Upload and live-validate the October 1 Netlify package | Planned |
| October 8-15 | Audit control and failure-handling evidence and complete the clean reproduction rehearsal | Planned |
| October 15-17 | Reconcile hours, update limitations and references, render and inspect Report 4 | Planned |
| October 18 | Confirm Canvas instructions and submit Progress Report 4 by 11:59 p.m. | Planned |
| October 20 / 25 | Post Video IV and complete Peer Feedback Report IV | Planned; confirm live Canvas |
| November 1 / 3 / 8 | Progress Report 5, Video V, and peer feedback | Planned; confirm live Canvas |
| November 15 | Submit final presentation video, no more than 15 minutes | Planned |
| November 22 | Submit peer feedback on final presentation | Planned |
| December 6 | Submit final project report and reproducible package | Planned |

## Evaluation:

The frozen experimental evidence remains unchanged through October 1. The
student-facing workbook and public table are read-only views of existing
records; they did not execute new candidate tests or alter any outcome. All 15
frozen primary initial attempts have complete evidence. The denominator excludes pilot
retries and the deterministic non-AI control. Original human conflict reviews
are 10/10 complete: seven acceptances under the original evidence and three
requests for more testing. Later decisions are recorded separately.

| Primary case | Initial attempts | Target SAST resolved | Security pass | Functional pass | Automated decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Reflected XSS | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| SQL injection | 5 | 5/5 | 5/5 | 5/5 | 5 ready for review |
| Path traversal | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| Total | 15 | 5/15 | 15/15 | 15/15 | 5 ready for review; 10 need adjudication |

Security and functional columns count candidates whose entire frozen primary
suite passed; they do not count individual cases. Target-SAST resolution was
5/15 (33.3%), and SAST/runtime disagreement was 10/15 (66.7%). The XSS and
traversal findings remained for all ten candidates even though their registered
primary runtime suites passed. These are evidence disagreements, not proof that
the findings are false positives or that the patches are fully secure. No
primary SAST false success was observed; a separate labeled non-AI control
exercises that policy branch without entering AI-attempt metrics.

The primary candidate table above counts candidates whose complete suite
passed. The case-evidence report additionally exposes the underlying individual
runtime observations:

| Evidence layer | Category | Observations | Pass | Fail | Inconclusive |
| --- | --- | ---: | ---: | ---: | ---: |
| Primary-v1 | Security | 40 | 40 | 0 | 0 |
| Primary-v1 | Functional | 60 | 60 | 0 | 0 |
| Supplemental-v1 | Security | 60 | 55 | 0 | 5 |
| Supplemental-v1 | Behavioral parity | 45 | 40 | 5 | 0 |
| Supplemental-v1 | Robustness | 35 | 25 | 10 | 0 |
| PATH-S06 extension-v1 | Security | 5 | 0 | 5 | 0 |

These denominators remain separate. In particular, the 100 primary
observations, 140 supplemental-v1 observations, and five extension observations
must not be pooled into one security or production-success rate.

| Supplemental category | Observations | Pass | Fail | Inconclusive | Meaning |
| --- | ---: | ---: | ---: | ---: | --- |
| Security | 60 | 55 | 0 | 5 | PATH-S06 could not create its Windows symlink fixture for five traversal candidates |
| Behavioral parity | 45 | 40 | 5 | 0 | Four XSS missing-input changes and one traversal valid-file rejection |
| Robustness | 35 | 25 | 10 | 0 | New SQLi and traversal ambiguous/malformed-input contracts |
| Total | 140 | 120 | 15 | 5 | Mixed categories; not one security success rate |

The supplement evaluated the same 15 saved candidates after baseline
characterization. XSS 03 passed all nine registered supplemental cases. XSS 01,
02, 04, and 05 passed their three registered security cases but failed the
frozen XSS-P01 missing-input parity case; later records reject those four
candidates under exact parity. The rejections do not mean the registered XSS
attacks remained exploitable.

All five SQLi candidates passed three supplemental injection-security and two
behavioral-parity cases and returned no unauthorized rows. SQL-R01 still
failed because repeated username parameters returned HTTP 200 with an empty
array rather than the registered HTTP 400 response. The five later acceptances
are bounded to the tested injection repair and preserve this disclosed
robustness failure.

Every traversal candidate passed the five executable supplemental security
cases, but PATH-S06 remained inconclusive in supplemental-v1. Traversal 01 also
failed one parity and one robustness case and was later rejected. Traversal
02-05 received later requests for more testing; traversal 03 retains three
robustness failures and traversal 05 retains the repeated-parameter failure.
There are 14 supplemental-v1 later human records in total: five rejections,
five bounded SQLi acceptances, and four requests for more testing. No later
record overwrites a primary result.

The separately frozen `path-s06-extension-v1` then executed that one security
case in WSL2. The vulnerable baseline returned HTTP 200 and the controlled
outside marker, establishing the control. Each of the five saved traversal
candidates also returned HTTP 200 and disclosed the marker. The extension
therefore records zero pass, five fail, and zero inconclusive candidate
outcomes. These are conclusive security disclosures, not merely failures to
return a preferred status code. Tony recorded five separate
`FOLLOW_UP_REJECT_CANDIDATE` qualifications after reviewing the evidence and
manually reproducing Traversal 02. These records do not alter the original
primary or supplemental-v1 decisions.

| Report 4 extension status | Current state on October 1 |
| --- | --- |
| Video III feedback | Video posted; feedback collection and disposition summary pending |
| PATH-S06 separate extension | Complete and verified: baseline gate passed; 0/5 candidate pass, 5/5 fail, 0 inconclusive |
| PATH-S06 human qualification | 5/5 complete: Traversal 01 reaffirmed; Traversal 02-05 later rejected; original records preserved |
| Second fixture | Not selected or executed |
| Primary-v1 metrics | Frozen and unchanged |
| Supplemental-v1 metrics | Frozen and unchanged |
| Clean test-suite rehearsal | 131/131 tests passed from a clean local clone |
| Broader clean-package audit | Documented commands and release exclusions still planned; public export validation complete |
| Student evidence report | Complete: 15 candidate rows; 100 primary, 140 supplemental-v1, and 5 extension case rows; 29 human records |
| Updated public-reference source | Local browser validation passed; October 1 Netlify deployment and live check remain pending |

## Report Outline:

1. Problem, motivation, and bounded research question.
2. Related work, alternatives, and specific contribution.
3. Controlled scope, threat model, and benchmark construction.
4. Architecture, model authority, validators, deterministic policy, and human boundary.
5. Frozen primary method, comparator, provenance, and reproducibility.
6. Primary results, separate pilot/control examples, and original human reviews.
7. Supplemental methods and results, later human qualifications, and any separately versioned extension.
8. Generalization boundary, limitations, deployment feasibility, and lessons from peer feedback.
9. Conclusion, references, evidence index, and AI-use disclosure.

## References:

Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2022). Asleep at
the keyboard? Assessing the security of GitHub Copilot's code contributions.
2022 IEEE Symposium on Security and Privacy.
https://doi.org/10.1109/SP46214.2022.9833571

Pearce, H., Tan, B., Ahmad, B., Karri, R., & Dolan-Gavitt, B. (2023). Examining
zero-shot vulnerability repair with large language models. 2023 IEEE Symposium
on Security and Privacy. https://doi.org/10.1109/SP46215.2023.10179324

Kulsum, U., Zhu, H., Xu, B., & d'Amorim, M. (2024). A case study of LLM for
automated vulnerability repair: Assessing impact of reasoning and patch
validation feedback. Proceedings of the 1st ACM International Conference on
AI-Powered Software. https://doi.org/10.1145/3664646.3664770

OWASP Foundation. (n.d.). Web Security Testing Guide, version 4.2.
https://wstg.owasp.org/v4.2/

Semgrep. (n.d.). Run rules. https://semgrep.dev/docs/running-rules

## Appendix:

Evidence index: docs/study-protocol-v1.md and benchmarks/primary/v1/ define the
frozen primary study. data/primary_trials/v1/, data/primary_reviews/v1/, and
data/evaluation/primary-report.json preserve candidate, automated, and original
human evidence. docs/supplemental-protocol-v1.md,
tests/supplemental/v1/cases.json, data/supplemental/v1/, and
docs/supplemental-results-v1.md preserve the supplemental protocol, cases,
observations, and 14 later records. fixproof-public/ contains the sanitized
static reference deployed at https://fixproof.netlify.app/. The Video III deck,
script, render, validation record, and Report 4 plan are under
docs/coursework/review-2026-09-29/.

The separate PATH-S06 extension is defined by
`docs/path-s06-extension-v1-protocol.md`, hash-locked in
`data/extensions/path-s06-v1/protocol-lock.json`, and summarized in
`docs/path-s06-extension-v1-results.md`. Its evidence is under
`data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/` and is
not included in supplemental-v1's 140-observation denominator.
The updated printable appendix includes the five extension results and complete
extension rationales. `fixproof-public/` now contains the validated static
source; deployment of that updated source remains a separate publishing step.

The student evidence report is under
docs/coursework/review-2026-10-01/. Its Excel workbook and CSV tables expose the
individual requests, outputs, and evaluation reasons behind the candidate
matrices. FixProof-student-evidence-validation.json records source and output
hashes plus the reconciled counts. The sanitized public files include the test
evidence page, its selected public JSON, and the downloadable workbook. The
versioned October 1 Netlify ZIP is the next deployment package.

Verification checkpoint, September 30: primary evidence verified 15/15 initial
attempts and 10/10 original reviews; supplemental evidence verified three
baselines and 15 saved candidates; supplemental human records verified 14/14
complete. The deployed public JSON reported 15 candidates, 140 supplemental
candidate-case observations, and 14 later human records. These checks verify
saved evidence and bindings; they do not rerun model calls or turn targeted
tests into a production-security claim.

PATH-S06 extension checkpoint, September 30: the frozen protocol and result
hashes verified; the candidate matrix recomputed as zero pass, five fail, and
zero inconclusive; before/after fingerprints confirmed that primary-v1 and
supplemental-v1 did not change.

Human qualification checkpoint, September 30: five extension packets and five
results verified. Each result binds the approved rationale, registered
candidate outcome, and preserved prior follow-up. Only Traversal 02 is labeled
as manually reproduced.

Student evidence checkpoint, October 1: workbook integrity and all exported
counts verified; public browser checks passed for pagination, candidate,
layer, result, and case search filters; and the full FixProof unit-test suite
passed 131/131 tests. These checks validate the reporting layer but do not
convert the bounded benchmark into a production-security claim.

Generative AI disclosure: OpenAI ChatGPT/Codex assisted planning,
implementation, debugging, test orchestration, documentation, evidence
organization, presentation preparation, and drafting. FixProof separately used
saved OpenAI API calls to generate the primary repair candidates. Tony Tran
remains responsible for verifying claims and references, reporting actual
effort, making human-review decisions, approving any new test plan, and
approving the submitted text.
