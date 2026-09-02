# FixProof Threat Model

## Objective and scope

FixProof evaluates AI-generated remediations for deliberately vulnerable,
local JavaScript/Express benchmarks. The protected outcome is an evidence-based
human review decision, not autonomous production deployment.

## Assets

- the unchanged vulnerable baseline and independently established ground truth;
- the exact model prompt, response identifier, and candidate remediation;
- scanner rule provenance and before/after SAST findings;
- targeted security and functional-regression results;
- deterministic policy decisions and retry lineage;
- human adjudication packets, results, and artifact hashes;
- local credentials such as `OPENAI_API_KEY`.

## Trust boundaries

| Boundary | Less-trusted side | Trusted control |
|---|---|---|
| Model generation | AI-generated analysis and patched code | Structured output validation and isolated application |
| Candidate execution | Modified benchmark application | Disposable workspace, local-only endpoint, and controlled process lifecycle |
| Scanner output | Rule matches, misses, and false positives | Independent ground truth, rule provenance, and runtime validation |
| Runtime security tests | Endpoint behavior for selected payloads | Explicit pass/fail/inconclusive criteria and preserved raw results |
| Functional tests | Selected expected behaviors | Separate regression cases that the remediation prompt does not reveal |
| Automated policy | Deterministic classification | Human review or adjudication before acceptance |
| Repository/package | Local generated files and secrets | Ignore rules, tracked-file archive, and clean-extraction verification |

## Threat and failure cases

### Candidate evades SAST without fixing behavior

The target finding may disappear because functionality was removed or the code
was transformed beyond rule coverage. FixProof requires targeted security and
functional evidence before a candidate becomes ready for review.

### Candidate fixes the exploit but breaks intended behavior

The XSS first attempt demonstrates this failure: security tests passed while
functional tests detected corrupted adjacent special characters. The policy
rejects the candidate.

### Scanner misses a real vulnerability

Ground truth is established independently. A controlled rule may supplement a
default miss, but its origin must remain labeled and must not be presented as a
default Semgrep detection.

### Scanner and runtime evidence disagree

A persistent target with passing runtime security and functional tests is not
automatically accepted or rejected. It is classified as a disagreement and
sent to human adjudication.

### Remediation model influences its own grade

The model does not receive hidden ground-truth test answers and cannot write
the final decision. Validation and policy execution occur outside the model
response.

### Candidate modifies the original application or unrelated files

Candidates are applied to copied workspaces. Workspace metadata records the
original and candidate hashes, patch hash, and whether the original changed.

### Stale or tampered evidence is presented

The authoritative manifest selects attempts. Reports recompute stage summaries
and SHA-256 bindings, while adjudication packets bind the reviewed evidence and
refuse stale content.

### Secret or generated dependency enters a submission

The API key remains in an ignored `.env`. Submission packaging must operate on
tracked files and must exclude `.env`, virtual environments, `node_modules`,
temporary outputs, and unselected generated workspaces.

## Out of scope

- malicious arbitrary third-party repositories;
- hardened container or operating-system isolation;
- production CI/CD deployment and automatic approval;
- application-wide security guarantees;
- comprehensive Semgrep accuracy measurement;
- generalization beyond the controlled JavaScript/Express sample.

## Residual risks

- Endpoint-specific payloads can miss variants outside the test design.
- Reflected-XSS checks do not execute JavaScript in a browser.
- Controlled rules can overfit a benchmark.
- A small number of attempts cannot estimate broad model performance.
- Human adjudication can still be mistaken despite complete evidence.

