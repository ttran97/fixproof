# FixProof: A Validation-Oriented System for AI-Generated Vulnerability Remediation

Tony Tran  
Section: CS OCY, OC1  
Progress Report 3 — working draft verified through September 23, 2026

> **September 23 checkpoint, not a finished submission:** Update
> the effort record through the submission date, reconcile any September 11-13
> hours, and complete template-specific fields. Verify the live Canvas
> instructions, references, AI disclosure, rendering, and submission receipt.

## Problem Statement

AI coding tools can produce insecure code, while an AI-generated repair can
leave the original weakness exploitable, introduce a different weakness, or
change intended application behavior. Disappearance of a static-analysis
warning therefore provides incomplete evidence that a repair is correct.
Pearce et al. (2022) evaluated 1,689 Copilot-generated programs across 89
security scenarios and found approximately 40% vulnerable within that study.
Research has also evaluated LLMs as vulnerability-repair generators and used
external validation feedback to refine patches (Pearce et al., 2023; Kulsum et
al., 2024).

FixProof investigates how separately recorded static-analysis, targeted
runtime-security, functional, deterministic-policy, and human-review evidence
can support decisions about AI-generated repairs. Its scope is deliberately
limited to three controlled JavaScript/Express fixtures: reflected cross-site
scripting (CWE-79), SQL injection (CWE-89), and path traversal (CWE-22). This
scope supports repeatable evidence collection but does not represent all
AI-generated applications, vulnerability classes, or production conditions.

The 15 repair attempts do not estimate how often AI-generated repairs succeed
in production. Instead, the controlled benchmark evaluates whether separate
evidence channels reveal information omitted by an initial pass/fail result.
All 15 candidates passed the frozen primary security and functional checks,
but the preregistered supplemental evaluation later identified five
behavioral-parity failures, ten robustness failures, and five inconclusive
symlink-security observations. These results support the project goal at the
workflow level: an AI-generated repair should be treated as an untrusted
candidate and evaluated through preserved static, runtime, behavioral, policy,
and human-review evidence. The measured percentages apply only to these three
fixtures and are not projected to production repositories.

## Solution Statement

FixProof is a Python orchestration and evaluation prototype. It scans a
controlled Express application with Semgrep CE, normalizes a finding, and gives
a remediation model one finding plus focused source context. The returned
candidate is applied only to a copied workspace. FixProof then checks syntax,
reruns SAST, and executes targeted security and functional tests. Deterministic
policy routes the evidence to `REJECT`, `READY_FOR_HUMAN_REVIEW`, or
`NEEDS_HUMAN_ADJUDICATION`; the repair model does not approve or deploy its own
patch.

These implementation choices are deliberate. Three minimal fixtures make
ground truth, attack behavior, and benign behavior reproducible within the
practicum timeline, at the cost of production realism. A fixed model, prompt
version, and five calls per CWE hold generation conditions constant while
showing within-fixture variation; they do not provide independent application
samples or model-to-model comparison. Semgrep supplies one preserved static
signal, while targeted runtime and functional checks measure exploit behavior
and intended behavior separately. Copied workspaces preserve study inputs but
are not security sandboxes. Deterministic policy makes evidence handling
repeatable, and a separate human boundary prevents the repair model from
approving its own output.

The project deliverables are the prototype, three versioned benchmark
fixtures, preserved primary and supplemental evidence, deterministic reports,
a dashboard and CLI demonstration, reproducibility documentation, and the
final report and presentation. The project evaluates AI-generated repairs to
purpose-built fixtures. It does not claim to evaluate a representative corpus
of AI-generated applications.

## Completed Tasks Since Progress Report 2 (September 23 Checkpoint)

**Reporting checkpoint:** September 14-23, 2026, after submitting Report 2 on
September 13. Extend this period and update the estimate for any further work
completed before submitting Report 3.  
**Effort since Report 2 submission:** Approximately 15 hours through September
23, based on Tony's estimate of 1.5 hours per day from September 14 through
September 23 (ten days). Time was
primarily spent reviewing the project file structure and documentation,
checking test and saved-evidence results, and reviewing candidates and recording
human rationales, preparing the evidence appendix, and aligning the report with
the professor's feedback. This is a self-reported estimate, not time inferred
from commits or automated runs.  
**Cumulative effort:** Not yet reconciled. Earlier reports stated 31.5 hours
before the 13.5-hour September 2-10 period. Adding this checkpoint's estimated
15 hours gives approximately 60 hours **plus any September 11-13 work not
included in Report 2's 13.5 hours**. Enter a reconciled cumulative figure
before submission; do not silently count those dates as zero.

The ten original human reviews and Video II posting were already reflected in
the September 13 checkpoint. They are background for the work below, not new
accomplishments counted again in this reporting period.

- Defined and froze the `supplemental-v1` protocol before candidate execution.
  The protocol separates security, behavioral-parity, and new robustness
  requirements rather than combining them into one success label.
- Implemented isolated supplemental execution with registered cases,
  environment preflight, disposable application copies, fixture preparation,
  saved observations, and report verification. The supplement characterized
  all three baselines before evaluating the 15 saved primary candidates; it
  made no new model calls and did not rewrite primary-v1.
- Evaluated 140 registered candidate-case observations. Security recorded 55
  passes, zero failures, and five inconclusive cases. Behavioral parity
  recorded 40 passes and five failures. Robustness recorded 25 passes and ten
  failures. These categories have different meanings and are not combined into
  a security success rate.
- Recorded three dated, evidence-bound requested follow-up decisions. XSS 04
  and 05 were rejected because they changed the frozen missing-input behavior. Path-
  traversal 01 was rejected because it blocked a valid in-root filename and
  missed a repeated-parameter contract. The original primary reviews and
  metrics were preserved.
- On September 21, applied the same frozen parity criterion to the previously
  accepted XSS 01 and 02 candidates. Both received separate
  `FOLLOW_UP_REJECT_CANDIDATE` qualifications after personal evidence review.
  Their original primary acceptances and all primary metrics remain unchanged.
- Verified that all five SQLi candidates passed the supplemental security,
  baseline-parity, punctuation, and Unicode cases, but missed the newly defined
  repeated-parameter robustness requirement. Traversal attempts 03 and 05 also
  missed supplemental robustness cases. These are newly defined contract
  limitations, not retroactive primary security failures.
- On September 22, recorded five bounded SQLi acceptances and four traversal
  requests for more testing as separate, evidence-bound human results. All 14
  supplemental human packet/result bindings verify; primary records and test
  outcomes remain unchanged.
- Preserved the path-traversal symlink case as inconclusive after Windows
  denied creation of the required fixture. The unexecuted case was not counted
  as a pass.
- Corrected a supplemental verifier portability defect caused by a saved
  absolute source path from another checkout. Verification now resolves the
  registered application in the active checkout and still checks its content
  hash. No saved experimental result or frozen primary implementation changed.
- On September 22, the repository passed 119 automated tests. Primary evidence
  verification confirmed all 15 attempts and all ten original reviews;
  supplemental verification confirmed three baselines and 15 saved candidates,
  and the human-record verifier confirmed 14/14 completed records.
  These checks establish current internal consistency but did not repeat the
  historical model calls, live SAST runs, or application/browser experiments.
- Generated and inspected the 15-candidate evidence appendix. Its primary and
  supplemental matrices preserve original automated states, registered
  failures and inconclusive cases, all 14 later human decisions, and complete
  recorded rationales. It is a Video III backup reference rather than a
  replacement for the report narrative.
- The required Video II peer-feedback activity due September 27 is in progress
  and remains a separate course obligation.

## Methodology Paragraph Summary and Design Rationale

The primary experiment remains frozen at five initial model calls per CWE, for
15 total attempts. Each fixture defines a vulnerable route, attacker-controlled
input, ground-truth attack behavior, and expected benign behavior. The fixed
primary evaluation compares SAST-only interpretation with the complete policy
using the same saved candidate. Primary results, pilot retries, the constructed
non-AI control, lifecycle history, and supplemental observations remain in
separate denominators.

The 15 scheduled calls are experimental attempts, not 15 independent
applications or 15 unique patches. The five SQLi calls produced identical
candidate source, while XSS and path traversal each produced five distinct
candidate sources. This duplication is preserved as an observed model outcome
and prevents the repeated SQLi code from being presented as five independent
implementations.

The supplemental study was motivated by gaps found during human review. Cases
and oracles were registered before candidate execution. The same applicable
cases were run first against the baseline and then against every saved candidate
for that CWE in a disposable copy. Security cases ask whether registered attacks
execute or escape their intended boundary. Behavioral-parity cases compare
candidate output with the frozen baseline. Robustness cases impose explicit new
handling requirements for malformed or ambiguous input. An unavailable case is
inconclusive rather than successful.

This design makes omitted behavior visible. It does not prove application-wide
security: registered tests cover selected inputs, SAST coverage is
configuration-dependent, and repeated candidates from one fixture are not
independent applications.

The choice of three CWEs rather than broad OWASP coverage permits a frozen
route, attack, ground truth, and benign-behavior oracle for each fixture, with
five repeated model attempts per class. One fixed model and prompt minimize
variation in this small study; they do not support model-to-model claims.
Semgrep supplies a reproducible static signal, including a disclosed local
SQLi rule where default detection missed the target, but scanner disappearance
is not the success oracle. The same saved candidates are inspected under the
SAST-only interpretation and the full validation policy. A bounded pilot retry
is reported separately from the 15 initial primary attempts. These choices
prioritize traceability over corpus diversity, production-scale functional
coverage, performance measurement, or generalizability.

### Related-work comparison

Pearce et al. (2022) studied the security of AI-generated code across many
controlled scenarios; that work motivates treating generated output as
untrusted but does not evaluate FixProof's repair workflow. Pearce et al.
(2023) studied zero-shot vulnerability repair across synthetic, hand-crafted,
and historical real-world cases using multiple models; their reported
functional-correctness difficulties motivate FixProof's separate behavioral
checks. Kulsum et al. (2024) evaluated VRpilot on C and Java datasets and used
compiler, sanitizer, and test feedback to iteratively refine patches. That
work establishes validation-feedback repair as prior art, not a novel FixProof
invention.

FixProof instead holds one small web fixture per CWE and a fixed model/prompt
constant, then preserves stage-level static, runtime-security, functional,
and later supplemental outcomes for the *same* saved candidates. Its human
boundary and category-specific evidence records are a prototype contribution,
not a claim of superior repair performance over those studies. A direct
cross-study success-rate comparison would be invalid because the datasets,
languages, models, and success criteria differ. The remaining final-paper work
is to develop this comparison in more detail and test claims against each
paper, not just add more citations.

## Evaluation

### Frozen primary study

| Primary case | Initial attempts | Target SAST resolved | Security pass | Functional pass | Automated decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Reflected XSS | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| SQL injection | 5 | 5/5 | 5/5 | 5/5 | 5 ready for review |
| Path traversal | 5 | 0/5 | 5/5 | 5/5 | 5 need adjudication |
| **Total** | **15** | **5/15** | **15/15** | **15/15** | **5 ready; 10 disagreements** |

The target SAST finding resolved in 33.3% of attempts, while 66.7% produced a
SAST/runtime disagreement. No primary SAST false success was observed. That
absence does not establish that FixProof prevents false confidence generally.
The five SQLi `READY_FOR_HUMAN_REVIEW` outcomes are readiness states, not
recorded approvals.

### Supplemental study

| Category | Candidate observations | Pass | Fail | Inconclusive | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Security | 60 | 55 | 0 | 5 | Every executable registered attack case passed; five symlink cases were unavailable. |
| Behavioral parity | 45 | 40 | 5 | 0 | Four XSS candidates changed missing-name output; traversal 01 rejected a valid filename. |
| Robustness contract | 35 | 25 | 10 | 0 | All SQLi candidates and selected traversal candidates missed new input-handling rules. |
| **Total** | **140** | **120** | **15** | **5** | Mixed evidence categories; not one security success rate. |

### Recorded review decisions for remaining supplemental cases

On September 22, after reviewing the linked patches and supplemental evidence,
I recorded nine additional candidate-level human results. I accepted SQLi attempts 01–05
acceptable for the bounded SQL-injection repair because their parameterized
queries passed every registered security and behavioral-parity case and
returned no broadened or unauthorized rows. Each candidate still failed the
new `SQL-R01` repeated-parameter robustness requirement by returning HTTP 200
with `[]` instead of HTTP 400. I retain that outcome as a failed robustness
case and disclose the client-visible status-code limitation; bounded acceptance
does not mean full supplemental conformance.

For path-traversal attempts 02–05, I recorded requests for more testing.
Traversal 03 failed three malformed-input robustness
contracts and traversal 05 failed the repeated-parameter contract. More
importantly, `PATH-S06` remains inconclusive for every traversal candidate
because the Windows environment could not create the required symlink fixture.
The executable attacks passed, but symlink-escape protection remains unverified.
These are separate dated human records and do not alter the original primary
acceptances, registered test outcomes, or metrics. The verifier confirms all
14 supplemental human packet/result bindings: five rejections, five bounded
acceptances, and four requests for more testing.

### Compact candidate comparison

| Evidence | XSS 03 | XSS 04 |
| --- | --- | --- |
| Primary SAST target | Persistent | Persistent |
| Primary security and functional checks | Pass | Pass |
| Supplemental security | 3/3 pass | 3/3 pass |
| Supplemental behavioral parity | 5/5 pass | 4/5 pass |
| Supplemental robustness | 1/1 pass | 1/1 pass |
| Missing `name` behavior | Preserves `Hello undefined` | Changes output to `Hello ` |
| Recorded human outcome | Original acceptance retained | Follow-up rejection |

This comparison demonstrates why the original passing counters were not enough.
Both candidates passed the registered attacks, but only XSS 03 preserved every
registered benign behavior. XSS 04 was rejected for a bounded functional-parity
failure, not because the tested XSS payloads remained exploitable.

### Later qualification of XSS 01 and 02

XSS 01 and 02 were originally accepted, but each later failed the same
`XSS-P01` missing-input parity case as XSS 04 and 05. Their registered
supplemental counts are eight passes and one failure, including 3/3 security
passes, 4/5 parity passes, and 1/1 robustness pass. On September 21, Tony
reviewed both patches, their original decisions, and all nine supplemental
outcomes for each candidate. He recorded `FOLLOW_UP_REJECT_CANDIDATE` for both.

For XSS 01, `String(value ?? "")` converted the omitted value to an empty
string. For XSS 02, `String(name ?? "")` produced the same change. In both
cases, the observed heading was `Hello ` instead of the frozen baseline
`Hello undefined`. These are bounded behavioral-parity decisions; they do not
mean the registered XSS attacks remained exploitable. The later records
qualify, but do not overwrite, the original acceptances or primary metrics.

## Interpretation and Response to Feedback

The supplemental study responds directly to feedback about whether a fix can
pass the original checks while changing application behavior. It also makes the
evaluation more systematic through frozen inputs, predefined category-specific
oracles, repeated repair attempts, baseline/candidate symmetry, preserved raw
observations, and separate human conclusions.

The work also clarifies what the AI component does. The experimental model
proposes candidate source code. Python orchestration, Semgrep, targeted runtime
tests, deterministic policy, and a person provide separate evidence and
decisions. Codex assistance used during project development and report drafting
is distinct from the model calls that generated experimental repair candidates.

The three-CWE scope remains intentional. Adding more weakness classes now would
increase breadth without addressing the strongest observed limitation: the
original fixed tests did not capture every relevant behavior. The current
priority is consistent interpretation, comparison with prior work,
reproducibility, and clear communication of what the evidence supports.

## Questions I Have or Issues I Am Running Into

Later evidence required qualifying two earlier human decisions. XSS 01 and 02
shared the same supplemental parity failure as XSS 04 and 05, so the frozen
criterion was applied consistently through separate dated rejection records.
This preserved what was known during the original reviews while making the
later interpretation explicit.

The symlink escape case remains unexecuted because the Windows environment
could not create the fixture. This limits the traversal conclusion. A later run
on a suitable environment could reduce that uncertainty, but any such run must
be separately dated and must not turn the original inconclusive outcome into a
pass.

The study uses one controlled application per CWE and five repairs per fixture.
It therefore provides repeated repair observations, not broad application
diversity or a general repair-success estimate. Remote Semgrep rule provenance,
the same-host reproducibility check, targeted-test coverage, and the lack of
performance/load evaluation are additional limitations.

Feedback requested: Is the category-separated supplemental evaluation and
consistent follow-up review sufficient for this practicum scope? Would an
independent second reviewer for selected disagreements add more useful evidence
than another vulnerability class?

## Tasks for the Next Project Report

- Expand the related-work comparison across benchmark type and size, repair
  model, validation oracle, retries, success definition, and limitations.
- Draft the final paper's methods and results sections using the verified
  primary/supplemental separation and explicit denominators.
- Prepare Video III around XSS 03 versus XSS 04, showing the patch, independent
  evidence channels, missing-input parity result, and human boundary.
- Decide whether the symlink limitation should remain documented or receive a
  separately dated run on an environment that supports the fixture.
- Add supplemental verification to the clean-package checklist and rehearse the
  evidence dashboard plus one saved-candidate replay.
- Create a clean versioned release snapshot before the final demonstration,
  excluding local dependencies, caches, generated logs, and secrets; rerun all
  evidence and automated checks from the packaged copy.
- Complete required peer feedback and incorporate substantive feedback when it
  materially changes the research or presentation.

## Timeline

| Milestone | Status |
| --- | --- |
| Define problem, compare SAST options, and establish repository | Completed |
| Implement three-CWE pilot and separate non-AI control | Completed |
| Freeze primary fixtures, protocol, prompt/model settings, and schedule | Completed |
| Collect and verify 15 primary initial attempts | Completed September 4 |
| Implement primary dashboard, review packets, and finding lifecycle | Completed |
| Complete ten original disagreement reviews | Completed September 12 |
| Predefine and freeze supplemental protocol and oracles | Completed September 14 |
| Characterize three baselines and evaluate 15 saved candidates | Completed September 14-15 |
| Record three originally requested follow-up decisions | Completed September 15 |
| Qualify XSS 01-02 consistently against later evidence | Completed September 21 |
| Record nine SQLi/traversal decisions and verify 119 tests plus 14 follow-up records | Completed September 22 |
| Complete evidence appendix and align Report 3 with professor feedback | Completed September 23 |
| Submit Video II peer feedback | In progress; due September 27 in supplied schedule |
| Complete and submit Progress Report 3 | Planned October 1; confirm live Canvas deadline |
| Prepare Video III evidence comparison | Next presentation milestone |
| Strengthen related work and draft final methods/results | In progress / next phase |
| Rehearse reproducible package and final presentation | Planned for October-November |
| Submit final presentation video | November 15 in supplied schedule |
| Submit final report | December 6 in supplied schedule |

## Report Outline

1. Problem, motivation, and research question.
2. Related work, alternatives, and specific contribution.
3. Controlled scope, threat model, and benchmark construction.
4. Architecture, model authority, validators, decision policy, and human boundary.
5. Frozen primary method, comparator, provenance, and reproducibility.
6. Primary results, pilot/control examples, and original human reviews.
7. Supplemental method, results, follow-up qualifications, and limitations.
8. Conclusion, evidence index, references, and AI-use disclosure.

## References

Kulsum, U., Zhu, H., Xu, B., & d'Amorim, M. (2024). A case study of LLM
for automated vulnerability repair: Assessing impact of reasoning and patch
validation feedback. *Proceedings of the 1st ACM International Conference on
AI-Powered Software (AIware '24)*. https://doi.org/10.1145/3664646.3664770

OWASP Foundation. (n.d.). *Web Security Testing Guide, version 4.2*.
https://wstg.owasp.org/v4.2/

Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2022).
Asleep at the keyboard? Assessing the security of GitHub Copilot's code
contributions. *2022 IEEE Symposium on Security and Privacy*.
https://doi.org/10.1109/SP46214.2022.9833571

Pearce, H., Tan, B., Ahmad, B., Karri, R., & Dolan-Gavitt, B. (2023).
Examining zero-shot vulnerability repair with large language models. *2023
IEEE Symposium on Security and Privacy*.
https://doi.org/10.1109/SP46215.2023.10179324

Semgrep. (n.d.). *Run rules*. https://semgrep.dev/docs/running-rules

## Appendix: Evidence Index and Verification

- Frozen primary method: `docs/study-protocol-v1.md`.
- Primary fixtures: `benchmarks/primary/v1/`.
- Primary evidence and reviews: `data/primary_trials/v1/` and
  `data/primary_reviews/v1/`.
- Supplemental protocol and results: `docs/supplemental-protocol-v1.md`,
  `data/supplemental/v1/`, and `docs/supplemental-results-v1.md`.
- Current primary and supplemental verification:
  `python -m fixproof.evaluation.primary_report --check` and
  `python -m fixproof.evaluation.supplemental_report --check`.
- Full automated checks: `python -m unittest discover -s tests -v`.

The source-archive packaging script currently checks the primary report but
does not separately check the supplemental report or the later human
follow-up bindings. Add those checks to the final packaging rehearsal; do not
claim a clean committed-archive check has already passed.

Verification checks stored evidence, hashes, report reconstruction, and current
software behavior under tests. It does not authenticate the original
observations independently or rerun every historical external tool and
application execution.

## Generative AI Disclosure

OpenAI ChatGPT/Codex assisted with project planning, implementation, debugging,
test orchestration, documentation, evidence organization, and preparation of
this report draft. FixProof separately used the OpenAI API to generate the saved
experimental remediation candidates. The evaluation harness and deterministic
policy assessed their recorded behavior; Tony Tran remains responsible for
checking the evidence, making human review decisions, reporting actual effort,
verifying citations and claims, and approving the submitted text. Experimental
prompts and responses are retained with the project evidence. This disclosure
must be reconciled with the actual tools and records used before submission.

## Submission Checklist

- [ ] Update the September 14-21 estimated 12 hours through the final report
      cutoff, reconcile any September 11-13 work, and enter cumulative hours.
- [x] Record Tony's XSS 01 and 02 supplemental conclusions without altering
      the original primary records.
- [ ] Confirm peer-feedback completion separately when finished.
- [ ] Confirm live Canvas requirements and deadline.
- [ ] Check every number against the saved reports.
- [ ] Explicitly check supplemental evidence and five later review bindings
      when rehearsing the committed source archive.
- [ ] Verify citations and apply the required citation style.
- [ ] Personally verify the AI disclosure and retain required interaction
      records.
- [ ] Transfer this draft into the official template, inspect the rendered
      document, and retain the submission receipt.
