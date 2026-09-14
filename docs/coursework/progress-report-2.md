# Historical September 10 Markdown draft

The supplied later DOCX includes Tony's effort statement, and the repository now
contains three conflict reviews. Use the [September 12 reviewed report and assessment](review-2026-09-12/FixProof-assessment.md)
for the current revision. The earlier draft below is preserved as history.

Section: CS OCY, OC1

# FixProof: A Validation-Oriented System for AI-Generated Vulnerability Remediation

Tony Tran

Progress Report 2 — evidence checked September 10, 2026

Draft: reporting dates and actual effort hours require confirmation from my personal work log before submission.

## Problem Statement:

AI coding tools can generate insecure code, and a proposed security repair can leave the vulnerability exploitable or change intended application behavior. Disappearance of a static-analysis warning therefore provides incomplete evidence of a correct repair. Pearce et al. (2021a) found approximately 40% of 1,689 Copilot-generated programs vulnerable in their selected security scenarios; this is evidence from that study, not a current universal vulnerability rate. Research on vulnerability repair and validation feedback already exists (Pearce et al., 2021b; Kulsum et al., 2024). FixProof investigates how separate validation evidence can support a human patch decision in a small, controlled JavaScript/Express setting, without claiming to be the first system to validate generated repairs.

## Solution Statement:

FixProof scans controlled Express applications with Semgrep CE, normalizes findings, and gives a remediation model one finding and focused source context. It applies the returned candidate to a copied workspace, then performs JavaScript syntax checks, SAST comparison, targeted security tests, and functional tests. Deterministic Python policy produces REJECT, READY_FOR_HUMAN_REVIEW, or NEEDS_HUMAN_ADJUDICATION. The remediation model neither grades its own patch nor records human approval. Deliverables are the prototype, three versioned CWE benchmarks, auditable evaluation artifacts, a dashboard and CLI demonstration, documentation, and the final report/presentation.

In response to the professor's scope feedback, the evaluated applications are deliberately constructed fixtures for reflected XSS (CWE-79), SQL injection (CWE-89), and path traversal (CWE-22). AI generates the repair candidates. This is a refinement of the original broad AI-generated-application proposal, not evidence of a representative AI-generated application corpus.

## Completed Tasks (Last 2 Week):

- Verified and incorporated the completed primary study into a separate results workflow: five initial model calls per CWE, 15 total, with fixed model/prompt conditions and a frozen protocol. Report 1 described the four-attempt pilot; the primary records are dated September 4 and are newly reported here, rather than claimed as additional trials run after Report 1.
- Implemented primary report verification and a separate 15-trial dashboard. Verification checks frozen inputs and implementation bindings, 105 attempt-artifact hashes, candidate source/patch evidence, reconstructed finding comparisons, policy decisions, and aggregate metrics. This makes the primary conclusions traceable without mixing pilot retries or the non-AI control into their denominator.
- Added evidence-bound human-review packets for the ten SAST/runtime disagreements. Two XSS reviews are recorded as ACCEPT_CANDIDATE; eight reviews remain pending. Human results remain separate from automated decisions. Added a rationale-file CLI option after embedded quotes caused Windows PowerShell argument errors, allowing review text to be recorded reliably.
- Implemented a separate versioned finding-history component for new, persistent, resolved, and reopened states. A recorded SQLi baseline/candidate/baseline replay demonstrates reopening, with tests for transitions, ambiguous identities, coverage changes, and tampering. This post-collection addition does not modify the frozen primary comparator or constitute a new live three-version experiment.
- Strengthened reproducibility and regression checks. The current verification run passed 89 automated tests on September 10. The September 5 fresh Python environment check passed the then-current 87 tests, restored all six pilot/primary apps' locked Node dependencies, and reproduced all four selected pilot demo decisions on the same Windows host. Later review-CLI tests account for the increase to 89.
- Refined the architecture, methodology, evidence map, repository guide, review instructions, and submission walkthrough. Active documentation distinguishes primary results from pilot history and identifies preserved experimental files versus generated dependencies. The original study inputs and candidate evidence remain intact.

Effort record: actual reporting dates, activity breakdown, and total hours are not yet reconciled for this draft. The prior report's 31.5 hours are not reused as this period's effort. I will enter my actual hours before submission; repository output and test counts cannot establish hours worked.

## Tasks for the Next Project Report:

- Complete the remaining eight conflict reviews: XSS trials 03–05 and path-traversal trials 01–05. For each, explain the patch behavior, persistent warning, security observations, functional observations, and any uncertainty. Preserve existing results; record any expanded analysis as a dated supplement.
- Define a small supplemental test matrix for gaps discovered during review, with expected outcomes fixed before testing. Prioritize additional XSS contexts and traversal boundary/encoding cases over adding another CWE. Save all outcomes separately from primary-v1, including failures and inconclusive results.
- Develop the related-work comparison and justify minimal fixtures, Semgrep with disclosed supplemental rules, one fixed model, and a SAST-only comparator. Explain what these choices make measurable and what realism they sacrifice.
- Draft the final methods/results sections and figures, rehearse the bounded demo, organize actual AI-use records, and run a clean committed-archive verification. Confirm the final course format and deadline separately from the internal late-November completion target.

## Questions I have or Issues I’m running into:

The main methodological issue is disagreement: ten primary candidates pass the targeted runtime and functional checks while their SAST target persists. I am reviewing these conflicts rather than automatically calling the warnings false positives. My first two written rationales primarily describe encoding changes; fuller discussion of scanner behavior and test limitations is still needed for the final analysis.

The primary sample contains no SAST false successes, so it cannot establish a detection rate for naturally generated patches that clear SAST but fail later checks. One app per CWE and identical SQLi source across five calls also limit diversity. Remote Semgrep auto rules were not fully archived, and the fresh-environment check used the same Windows host. These are limitations to report, not reasons to revise completed observations.

Instructor guidance requested: Is the refined three-fixture scope with repeated repairs and a separate supplemental test set sufficient to address the original scope concern? Would a second reviewer for selected disagreements be a more useful extension than another vulnerability class? These are open questions; instructor acceptance has not been assumed.

## Methodology Paragraph Summary:

Each primary fixture defines a target route, attacker-controlled input, vulnerable operation, synthetic data, and expected benign behavior. Baseline security checks establish the intended vulnerability independently of scanner detection. The frozen study uses Semgrep 1.136.0, a disclosed controlled SQLi rule where default coverage missed the target, and gpt-5.2 for five separate initial calls per CWE. Prompts withhold evaluator ground truth and test implementations. The model returns structured repair fields; implemented validators execute HTTP security/functional checks, with Chromium execution observations for primary XSS. SAST-only interpretation and the full deterministic policy are compared on the same saved candidate. Initial attempts, pilot retries, non-AI controls, human conclusions, and post-collection lifecycle work are analyzed separately. Repeated calls on one fixture are not independent applications, and passing targeted tests does not prove application-wide security.

Semgrep's rule-configuration documentation supports explicitly declaring the scanner configuration and distinguishing registry/default configurations from local rule files (Semgrep, n.d.). The planned supplemental tests will use OWASP's Web Security Testing Guide as a reference for reviewing input vectors, encoding, and attack behavior (OWASP Foundation, n.d.). These sources support design and test planning; they do not certify FixProof's implementation or establish that its fixed tests cover the complete guide.

## Timeline:

Week labels retain the 16-week planning structure from Report 1. Completed work has been brought forward; later weeks are refinement and contingency capacity, not evidence of hours already worked. The internal final-package target is late November; exact course dates must be confirmed in Canvas. W15–W16 are reserves only if the course schedule requires them.

| Week # | Description of Task | Status |
|---|---|---|
| W1 | Define the problem and compare candidate SAST tools. | Completed; Report 1 |
| W1 | Establish the repository and perform initial controlled scans. | Completed; Report 1 |
| W2 | Implement and validate the three-CWE pilot, including the XSS retry and non-AI control. | Completed; Report 1 |
| W2 | Freeze primary fixtures, protocol, model/prompt settings, and trial schedule. | Completed |
| W2 | Collect 15 primary initial attempts and retain their evidence. | Completed September 4 |
| W3 | Verify primary results and expose evidence in a separate dashboard. | Completed |
| W3 | Implement lifecycle history and verify the recorded reopening replay. | Completed |
| W3 | Restore dependencies in a separate environment and verify tests/demos. | Completed on same host |
| W3 | Record primary conflict reviews and resolve CLI rationale quoting. | 2/10 reviews; CLI fix complete |
| W4 | Complete eight pending reviews and document remaining evidence gaps. | Planned |
| W4 | Specify supplemental payloads and expected benign/attack outcomes. | Planned |
| W5 | Run the supplemental checks and retain all outcomes separately. | Planned |
| W6 | Compare related repair systems and justify FixProof's design choices. | In progress |
| W7 | Draft methods and results with primary/pilot/control separation. | Planned |
| W8 | Rehearse the demo and produce architecture/results figures. | Planned |
| W9 | Assemble a full paper draft with limitations and provenance. | Planned |
| W10 | Address review feedback and document any supplemental retesting. | Planned |
| W11 | Audit citations, metric claims, and AI-use records. | Planned |
| W12 | Reproduce the intended committed archive and inspect package contents. | Planned |
| W13 | Finalize the presentation narrative and rehearse its duration. | Planned |
| W14 | Finalize the paper and reproducible project package for the late-November target. | Planned |
| W15 | Recheck affected artifacts if final review identifies corrections. | Contingency |
| W16 | Reproduce any corrected package and preserve its verification record. | Contingency |

## Evaluation:

All 15 scheduled initial attempts have complete candidate and validation records. The fixed denominator excludes pilot attempts, retries, and the constructed non-AI control.

| Primary case | Initial attempts | Target SAST resolved | Security pass | Functional pass | Automated decision |
|---|---|---|---|---|---|
| Reflected XSS | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| SQL injection | 5 | 5/5 | 5/5 | 5/5 | 5 ready for review |
| Path traversal | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| Total | 15 | 5/15 | 15/15 | 15/15 | 5 ready; 10 disagreements |

Target-SAST resolution is 33.3%; SAST/runtime disagreement is 66.7%. No primary SAST false success or new SAST finding was observed. The 15 response IDs produced 11 distinct candidate sources: five XSS, one SQLi, and five traversal. Human conflict-review completion is 2/10; the five SQLi readiness decisions are not recorded approvals.

The separate pilot demonstrates a functional regression: the first XSS patch changed legitimate text into an output containing “undefined” and failed two of six functional checks. Its retry passed those checks, although SAST still persisted. This is not a SAST false success because the warning did not disappear. The separately constructed non-AI control demonstrates the false-success policy branch. Primary retry improvement is not applicable because no initial primary candidate was rejected. These results support traceable evidence separation within the controlled scope; they do not establish general repair effectiveness.

## Report Outline:

1. Problem, motivation, and research question.
2. Related work, alternatives, and specific contribution.
3. Controlled scope, threat model, and benchmark construction.
4. Architecture, model authority, validators, decision policy, and human boundary.
5. Frozen experimental method, comparator, provenance, and reproducibility.
6. Primary results, separate pilot/control examples, and actual human conclusions.
7. Supplemental evaluation, lifecycle demonstration, limitations, and deployment feasibility.
8. Conclusion, references, evidence index, and AI-use disclosure.

## References:

Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2021a). Asleep at the keyboard? Assessing the security of GitHub Copilot's code contributions [Preprint]. arXiv. https://arxiv.org/abs/2108.09293

Pearce, H., Tan, B., Ahmad, B., Karri, R., & Dolan-Gavitt, B. (2021b). Examining zero-shot vulnerability repair with large language models [Preprint]. arXiv. https://arxiv.org/abs/2112.02125

Kulsum, U., Zhu, H., Xu, B., & d'Amorim, M. (2024). A case study of LLM for automated vulnerability repair: Assessing impact of reasoning and patch validation feedback [Preprint]. arXiv. https://arxiv.org/abs/2405.15690

OWASP Foundation. (n.d.). Web Security Testing Guide (Version 4.2). Retrieved September 10, 2026, from https://wstg.owasp.org/v4.2/

Semgrep. (n.d.). Run rules. Retrieved September 10, 2026, from https://docs.semgrep.dev/running-rules

## Appendix

Evidence index: `docs/study-protocol-v1.md` records the frozen design; `benchmarks/primary/v1/` contains the three fixtures; `data/primary_trials/v1/` preserves candidate and validation evidence; `data/evaluation/primary-report.json` and `docs/primary-results.md` contain verified results; `data/primary_reviews/v1/` contains the separate reviewer records; `data/lifecycle/` contains the recorded reopening replay. `docs/README.md` maps active and historical documentation. Installed environments, local credentials, and disposable output are excluded from the source archive.

Verification: `python -m fixproof.reproduce --verify` rebuilds reports and runs the tests. `powershell.exe -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite` replays four pilot candidates with live runtime checks and recorded SAST. Neither command generates new AI candidates. The primary evidence view is `/ui/primary.html` after starting `python -m fixproof.reproduce --serve`.

Generative AI disclosure: OpenAI ChatGPT/Codex assisted with project planning, implementation, debugging, test orchestration, documentation, and preparation of this report draft. FixProof separately used the OpenAI API to generate remediation candidates; evaluator code and deterministic policy assessed their recorded behavior. Runtime prompts/responses are retained in experiment artifacts. Development and report-authoring conversations also require sanitized attribution records. I remain responsible for verifying the report, reporting my actual effort, and making human-review decisions. This draft does not attest that all personal review or disclosure work is complete.
