# FixProof Experiment Evaluation Report

This report is generated deterministically from the authoritative attempt manifest `data/evaluation/experiment-manifest.json`. Rates use the remediation attempt as the aggregation unit.

## Experiment matrix

| Case | CWE | Attempt | SAST | Security | Functional | New findings | Decision |
|---|---:|---:|---|---|---|---:|---|
| XSS | 79 | 1 | Persistent | Pass (4/4) | Fail (4/6) | 0 | Reject |
| XSS | 79 | 2 | Persistent | Pass (4/4) | Pass (6/6) | 0 | Human adjudication |
| SQLi | 89 | 1 | Resolved | Pass (2/2) | Pass (3/3) | 0 | Ready for human review |
| Path traversal | 22 | 1 | Persistent | Pass (2/2) | Pass (3/3) | 0 | Human adjudication |

## Outcome-coverage controls

These deterministic non-AI controls exercise missing policy outcomes and are excluded from every primary AI-attempt metric.

| Control | Origin | SAST | Security | Functional | Classification | Decision |
|---|---|---|---|---|---|---|
| XSS static-output control | deterministic_non_ai | Resolved | Inconclusive | Fail | `sast_false_success` | Reject |

| Required outcome | Primary AI attempt | Non-AI control | Covered |
|---|---|---|---|
| `validated_candidate` | Yes | No | Yes |
| `sast_false_success` | No | Yes | Yes |

## Aggregate metrics

| Metric | Result |
|---|---:|
| SAST remediation success rate | 1/4 (25.0%) |
| Targeted security validation pass rate | 4/4 (100.0%) |
| Functional preservation rate | 3/4 (75.0%) |
| Security regression/new finding rate | 0/4 (0.0%) |
| Retry improvement rate | 1/1 (100.0%) |
| Human adjudication rate | 2/4 (50.0%) |
| Human adjudication completion rate | 2/2 (100.0%) |
| SAST false-success count | 0 |
| SAST/runtime disagreement count | 2 |

A false success requires the target SAST finding to be resolved while at least one downstream validation condition fails. A persistent target is therefore not counted as a false success.

## Retry analysis

| Case | From | To | Improved | Improved dimensions | Worsened dimensions |
|---|---:|---:|---|---|---|
| XSS | 1 | 2 | Yes | functional_validation | None |

## Human adjudication

Human adjudication records a separate human conclusion and does not replace the automated decision.

| Case | Attempt | Status | Verdict | Packet |
|---|---:|---|---|---|
| XSS | 2 | Completed | ACCEPT_CANDIDATE | `data/adjudications/CF-ffcaa5bd5497-attempt-02-packet.json` |
| Path traversal | 1 | Completed | ACCEPT_CANDIDATE | `data/adjudications/CF-bc4a65bafb2d-attempt-01-packet.json` |

## Evidence revisions

| Case | Attempt | Revision | Historical adjudication | Reason |
|---|---:|---|---|---|
| SQLi | 1 | `controlled-sqli-rule-v2` | ACCEPT_CANDIDATE by Tony Tran | The sink was narrowed to the SQL query argument so safely bound parameter values are not treated as query text. |

Historical decisions and adjudications remain preserved with SHA-256 digests in the machine-readable report.

## Evidence provenance

| Case | Attempt | Rule origin | Policy | Decision artifact |
|---|---:|---|---|---|
| XSS | 1 | unrecorded | 0.1-strict | `data/decisions/CF-ffcaa5bd5497.json` |
| XSS | 2 | unrecorded | 0.2-evidence-aware | `data/decisions/CF-ffcaa5bd5497-attempt-02-policy-02.json` |
| SQLi | 1 | fixproof_controlled | 0.2-evidence-aware | `data/decisions/CF-345f0ac3d7ae-attempt-01-rule-v2.json` |
| Path traversal | 1 | semgrep_oss | 0.2-evidence-aware | `data/decisions/CF-bc4a65bafb2d-attempt-01.json` |

Rule provenance is recorded for 2/4 selected attempts. The historical XSS baseline uses the pre-provenance schema, so its rule origin is reported as `unrecorded` rather than inferred.

The machine-readable report records every selected artifact path and SHA-256 digest so the matrix can be audited against its inputs.

## Interpretation limits

- These rates describe a small, controlled benchmark and should not be generalized to production remediation performance.
- Targeted runtime tests establish behavior for the tested endpoint and payloads, not application-wide security.
- A SAST/runtime disagreement is escalated for human adjudication; it is not an automatic approval.
