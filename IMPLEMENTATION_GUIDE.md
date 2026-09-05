# FixProof historical implementation notes

This preserves the development and pilot checkpoints through September 4,
2026. Its task lists, counts, and "next step" statements describe those
checkpoints, not the current backlog. Do not use them as instructions to
repeat experiments or overwrite recorded evidence.

For current work, read [prototype status](docs/prototype-status.md), the
[documentation index](docs/README.md), and the
[submission guide](docs/cs6727-submission-guide.md). The primary report and
dashboard, pending primary review packets, and four-state lifecycle tracking
were added after the frozen study. Human conclusions and final course
deliverables remain separate work.

## 1. Historical handoff point (September 4, 2026)

September 4, 2026 review: the detailed case history below describes the pilot.
All 15 initial primary-v1 attempts are also recorded in
`data/primary_trials/v1/`: five ready for human review, ten requiring
adjudication, and zero observed SAST false successes. The current report,
dashboard, and adjudication defaults still select the four-attempt pilot.
Read [the CS6727 alignment review](docs/cs6727-alignment-review.md) and
[submission guide](docs/cs6727-submission-guide.md) before planning next work.

```text
CWE-79:
attempts 1 and 2 complete

CWE-89:
attempt 1 complete
controlled-rule provenance preserved
security and functional validation pass
rule-v2 target SAST resolved
READY_FOR_HUMAN_REVIEW

CWE-22:
attempt 1 complete
default Semgrep provenance preserved
security and functional validation pass
SAST/runtime disagreement sent to human adjudication

PILOT EVALUATION:
manifest-driven report builder implemented
3 cases / 4 attempts selected
validated-candidate outcome observed in a pilot AI attempt
false-success outcome demonstrated by a separated non-AI control
selected adjudications completed 2/2
JSON metrics and Markdown matrix generated
read-only evaluation dashboard implemented
reproducibility verification/serve command implemented
controlled demo/operator command implemented for all three cases
architecture and methodology documentation completed
```

Use `data/evaluation/experiment-manifest.json` as the authority for selected
pilot attempts. Use the separate primary manifest and attempt records for the
15 primary observations. The narrowed core workflow is implemented, but
primary reporting/review integration, ten primary disagreement reviews,
explicit resolution of the original reopened-tracking and application-origin
commitments, fresh-install verification, and course deliverables remain.
Preserve the frozen primary implementation and evidence; document later
changes without rewriting the recorded study.

---

## 2. Environment

Repository root on the development machine:

```text
C:\Users\Tony Tran\Documents\fixproof
```

Use the Python virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="src"
```

Verified development versions included Python 3.11.9, OpenAI Python SDK 3.3.1, and Pydantic 2.13.4.

The OpenAI API key is provided through `OPENAI_API_KEY`. The remediation CLI
can load it once from the repository-local `.env`; that file is ignored by
version control and the dashboard allowlist. `src/fixproof/config.py` accepts
only `OPENAI_API_KEY` and `FIXPROOF_MODEL`, ignores blank values, and never
overrides an existing shell environment variable. `.env.example` is the safe
committable template. Never place a real key in code, documentation, generated
artifacts, or committed files. The model can also be supplied through
`FIXPROOF_MODEL` or the `--model` CLI option.

---

## 3. Scanner runner

File:

```text
src/fixproof/scanners/semgrep_runner.py
```

Existing important behavior:

- launches Semgrep with `subprocess.run`;
- does not capture CLI output because Windows Unicode CLI output previously caused decoding failures;
- accepts Semgrep return codes 0 and 1;
- checks that the JSON result file exists.

### Implemented combined configuration

Combine default Semgrep scanning with repository-local FixProof rules:

```text
semgrep scan
--config auto
--config <repo>/rules
--json
--output <output>
<target>
```

The public helper remains compatible with existing callers:

```python
run_semgrep(target, output)
```

The implementation accepts optional `project_rule_dir` and `additional_configs`; existing callers continue to work without modification.

Do not replace default Semgrep rules with only the custom rule pack.

---

## 4. Scanner parser

File:

```text
src/fixproof/scanners/semgrep_parser.py
```

Current responsibilities:

- parse raw Semgrep JSON;
- normalize scanner/rule/CWE metadata;
- resolve source files;
- extract source snippets;
- generate MVP `FP-*` IDs;
- write normalized output.

Current IDs are location-sensitive and may change when patches move source lines.

### Implemented rule provenance

Raw custom rules contain:

```json
"metadata": {
  "fixproof_controlled_rule": true
}
```

The parser assigns:

```python
rule_origin = (
    "fixproof_controlled"
    if metadata.get("fixproof_controlled_rule") is True
    else "semgrep_oss"
)
```

The normalized field is stored on each finding and preserved by `finding_correlator.py`, the context builder, prompt inputs, and evaluation report.

Reason: final evaluation must distinguish default scanner detections from project-controlled evaluation rules.

---

## 5. Finding correlation

File:

```text
src/fixproof/findings/finding_correlator.py
```

Current MVP correlation key:

```text
(file, CWE, start_line)
```

Canonical IDs use `CF-*` hashes.

The correlator preserves multiple rule evidence records instead of dropping duplicates and retains `rule_origin` on those evidence records.

Do not redesign correlation unless necessary for the evaluation. Cross-version comparison is handled separately by the validation runner.

---

## 6. Context builder

File:

```text
src/fixproof/agent/context_builder.py
```

Current behavior:

- maps file suffixes to languages;
- recognizes Express routes;
- searches upward from the finding line to the enclosing route;
- brace-counts to determine route end;
- emits `context_type: express_route` when possible;
- otherwise emits a `line_window`.

For the SQLi benchmark, verify the final CWE-89 context includes all of:

```text
req.query.username
query construction
db.all(query, ...)
```

If the full `/user` route is already captured, do not add unnecessary SQL-specific context logic.

---

## 7. Prompt builder

File:

```text
src/fixproof/agent/prompt_builder.py
```

Prompt artifacts are written to `data/prompts/`.

The prompt tells the remediation model to make one minimal candidate patch, preserve behavior, avoid unrelated changes, avoid scanner suppression, avoid new weaknesses, and not validate itself.

Required structured fields:

```json
{
  "canonical_id": "...",
  "analysis": "...",
  "remediation_strategy": "...",
  "patched_code": "...",
  "assumptions": [],
  "needs_additional_context": false
}
```

Ground truth must never be added to the prompt.

---

## 8. Remediation agent

File:

```text
src/fixproof/agent/remediation_agent.py
```

Current behavior:

- loads one matching canonical prompt;
- calls the OpenAI API;
- requests structured Pydantic output;
- checks returned canonical ID;
- writes the candidate JSON to `data/remediations/`;
- does not apply the candidate to the baseline source.

The current experiment model is configurable and was set to `gpt-5.2` during the documented XSS attempts. Do not hard-code a model name into core logic.

---

## 9. Patch workspace

File:

```text
src/fixproof/patches/patch_workspace.py
```

The current version supports:

```text
workspaces/<canonical-id>/attempt-XX/
```

It copies the benchmark app while ignoring `node_modules`, `.git`, and caches, replaces exactly one original source context, creates a unified diff, and records SHA-256 hashes.

`workspace.json` records:

```text
canonical ID
attempt number
original source
workspace source
patch file
remediation file
model
response ID
original source SHA-256
candidate source SHA-256
patch SHA-256
original_modified = false
```

Never overwrite the baseline application.

---

## 10. Preliminary validation

File:

```text
src/fixproof/validation/validation_runner.py
```

Stages:

```text
1. JavaScript syntax via node --check
2. candidate Semgrep scan
3. normalize + correlate
4. baseline/candidate semantic comparison
```

The semantic comparison avoids line-sensitive `CF-*` IDs. For Express routes it currently uses:

```text
filename|CWE|express:<method>:<route>
```

Example:

```text
app.js|CWE-79|express:get:/hello
```

This correctly tracked the XSS target after patch lines moved.

---

## 11. CWE-79 security validator

File:

```text
src/fixproof/validation/security_validator.py
```

Current scope: controlled reflected XSS only.

It discovers the route and query parameter from context, launches the candidate on port 3000, reuses baseline `node_modules` through `NODE_PATH`, sends controlled XSS payloads, checks the reflected user-controlled region, stores evidence, and stops the process.

Current payload set includes script tags, event-handler markup, quote/SVG payloads, and adjacent markup characters.

Limitation: no browser/JavaScript execution. Preserve this limitation in the final report.

---

## 12. Functional validator

File:

```text
src/fixproof/validation/functional_validator.py
```

The validator verifies response semantics. It extracts the reflected user value, HTML-decodes it, and compares it to the expected input.

This is what detected Attempt 1's `undefined` regression for adjacent special characters.

---

## 13. Decision engine

File:

```text
src/fixproof/validation/decision_engine.py
```

Current policy:

```text
0.2-evidence-aware
```

### REJECT

Use when there is a concrete failure: syntax, new SAST findings, security failure/inconclusive result, or functional regression.

### READY_FOR_HUMAN_REVIEW

Requires:

```text
syntax pass
target SAST resolved
new findings = 0
security pass
functional pass
```

### NEEDS_HUMAN_ADJUDICATION

Requires:

```text
syntax pass
target SAST persistent
new findings = 0
security pass
functional pass
```

This policy prevents automatic retries that only optimize code to silence a scanner.

---

## 14. Retry prompt builder

File:

```text
src/fixproof/agent/retry_prompt_builder.py
```

A rejected attempt can produce a retry prompt containing:

- original remediation task;
- previous candidate;
- syntax result;
- target SAST status;
- new findings;
- targeted security result;
- functional result;
- failed functional test evidence;
- decision classification;
- reason codes;
- evidence conflict.

The AI is not given a manual diagnosis or prewritten correct patch.

---

## 15. Completed XSS experiment

### Baseline

Target:

```text
CF-ffcaa5bd5497
CWE-79
GET /hello
```

### Attempt 1

Results:

```text
syntax                 pass
target SAST            persistent
new SAST findings      0
security               pass (4/4)
functional             fail (4/6)
decision               REJECT
```

Two inputs were corrupted to `undefined` because the model's regex grouped adjacent special characters.

### Attempt 2

Generated from Attempt 1 validation evidence.

Results:

```text
syntax                 pass
target SAST            persistent
new SAST findings      0
security               pass (4/4)
functional             pass (6/6)
classification         sast_runtime_disagreement
decision               NEEDS_HUMAN_ADJUDICATION
retry_allowed           false
```

Do not generate Attempt 3 automatically for this case.

---

## 16. SQL injection benchmark

Application:

```text
sample_apps/vulnerable-sqli-app/app.js
```

Dependencies:

```text
express
sqlite3
```

The app uses an in-memory database seeded with:

```text
alice / user
bob / admin
charlie / user
```

Vulnerable route:

```text
GET /user?username=<value>
```

Data flow:

```text
req.query.username
   -> username
   -> concatenated SQL query
   -> db.all(query, ...)
```

### Ground-truth runtime proof

Normal:

```powershell
Invoke-RestMethod "http://127.0.0.1:3000/user?username=alice"
```

returns one row.

Injection:

```powershell
Invoke-RestMethod "http://127.0.0.1:3000/user?username=%27%20OR%20%271%27%3D%271"
```

returns all three rows.

Therefore SQL injection is confirmed independently from SAST.

---

## 17. SQLi scanner results

Default Semgrep CE/OSS preparation scan detected only:

```text
CWE-352 CSRF
```

It did not detect CWE-89.

This is a recorded scanner miss, not a reason to modify the benchmark.

---

## 18. Controlled SQLi rule

File:

```text
rules/fixproof-sqli.yml
```

Working rule:

```yaml
rules:
  - id: fixproof.javascript.sqlite3.sql-injection
    mode: taint

    languages:
      - javascript

    message: >
      User-controlled Express query input reaches a SQLite query
      execution function. Use parameterized SQL instead of constructing
      SQL with untrusted input.

    severity: ERROR

    metadata:
      cwe: "CWE-89"
      category: security
      confidence: HIGH
      impact: HIGH
      likelihood: HIGH
      fixproof_controlled_rule: true

    pattern-sources:
      - pattern: req.query.$PARAM

    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: db.all($QUERY, ...)
              - pattern: db.get($QUERY, ...)
              - pattern: db.run($QUERY, ...)
              - pattern: db.exec($QUERY, ...)
          - focus-metavariable: $QUERY
```

Direct test:

```powershell
semgrep `
  --config rules\fixproof-sqli.yml `
  --json `
  --output data\raw_scans\vulnerable-sqli-rule-test-02.json `
  sample_apps\vulnerable-sqli-app\app.js
```

Observed:

```text
Findings: 1
CWE-89
severity ERROR
confidence HIGH
```

The first more generic rule attempt returned zero findings. The literal `req`/`db` benchmark rule is therefore intentionally narrow. Revision v2 focuses the sink on `$QUERY`, which preserves the vulnerable-baseline detection but stops treating a safely bound parameter array as SQL text. Document it as a controlled evaluation rule, not a general SQLi detector.

---

## 19. Completed implementation state

The controlled-rule integration, rule-provenance propagation, SQLi workflow, and CWE-22 path-traversal workflow are complete. The selected experiment now contains three cases and four remediation attempts:

```text
XSS             attempts 1 and 2
SQL injection   attempt 1
Path traversal  attempt 1
```

Each selected attempt has remediation, isolated workspace, preliminary SAST comparison, targeted security validation, functional validation, and deterministic decision artifacts.

---

## 20. Evaluation/reporting workflow

The report builder aggregates only the attempts explicitly selected by:

```text
data/evaluation/experiment-manifest.json
```

This is required because historical artifacts may have legacy names or superseded policy outputs. The manifest is the authority for which decision belongs to each attempt.

Run:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.report_builder
```

The builder validates cross-artifact canonical IDs, checks decision evidence against the underlying validation artifacts, recomputes the experiment labels, verifies retry lineage, and writes:

```text
data/evaluation/experiment-report.json
docs/evaluation-report.md
```

The JSON report includes selected artifact paths and SHA-256 digests. The Markdown report includes the final matrix, aggregate metrics, retry analysis, provenance notes, and interpretation limits.

### Human adjudication boundary

Generate or verify pending packets with:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.adjudication init
```

Packets are immutable evidence bundles under `data/adjudications/`. A packet binds the selected decision, validation artifacts, remediation, workspace, candidate-source hash, and patch hash. Running `init` is idempotent for unchanged evidence and refuses to overwrite a stale packet.

JSON artifact digests are byte-exact SHA-256 values. Historical workspace candidate and patch hashes use normalized UTF-8 text so their meaning remains stable across Windows CRLF and LF line endings; each packet records this hash mode explicitly.

Human conclusions are separate `adjudication_result` artifacts. Use:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.adjudication record --help
```

Do not ask the remediation model or another AI step to supply the human verdict. The reviewer must inspect all evidence, choose an allowed verdict, provide a rationale, and confirm the required checklist. Then add the result path as `adjudication_result` in the corresponding experiment-manifest entry and regenerate the report.

Current status:

```text
original disagreement reviews completed: 3/3
adjudications required by current authoritative matrix: 2
current selected adjudications completed: 2/2
verdict: ACCEPT_CANDIDATE for both selected disagreements
```

The earlier SQLi disagreement adjudication remains preserved, but rule-v2 revalidation moved the same AI candidate to `READY_FOR_HUMAN_REVIEW`. It is therefore historical evidence rather than a currently selected adjudication requirement.

---

## 21. Artifact naming

Use attempt-aware naming going forward:

```text
data/remediations/<CF-ID>-attempt-01.json
data/validation/<CF-ID>-attempt-01.json
data/security_validation/<CF-ID>-attempt-01.json
data/functional_validation/<CF-ID>-attempt-01.json
data/decisions/<CF-ID>-attempt-01.json
data/adjudications/<CF-ID>-attempt-01-packet.json
data/adjudications/<CF-ID>-attempt-01-result.json
```

Existing XSS Attempt 1 artifacts without the suffix should be preserved rather than renamed destructively.

---

## 22. Evaluation metrics

Useful deterministic metrics:

```text
SAST remediation success rate
targeted security validation pass rate
functional preservation rate
security regression/new finding rate
SAST false-success count
SAST/runtime disagreement count
retry improvement rate
human adjudication rate
human adjudication completion rate
```

False success definition:

```text
target SAST = resolved
AND
(security != pass OR functional != pass OR new findings > 0)
```

Do not classify XSS Attempt 1 as false success because its target SAST finding remained persistent.

The selected primary AI attempts contain one `validated_candidate` outcome but no organic AI false-success. A deterministic non-AI XSS static-output control exercises `sast_false_success` end to end. It must remain labeled `outcome_coverage_only` and excluded from primary AI-attempt metrics.

### Read-only evaluation dashboard

After regenerating the report, launch:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.dashboard
```

Then open `http://127.0.0.1:8080/ui/`. The dashboard consumes only `data/evaluation/experiment-report.json`. It is intentionally read-only and exposes only dashboard assets plus that report through the local HTTP server. It must not gain remediation-generation, adjudication, deployment, authentication, or database responsibilities for the CS6727 scope.

### Reproducibility gate

Run the final deterministic verification with the project interpreter:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.reproduce --verify
```

This command regenerates the JSON and Markdown reports, verifies primary-AI
and non-AI-control separation, confirms required outcome and decision-state
coverage, checks completed adjudications and SHA-256 artifact bindings, and
runs all unit tests. It does not rerun the scanner or remediation model.

Verify and serve the dashboard in one command with:

```powershell
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

Do not use a bare `python` command when the system interpreter differs from
`.venv`.

### Controlled demonstration runner

The safe presentation entry point is:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.demo `
  --case sqli `
  --validate `
  --serve
```

`src/fixproof/demo.py` selects only authoritative AI attempts from the
experiment manifest, reruns runtime validators into a unique `TEMP` directory,
recomputes the decision, requires it to match the recorded classification and
disposition, verifies dashboard freshness/readiness, and then serves the
read-only UI. It does not rerun preliminary SAST, call the model, or overwrite
experiment artifacts.

Supported selections are `sqli`, `xss`, and `path-traversal`. XSS defaults to
Attempt 2; `--attempt 1` exercises the rejected functional-regression outcome.
See `docs/demo-guide.md` for the presentation script and scope statement.

---

## 23. Methodology to preserve

For every benchmark:

```text
1. Establish ground truth independently.
2. Record default scanner behavior.
3. Add labeled controlled rules only if needed.
4. Normalize/correlate scanner evidence.
5. Give scanner evidence + source context to the model, not ground truth.
6. Save the model output unchanged.
7. Apply only in an isolated workspace.
8. Run syntax/build validation.
9. Run SAST comparison.
10. Run targeted security validation.
11. Run functional/regression validation.
12. Compute deterministic disposition.
13. Retry only when policy permits.
14. Require human review/adjudication.
```

---

## 24. Known limitations

Current limitations are acceptable for the practicum and should be documented:

- JavaScript/Express focused;
- Semgrep CE/OSS;
- custom SQLi rule is benchmark-oriented and identifier-specific;
- XSS security validator is endpoint/context specific;
- no browser-based XSS execution;
- filesystem workspaces are isolation-by-copy, not hardened containers;
- functional tests are controlled benchmark tests;
- canonical fingerprinting remains MVP-level.

Do not hide these limitations and do not attempt to solve all of them before completing the evaluation.

---

## 25. Scope guardrails

Avoid turning the project into:

- a full SAST replacement;
- a full DAST platform;
- a production CI/CD deployment engine;
- a multi-language remediation platform;
- a Semgrep accuracy research project;
- an autonomous system that deploys without human approval.

The CS6727 value is the validation-oriented security-remediation workflow and its measured outcomes.
