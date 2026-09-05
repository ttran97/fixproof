# FixProof primary-v1 results

Generated from verified recorded evidence; no model or runtime tests are rerun.

| Trial | Target SAST | Security | Functional | Decision | Human review |
|---|---|---|---|---|---|
| primary-v1-xss-initial-01 | persistent | 4/4 | 6/6 | NEEDS_HUMAN_ADJUDICATION | completed |
| primary-v1-xss-initial-02 | persistent | 4/4 | 6/6 | NEEDS_HUMAN_ADJUDICATION | completed |
| primary-v1-xss-initial-03 | persistent | 4/4 | 6/6 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-xss-initial-04 | persistent | 4/4 | 6/6 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-xss-initial-05 | persistent | 4/4 | 6/6 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-sqli-initial-01 | resolved | 2/2 | 3/3 | READY_FOR_HUMAN_REVIEW | not_required |
| primary-v1-sqli-initial-02 | resolved | 2/2 | 3/3 | READY_FOR_HUMAN_REVIEW | not_required |
| primary-v1-sqli-initial-03 | resolved | 2/2 | 3/3 | READY_FOR_HUMAN_REVIEW | not_required |
| primary-v1-sqli-initial-04 | resolved | 2/2 | 3/3 | READY_FOR_HUMAN_REVIEW | not_required |
| primary-v1-sqli-initial-05 | resolved | 2/2 | 3/3 | READY_FOR_HUMAN_REVIEW | not_required |
| primary-v1-path-traversal-initial-01 | persistent | 2/2 | 3/3 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-path-traversal-initial-02 | persistent | 2/2 | 3/3 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-path-traversal-initial-03 | persistent | 2/2 | 3/3 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-path-traversal-initial-04 | persistent | 2/2 | 3/3 | NEEDS_HUMAN_ADJUDICATION | pending |
| primary-v1-path-traversal-initial-05 | persistent | 2/2 | 3/3 | NEEDS_HUMAN_ADJUDICATION | pending |

## Primary metrics

All rates use the 15 scheduled initial attempts; pilot and control evidence are separate.

- valid_candidate_generation_application: 15/15 (100.0%).
- sast_remediation_success: 5/15 (33.3%).
- targeted_security_pass: 15/15 (100.0%).
- functional_preservation: 15/15 (100.0%).
- new_finding: 0/15 (0.0%).
- sast_only_apparent_success: 5/15 (33.3%).
- sast_false_success: 0/15 (0.0%).
- sast_runtime_disagreement: 10/15 (66.7%).

Conflict reviews completed: **2/10**. Ready for human review does not mean human approval.

Distinct candidate sources per case: {'xss': 5, 'sqli': 1, 'path-traversal': 5}.

Observed primary SAST false successes: 0. Pilot and non-AI control outcomes must be discussed separately.

Primary retry improvement is not applicable when no initial primary candidate is rejected. This report contains initial attempts only.

## Limits

- One application per CWE; repeated prompts are not independent applications.
- Passing targeted tests is not proof of application-wide security.
- Default Semgrep auto rule definitions were not fully archived.
- Pilot attempts, retry, and non-AI control are excluded from primary rates.
- Evidence verification does not perform or attest human review.
