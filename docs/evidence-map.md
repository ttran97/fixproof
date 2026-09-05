# FixProof Pilot Evidence Map

Current primary entry points: [verified primary results](primary-results.md),
[prototype status](prototype-status.md), and [human review guide](primary-review-guide.md).

This map covers the four-attempt **pilot** and its separate non-AI control.
The completed 15-attempt primary-v1 study is under `data/primary_trials/v1/`.
See [current prototype status](prototype-status.md) for its verified
results and remaining primary human reviews, and the
[submission guide](cs6727-submission-guide.md) for the repository walkthrough.

## What this map proves

FixProof does not claim that the AI model performed or judged the validation.
It shows that each recorded AI candidate was passed through independently
implemented SAST comparison, targeted runtime-security testing,
functional-regression testing, and deterministic policy evaluation.

The authoritative selection is
`data/evaluation/experiment-manifest.json`. The generated digest-bearing view is
`data/evaluation/experiment-report.json`.

## Reviewer starting points

| Question | Evidence |
|---|---|
| Are the baseline applications deliberately vulnerable? | `data/ground_truth/` and the three `sample_apps/` directories |
| What did Semgrep report before remediation? | `data/raw_scans/`, followed by `data/normalized/` and `data/correlated/` |
| What information did the model receive? | `data/contexts/` and `data/prompts/` |
| Is this an actual recorded AI response? | `data/remediations/` contains the model name, response ID, candidate, and assumptions |
| Was the baseline kept unchanged? | Selected `workspaces/**/workspace.json` files record source and patch hashes plus `original_modified` |
| Was the candidate rescanned? | `data/validation/` contains syntax, candidate SAST, semantic target comparison, and new findings |
| Were exploit behaviors tested? | `data/security_validation/` contains payloads, responses, criteria, and per-test results |
| Were regressions tested independently? | `data/functional_validation/` contains expected behavior and per-test results |
| How was the final state chosen? | `data/decisions/` records policy version, reason codes, classification, and disposition |
| How was conflicting evidence handled? | `data/adjudications/` contains immutable packets and separate human conclusions |

## Selected AI-attempt matrix

| Case | Attempt | Candidate | Candidate SAST | Security | Functional | Decision |
|---|---:|---|---|---|---|---|
| XSS / CWE-79 | 1 | `data/remediations/CF-ffcaa5bd5497.json` | `data/validation/CF-ffcaa5bd5497.json` | 4/4 pass | 4/6 pass | `REJECT` |
| XSS / CWE-79 | 2 | `data/remediations/CF-ffcaa5bd5497-attempt-02.json` | `data/validation/CF-ffcaa5bd5497-attempt-02.json` | 4/4 pass | 6/6 pass | `NEEDS_HUMAN_ADJUDICATION` |
| SQLi / CWE-89 | 1 | `data/remediations/CF-345f0ac3d7ae-attempt-01.json` | `data/validation/CF-345f0ac3d7ae-attempt-01-rule-v2.json` | 2/2 pass | 3/3 pass | `READY_FOR_HUMAN_REVIEW` |
| Path traversal / CWE-22 | 1 | `data/remediations/CF-bc4a65bafb2d-attempt-01.json` | `data/validation/CF-bc4a65bafb2d-attempt-01.json` | 2/2 pass | 3/3 pass | `NEEDS_HUMAN_ADJUDICATION` |

Across the four selected AI attempts, the retained results contain 12 targeted
security-test executions and 18 functional-test executions. These 30 checks
are attempt-level evidence, not 30 independent applications or vulnerability
classes.

## Case-specific walkthroughs

### Reflected XSS

1. Baseline: `sample_apps/vulnerable-js-app/app.js`
2. Ground truth: `data/ground_truth/vulnerable-js-app.json`
3. Raw scan: `data/raw_scans/vulnerable-js-app.json`
4. Model inputs: `data/contexts/vulnerable-js-app.json` and
   `data/prompts/vulnerable-js-app.json`
5. Attempt 1 shows why security-only success is insufficient: all four
   security cases pass, but two functional cases fail.
6. Retry evidence: `data/retry_prompts/CF-ffcaa5bd5497-attempt-02.json`
7. Attempt 2 restores all functional cases while leaving a SAST/runtime
   disagreement for human adjudication.
8. Review packet/result:
   `data/adjudications/CF-ffcaa5bd5497-attempt-02-*.json`

### SQL injection

1. Baseline: `sample_apps/vulnerable-sqli-app/app.js`
2. Ground truth: `data/ground_truth/vulnerable-sqli-app.json`
3. Default scanner behavior is preserved as a miss; the controlled rule is
   clearly labeled in `rules/fixproof-sqli.yml` and subsequent artifacts.
4. Selected rule-v2 baseline:
   `data/correlated/vulnerable-sqli-app-rule-v2.json`
5. The candidate uses a parameterized SQLite query.
6. Candidate SAST resolves, both runtime layers pass, and the result becomes
   ready for human review.

### Path traversal

1. Baseline: `sample_apps/vulnerable-path-traversal-app/app.js`
2. Fixtures: `public-files/welcome.txt`, `public-files/guide.txt`, and the
   intentionally outside `outside-secret.txt`
3. Ground truth: `data/ground_truth/vulnerable-path-traversal-app.json`
4. The candidate passes two traversal-security cases and three functional
   cases, but the SAST target persists.
5. The disagreement is retained rather than converted into an automatic
   success; the human packet and result are under `data/adjudications/`.

## Live demonstration

For a concise demonstration of the validated path:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Case sqli
```

For all controlled case and decision sets:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
```

The CLI labels recorded and newly executed evidence. Live outputs are written
to a disposable temporary directory and do not replace the authoritative
experiment.
