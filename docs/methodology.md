# FixProof Evaluation Methodology

## Research objective

FixProof evaluates whether a staged validation pipeline can distinguish
AI-generated vulnerability remediations that merely appear successful to a
static scanner from candidates that also preserve security and application
behavior.

The primary research question is:

> Does FixProof's multi-stage validation identify unsuccessful or functionally
> damaging AI-generated security fixes that would appear successful when
> remediation success is determined only by disappearance of the original SAST
> finding?

A secondary question asks whether measured failure evidence can improve a
retry without allowing the remediation model to grade itself.

## Experimental unit and benchmark selection

The aggregation unit is one scheduled initial remediation attempt, not one
vulnerability case. The existing authoritative manifest contains a feasibility
pilot with four AI-generated attempts across three controlled
JavaScript/Express cases:

| Case | CWE | Primary behavior under test | AI attempts |
|---|---:|---|---:|
| Reflected XSS | CWE-79 | Untrusted query value reflected in HTML | 2 |
| SQL injection | CWE-89 | Query input reaches a SQLite statement | 1 |
| Path traversal | CWE-22 | Request input controls a file path | 1 |

These pilot attempts are not part of the planned primary-trial denominator.
The primary study uses a frozen, versioned, target-only application for each CWE
and five independent initial attempts per case, for 15 scheduled initial
attempts. At most one eligible validation-feedback retry may follow an initial
attempt; retries are paired secondary outcomes and cannot replace or be
combined with the initial results.

Each benchmark is deliberately small enough to establish independent ground
truth and to test the affected endpoint deterministically. Results describe
this controlled sample and are not a production success-rate estimate. The
complete construction rules, AI contract, comparison mapping, failure rules,
and pre-freeze gates are defined in
[`docs/study-protocol-v1.md`](study-protocol-v1.md) and the machine-readable
`data/evaluation/trial-plan.json`. The internal protocol and primary-v1 suite
were frozen after all three baseline evidence gates passed; the results remain
subject to instructor review through the normal progress-report process.

## Experimental workflow

For each benchmark, FixProof follows the same sequence:

1. Establish vulnerability ground truth independently of SAST.
2. Record the default scanner's behavior.
3. Add a clearly labeled controlled rule only when default coverage is absent.
4. Normalize and correlate scanner evidence while preserving provenance.
5. Build focused source context and a structured remediation prompt.
6. Give the model scanner evidence and code context, but not ground truth tests.
7. Save the model response unchanged.
8. Apply the candidate only to an isolated attempt workspace.
9. Run syntax/build validation and a candidate SAST scan.
10. Compare the target semantically across baseline and candidate findings.
11. Run targeted runtime security validation.
12. Run functional and regression validation.
13. Compute a deterministic disposition from the recorded evidence.
14. Retry only when policy permits and use measured evidence as feedback.
15. Require a separate human review or adjudication at the policy boundary.

## Evidence channels

FixProof keeps five evidence channels separate:

- **Ground truth** confirms that the benchmark is genuinely vulnerable.
- **Scanner evidence** identifies rule findings and whether the target remains,
  resolves, or is accompanied by new findings.
- **Syntax/build evidence** determines whether the candidate is executable.
- **Targeted security evidence** exercises vulnerability-specific behavior with
  controlled payloads.
- **Functional evidence** checks intended behavior and regression cases.

No single channel is treated as sufficient proof. In particular, a resolved
SAST target is only one condition in the final policy.

## Scanner evidence provenance

A vulnerability can be experimentally confirmed even when a default scanner
rule set misses it, and adding a local evaluation rule does not retroactively
make the original scanner result a detection.

Every new normalized finding therefore records one of these rule origins:

- `semgrep_oss`: emitted by Semgrep's standard `auto` configuration.
- `fixproof_controlled`: emitted by a documented local FixProof rule carrying
  `fixproof_controlled_rule: true` in its Semgrep metadata.
- `unrecorded`: preserved for legacy artifacts created before provenance was
  added; no origin is inferred after the fact.

The origin is retained in normalized findings, canonical scanner evidence,
remediation contexts, prompts, and evaluation reports. The SQL injection result
must be described precisely: a runtime exploit established ground truth; the
default Semgrep CE configuration missed CWE-89; a documented, benchmark-focused
FixProof taint rule provided reproducible evidence for the remediation study.

## Remediation treatment

The remediation agent receives one canonical finding, focused source context,
rule provenance, and constraints to produce one minimal candidate. It does not
receive expected patches, hidden runtime payloads, ground-truth answers, or the
authority to validate its own response.

Model output is stored as a structured remediation artifact containing the
canonical ID, analysis, strategy, patched code, assumptions, and context-needs
flag. Model name and response ID are retained for auditability. Candidates are
never applied to the baseline application.

For the primary study, the fixed generator is `gpt-5.2`, the prompt template is
version `1.0`, and there are no model tools. The current Responses API call does
not explicitly set temperature, top-p, or seed, so those values are recorded as
provider/model defaults rather than inferred. Repetitions for a case receive
the same frozen task evidence and never receive results from other initial
attempts.

## Validation design

Preliminary validation checks JavaScript syntax, rescans the candidate, and
compares the baseline and candidate target by a semantic endpoint key rather
than a line-sensitive finding ID.

Targeted validators then test the behavior relevant to each CWE:

- CWE-79 sends markup and event-handler payloads, observes execution in
  headless Chromium, and separately verifies that ordinary and
  special-character inputs retain their intended value. Historical pilot
  artifacts used reflected-output evidence; primary-v1 uses browser execution.
- CWE-89 distinguishes expected username lookup from a classic injection that
  would return all seeded users, then verifies parameterized behavior.
- CWE-22 distinguishes approved public-file reads from traversal attempts and
  verifies normal file access remains intact.

Security and functional results can be `pass`, `fail`, or `inconclusive`.
Inconclusive security evidence cannot produce an automatic ready state.

## Deterministic disposition policy

The evidence-aware policy produces:

- `REJECT` for syntax failure, a new SAST finding, security failure or
  inconclusive security evidence, or functional failure.
- `READY_FOR_HUMAN_REVIEW` when syntax passes, the target resolves, no new
  findings appear, and both runtime validation layers pass.
- `NEEDS_HUMAN_ADJUDICATION` when syntax passes, the target persists, no new
  findings appear, and both runtime validation layers pass.

The last outcome explicitly records a SAST/runtime disagreement rather than
assuming either evidence source is universally correct.

## Retry treatment

Only policy-eligible failures may produce a retry prompt. The prompt contains
the prior candidate and measured syntax, scanner, security, and functional
evidence. The primary protocol permits at most one retry per eligible initial
attempt. It is analyzed as a paired secondary treatment and never replaces the
initial attempt. In the pilot, the XSS retry is considered improved because it
is no worse on all compared dimensions and improves functional preservation
from 4/6 to 6/6.

## Human adjudication

Human review uses an immutable packet that binds the decision, validators,
remediation, workspace, candidate source, and patch with recorded hashes. The
reviewer's identity, rationale, checklist, timestamp, and verdict are saved in
a separate result artifact. The human record does not mutate the automated
decision.

Allowed verdicts are `ACCEPT_CANDIDATE`, `REJECT_CANDIDATE`, and
`REQUEST_ADDITIONAL_TESTING`. The current authoritative matrix requires two
adjudications and contains two completed reviewer results.

## Metrics

Pilot metrics use the four manifest-selected AI-generated attempts as their
denominator; the non-AI outcome-coverage control is excluded. Future primary
metrics use all 15 scheduled initial attempts unless a metric explicitly
requires an applied candidate. Malformed or unapplicable model output remains a
recorded primary failure rather than being silently regenerated.

- **SAST remediation success rate:** target finding resolved / AI attempts.
- **Targeted security pass rate:** security validation passed / AI attempts.
- **Functional preservation rate:** functional validation passed / AI attempts.
- **New-finding rate:** one or more new SAST findings / AI attempts.
- **SAST false success:** target resolved while security is not pass,
  functionality fails, or new findings appear.
- **SAST/runtime disagreement:** target persists while security and functional
  tests pass and no new findings appear.
- **SAST-only apparent-success rate:** target resolved / scheduled initial
  attempts; the intentionally simplified comparator ignores runtime,
  functional, and new-finding evidence.
- **FixProof disposition distribution:** `REJECT`,
  `READY_FOR_HUMAN_REVIEW`, and `NEEDS_HUMAN_ADJUDICATION` / scheduled initial
  attempts.

Retry-improvement rate and adjudication-completion rate are secondary metrics.
Human review is never represented as an autonomous production acceptance.

## Pilot outcome-coverage control

The selected AI outputs did not organically produce a false success. To test
that policy branch deterministically, FixProof includes a static-output XSS
candidate that removes reflection. SAST reports the target resolved, targeted
security testing becomes inconclusive, and all functional cases fail.

This artifact is labeled `deterministic_non_ai` and
`outcome_coverage_only`. It demonstrates end-to-end false-success detection but
is never described as an AI result and is excluded from all primary metrics.

## Artifact selection and integrity

`data/evaluation/experiment-manifest.json` identifies the authoritative attempt
and control artifacts. Historical or superseded artifacts may remain on disk
without being double-counted. The report builder validates canonical IDs,
attempt lineage, decision evidence, test summaries, adjudication bindings, and
metric scope before computing results. The generated JSON records the path and
SHA-256 digest of every selected artifact.

## Reproducibility procedure

From the repository root, use the project virtual environment:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.reproduce --verify
```

The command regenerates `data/evaluation/experiment-report.json` and
`docs/evaluation-report.md`, verifies study invariants and control separation,
and runs the full unit-test suite. It does not call the model, rescan an
application, or overwrite a benchmark. `--serve` performs the same verification
and then starts the read-only dashboard.

## Threats to validity and limitations

- The sample contains three deliberately small JavaScript/Express cases.
- Endpoint-specific tests do not establish application-wide security.
- The browser-backed XSS checks cover a fixed route and payload set; they do not
  establish application-wide XSS safety.
- The controlled SQLi rule is intentionally benchmark-oriented and
  identifier-specific, not a general detector.
- Filesystem copies isolate attempts from baselines but are not hardened
  containers for arbitrary hostile programs.
- Historical XSS artifacts predate rule-provenance fields and are reported as
  `unrecorded`.
- One model configuration and a small number of attempts do not support broad
  claims about models, vulnerability classes, or production repositories.
- The false-success control proves policy coverage, not an organic frequency of
  AI false success.

These limitations should remain explicit in the report, presentation, and any
final paper.
