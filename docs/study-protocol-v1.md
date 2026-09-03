# FixProof Primary Study Protocol v1

## Status

This internal protocol was revised in response to instructor feedback about
scope, benchmark construction, the AI component, and evaluation rigor. It was
frozen on September 3, 2026 after the technical pre-freeze gates passed. The
design will be communicated through the normal course progress reports rather
than as a separate protocol submission.

The four existing AI attempts and the non-AI policy control are pilot evidence.
They establish feasibility and exercise the pipeline, but they are not part of
the planned primary-trial denominator.

## Research question and claim boundary

The primary research question is:

> Does FixProof's multi-stage validation identify unsuccessful or functionally
> damaging AI-generated security fixes that would appear successful when
> remediation success is determined only by disappearance of the original SAST
> finding?

FixProof does not claim to prove that an application is secure or that its
results generalize to production repositories. Its intended result is a more
complete, auditable evidence record for a human decision within three
controlled JavaScript/Express cases.

## Scope

### In scope

- JavaScript/Node.js applications using Express;
- reflected XSS (CWE-79), SQL injection (CWE-89), and path traversal (CWE-22);
- one target-only primary benchmark application per CWE;
- Semgrep Community Edition 1.136.0 with preserved rule provenance;
- one fixed remediation model, one prompt-template version, and five initial
  attempts per CWE;
- syntax, SAST, targeted runtime-security, and functional-regression evidence;
- deterministic dispositions followed by a separate human boundary; and
- one optional validation-feedback retry per eligible primary attempt,
  analyzed as a paired secondary condition.

### Out of scope

- arbitrary or hostile third-party repositories;
- automatic production approval or deployment;
- claims about every variant of a CWE;
- model-to-model, language-to-language, or SAST-tool comparisons;
- comprehensive Semgrep accuracy measurement; and
- statistically generalizable estimates of AI repair performance.

## Options considered and choices

| Design question | Options considered | Selected choice and justification |
|---|---|---|
| Vulnerability breadth | Many CWEs with few observations, or three CWEs with repeated attempts | Three CWEs with five initial attempts each. Depth supports repeatable, complete evidence chains within the practicum timeline. |
| Application source | Large public applications, public benchmark suites, or purpose-built minimal applications | Purpose-built target-only applications. They make ground truth, benign behavior, and exploit oracles deterministic; the resulting loss of production realism is reported as a limitation. |
| AI role | Autonomous repository agent, test-aware repair loop, or constrained single-finding generator | Constrained single-finding generator. This keeps model generation separate from evaluation and makes inputs and outputs auditable. |
| Scanner treatment | Treat SAST as ground truth, ignore scanner misses, or preserve default results and label supplemental rules | Preserve default Semgrep behavior and separately label any FixProof-controlled rule. Ground truth remains independent of SAST. |
| Acceptance evidence | Disappearance of the target SAST finding alone, or multi-stage validation | Evaluate both approaches on the same candidate. This isolates the value added by runtime and functional evidence. |
| Retry treatment | Unlimited repair loop, no retry, or one validation-informed retry | At most one retry for an eligible rejection. Retry evidence is paired with its parent and excluded from primary-attempt rates. |

## Primary benchmark construction contract

The existing `sample_apps/` applications and selected artifacts remain the
pilot snapshot. The versioned `benchmarks/primary/v1/` suite was created
without altering those historical files. Each primary application contains
exactly one intentionally seeded target vulnerability and no unrelated
intentionally seeded vulnerability.

| Case | Route and input | Source and sink | Baseline exploit oracle | Benign behavior oracle | Scanner treatment |
|---|---|---|---|---|---|
| Reflected XSS, CWE-79 | `GET /hello?name=...` | `req.query.name` to `res.send` HTML | Controlled markup/script reaches an executable browser context | Ordinary text and special characters retain their displayed value | Record Semgrep `auto`; the frozen target configuration must identify the target |
| SQL injection, CWE-89 | `GET /user?username=...` | `req.query.username` to a SQLite query API | A tautology payload returns rows outside the intended lookup | Known users return only expected rows; unknown users return none | Preserve the default Semgrep miss and use the labeled controlled SQLi rule v2 for target comparison |
| Path traversal, CWE-22 | `GET /file?name=...` | `req.query.name` to `fs.readFile` | Encoded or unencoded parent traversal reads only an artificial outside fixture | Approved public files remain readable and missing files retain expected behavior | Record Semgrep `auto`; the frozen target configuration must identify the target |

Before a benchmark is eligible for primary trials, its record must contain:

1. a fixed application path and baseline SHA-256;
2. one CWE, route, input, source, and sink;
3. the exact scanner version, configuration, target rule, and rule origin;
4. a reproducible exploit that succeeds against the baseline;
5. functional tests that pass against the baseline;
6. security and functional tests reviewed before model generation;
7. synthetic fixtures only, with no host or personal data;
8. a dependency lockfile and recorded runtime versions; and
9. confirmation that no unrelated vulnerability was intentionally seeded.

For CWE-79, browser execution is the primary exploit oracle. Reflected-response
inspection may remain as supplementary evidence, but it must not be described
as proof of browser-level exploit prevention.

## AI remediation component

The AI component is a constrained patch generator, not the evaluator or final
decision maker. Each initial attempt starts from the byte-identical vulnerable
baseline and receives only:

- one canonical finding ID;
- CWE and vulnerability category;
- Semgrep rule ID, description, and rule provenance;
- affected filename and code region;
- focused surrounding source context; and
- instructions to produce a minimal repair while preserving behavior.

It does not receive:

- ground-truth answers or reference patches;
- security- or functional-test implementations;
- hidden payload lists or expected test outputs;
- results from other primary attempts;
- authority to modify tests, validation logic, or scanner configuration; or
- authority to approve or deploy its candidate.

The model must return structured data containing the canonical ID, analysis,
remediation strategy, complete replacement code for the supplied source
context, assumptions, and an additional-context flag. FixProof saves the
response unchanged, verifies the canonical ID, and applies the code only to an
isolated candidate workspace. The explanation is evidence, not a grade.

The initial treatment uses `gpt-5.2` through the OpenAI Responses API. FixProof
does not explicitly send temperature, top-p, seed, or tool parameters, so the
protocol records those settings as provider/model defaults rather than
inventing values.

## Primary trial design

- Experimental unit: one scheduled initial remediation attempt.
- Initial attempts: five per CWE, 15 total.
- Starting state: the same frozen baseline for every attempt in a case.
- Prompt: identical versioned template and case evidence for repetitions of a
  case; only generated trial identifiers and timestamps may differ.
- Model: one fixed model for all initial attempts.
- Independence: no prior primary output or result is included in another
  initial prompt.
- Stopping rule: complete all 15 scheduled initial attempts; do not stop early
  because a desired outcome appears.
- Pilot separation: existing attempts are excluded from the primary denominator.

## Validation and comparison

Every valid candidate is evaluated by both approaches using the same recorded
source and evidence.

### SAST-only interpretation

- `APPARENT_SUCCESS`: the original target finding is resolved.
- `FAILURE`: the target finding persists.
- `INCONCLUSIVE`: a usable candidate scan is unavailable.

This deliberately simplified comparator ignores runtime security, functional
behavior, and newly introduced findings. It represents the claim under test:
that disappearance of the original finding is sufficient evidence of repair.

### FixProof disposition

- `REJECT`: syntax/startup failure, new SAST findings, failed or inconclusive
  targeted security validation, or failed functional validation.
- `READY_FOR_HUMAN_REVIEW`: target resolved, no new findings, and both runtime
  validation layers pass.
- `NEEDS_HUMAN_ADJUDICATION`: target persists, no new findings, and both runtime
  validation layers pass.

Neither automated positive state is production acceptance. A human remains the
final approval boundary, and human results are stored separately from the
automated disposition.

## Outcomes and metrics

Primary metrics use the 15 scheduled initial attempts as the denominator unless
the metric explicitly requires an applied candidate:

- valid-candidate generation/application rate;
- target-SAST resolution rate;
- targeted security-validation pass rate;
- functional-preservation rate;
- new-SAST-finding rate;
- SAST-only apparent-success rate;
- FixProof disposition distribution;
- SAST false-success count and rate; and
- SAST/runtime disagreement count and rate.

A SAST false success occurs when SAST-only reports `APPARENT_SUCCESS` but
FixProof rejects the same candidate because security, functionality, syntax, or
new-finding evidence fails. Results are descriptive; no population-level
statistical claim will be made from 15 attempts.

Retry-improvement and adjudication-completion measures are secondary. Retries
are paired with their parent attempt and never replace the primary result.

## Failure, rerun, and exclusion rules

- A structured model response that cannot be parsed, references the wrong
  finding, or cannot be applied is a recorded model/candidate failure. It is not
  silently regenerated and remains in the primary denominator.
- Candidate syntax or application-startup failure is a failed candidate and
  remains in the primary denominator.
- A transport, credential, scanner-execution, port-conflict, or validator
  infrastructure failure is documented and rerun using the same saved
  candidate when one exists. It is not relabeled as a remediation failure.
- Runtime startup and HTTP request timeouts are fixed at 10 seconds and 5
  seconds respectively. The implemented Semgrep process timeout is fixed at
  120 seconds.
- A benchmark may be excluded only before primary model generation if its
  baseline contract fails. After collection begins, exclusions require a
  documented protocol deviation and may not depend on candidate outcomes.
- If an infrastructure problem cannot be corrected, the affected observation
  is reported as missing/inconclusive; it is not replaced without disclosure.

## Optional retry condition

One retry is allowed only when the initial FixProof disposition is `REJECT` and
the policy marks retry as allowed. The retry receives the original task, prior
candidate, and measured validation failures. It is a paired secondary
treatment, not an independent primary attempt. No third attempt is permitted.

## Pre-freeze gates

The following gates were completed before the September 3, 2026 internal
freeze:

1. the target-only benchmark suite and benchmark manifest exist;
2. all three baseline ground-truth checks pass;
3. the browser-level CWE-79 oracle is automated;
4. the prompt template, model identifier, scanner configuration, controlled
   rule revision, environment, and timeouts are recorded;
5. failure, rerun, exclusion, retry, and stopping rules are implemented;
6. byte-identical restore checks and the complete automated test suite pass;
7. the protocol and benchmark hashes are captured; and
8. the revised design and evidence paths are ready to report through the
   course progress-report process.
