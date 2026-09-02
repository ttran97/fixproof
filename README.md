# FixProof

**FixProof: A Validation-Oriented Agentic Security System for AI-Generated Vulnerability Remediation**

FixProof is a Georgia Tech CS6727 Cyber Security Practicum prototype that evaluates AI-generated security remediations before a human approves them.

The core premise is:

> A SAST finding disappearing does not prove that a vulnerability was fixed correctly.

FixProof therefore treats SAST as one source of evidence and independently checks candidate patches with syntax/build validation, SAST rescanning, targeted security tests, functional/regression tests, and a deterministic decision policy.

## Research question

**Can a multi-stage validation pipeline distinguish AI-generated remediations that appear successful after SAST rescanning but still retain security issues, introduce regressions, or break application functionality?**

A secondary question now supported by the prototype is whether validation feedback can improve a later AI remediation attempt without allowing the model to grade its own work.

## Core design principles

- The remediation model never approves its own patch.
- Ground truth is independent from scanner output.
- SAST is evidence, not ground truth.
- Runtime security and functional validation are separate stages.
- Candidate patches are applied only to isolated workspaces.
- Original vulnerable applications are preserved.
- Conflicting evidence is escalated to a human instead of repeatedly rewriting code only to satisfy a scanner.
- Every remediation attempt should remain auditable and reproducible.

## Architecture

```text
Web Application / Repository
        |
        v
Baseline SAST Scan
        |
        v
Normalize Findings
        |
        v
Correlate / Deduplicate
        |
        v
Build Focused Source Context
        |
        v
Build Deterministic Prompt
        |
        v
AI Remediation Agent
        |
        v
Candidate Patch
        |
        v
Isolated Attempt Workspace
        |
        +-----------------------+
        |                       |
        v                       v
Syntax / Build Check        SAST Rescan
        |                       |
        +-----------+-----------+
                    |
                    v
        Baseline vs Candidate Comparison
                    |
                    v
        Targeted Security Validation
                    |
                    v
        Functional / Regression Validation
                    |
                    v
             Decision Engine
                    |
      +-------------+-------------------+
      |             |                   |
      v             v                   v
   REJECT   READY_FOR_HUMAN_REVIEW   NEEDS_HUMAN_ADJUDICATION
```

## Current project status

### CWE-79 reflected XSS: first prototype path complete

Baseline target: `GET /hello` in `sample_apps/vulnerable-js-app/app.js`.

```javascript
app.get("/hello", (req, res) => {
    const name = req.query.name;
    res.send("<h1>Hello " + name + "</h1>");
});
```

#### Attempt 1

The model generated a manual HTML escaping patch using a regex with `+`:

```javascript
.replace(/[&<>"]+/g, ...)
```

Independent validation produced:

| Validation layer | Result |
|---|---|
| Syntax | PASS |
| Target SAST finding | PERSISTENT |
| New SAST findings | 0 |
| Targeted CWE-79 runtime tests | 4/4 PASS |
| Functional regression tests | 4/6 PASS |
| Decision | REJECT |

The functional validator caught corruption of adjacent special characters, for example:

```text
Expected: Tony &<> Alicia
Actual:   Tony undefined Alicia
```

Decision reason codes:

```text
TARGET_SAST_FINDING_PERSISTENT
FUNCTIONAL_REGRESSION
```

#### Attempt 2

FixProof built a retry prompt from measured validation evidence rather than a manually supplied fix. The model generated character-by-character HTML escaping:

```javascript
.replace(/[&<>"']/g, (ch) => {
    switch (ch) {
        case "&": return "&amp;";
        case "<": return "&lt;";
        case ">": return "&gt;";
        case '"': return "&quot;";
        case "'": return "&#39;";
        default: return ch;
    }
});
```

Attempt 2 produced:

| Validation layer | Result |
|---|---|
| Syntax | PASS |
| Target SAST finding | PERSISTENT |
| New SAST findings | 0 |
| Targeted CWE-79 runtime tests | 4/4 PASS |
| Functional regression tests | 6/6 PASS |
| Classification | `sast_runtime_disagreement` |
| Decision | `NEEDS_HUMAN_ADJUDICATION` |
| Retry allowed | `false` |

This prevents the system from endlessly changing otherwise functional code only to make Semgrep quiet.

### CWE-89 SQL injection: current work

A separate controlled application exists at:

```text
sample_apps/vulnerable-sqli-app/
```

The route uses an actual SQLite execution sink:

```javascript
const username = req.query.username;

const query =
    "SELECT id, username, role FROM users " +
    "WHERE username = '" +
    username +
    "'";

db.all(query, (err, rows) => {
    ...
});
```

Runtime ground truth was confirmed:

```powershell
Invoke-RestMethod "http://127.0.0.1:3000/user?username=alice"
```

returns Alice only, while:

```powershell
Invoke-RestMethod "http://127.0.0.1:3000/user?username=%27%20OR%20%271%27%3D%271"
```

returns Alice, Bob, and Charlie. The decoded payload is:

```text
' OR '1'='1
```

Default Semgrep CE/OSS did **not** detect CWE-89 in this benchmark. It reported only CWE-352 CSRF. This scanner miss is intentionally preserved as evaluation evidence.

A controlled local rule was added at:

```text
rules/fixproof-sqli.yml
```

The working direct rule test reports one CWE-89 finding. The raw custom rule metadata contains:

```json
"fixproof_controlled_rule": true
```

The controlled rule is now integrated with the normal scanner pipeline, and rule provenance is preserved through normalization, correlation, prompt context, and evaluation reporting. Rule revision v2 focuses the taint sink on the SQL query argument, so it still detects the vulnerable concatenated query without treating a safely bound parameter value as SQL text. The existing AI-generated parameterized candidate now resolves CWE-89 and reaches `READY_FOR_HUMAN_REVIEW` while the original evidence and adjudication remain preserved as history.

## Repository layout

```text
fixproof/
|-- README.md
|-- IMPLEMENTATION_GUIDE.md
|-- pyproject.toml
|-- data/
|   |-- ground_truth/, raw_scans/, normalized/, and correlated/
|   |-- contexts/, prompts/, retry_prompts/, and remediations/
|   |-- validation/, security_validation/, and functional_validation/
|   |-- decisions/ and adjudications/
|   `-- evaluation/ and evaluation_controls/
|-- docs/
|   |-- architecture.md, methodology.md, and evaluation-report.md
|   |-- demo-guide.md and evidence-map.md
|   `-- related-work.md, threat-model.md, artifact-schema.md,
|       and reproducibility.md
|-- rules/
|-- sample_apps/
|   |-- vulnerable-js-app/
|   |-- vulnerable-sqli-app/
|   `-- vulnerable-path-traversal-app/
|-- scripts/
|-- src/fixproof/
|   |-- agent/, scanners/, findings/, and patches/
|   |-- validation/
|   `-- evaluation/
|-- tests/
|-- ui/
`-- workspaces/  (curated evidence files plus ignored disposable content)
```

## Environment setup

Use Python 3.11 in a virtual environment. The editable install uses the pinned
versions in `pyproject.toml`, including the Semgrep version recorded by the
pilot scans:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

The editable install handles the `src/` layout. If you intentionally run
without installing the project, set this in each new PowerShell session:

```powershell
$env:PYTHONPATH="src"
```

For one-time local setup, open the ignored `.env` file:

```powershell
notepad .env
```

Set its values locally:

```dotenv
OPENAI_API_KEY=replace-with-a-new-project-key
FIXPROOF_MODEL=gpt-5.2
```

The remediation CLI automatically finds the nearest `.env`, loads only
`OPENAI_API_KEY` and `FIXPROOF_MODEL`, and then lets the OpenAI SDK read the key
from the process environment. A shell environment variable or explicit
`--model` takes precedence. Use `--env-file` only when a different local file is
required.

`.env` is ignored by version control and is not exposed by the dashboard. It is
still plaintext on the local machine, so never share, record, or commit it. The
committable `.env.example` contains blank placeholders. Do not reuse a key that
has previously been exposed.

For JavaScript benchmark apps, restore the exact locked dependencies inside
each app directory. Example:

```powershell
Push-Location sample_apps\vulnerable-sqli-app
npm ci
Pop-Location
```

Research and audit starting points:

- [Evaluation methodology](docs/methodology.md)
- [Professor-facing evidence map](docs/evidence-map.md)
- [Threat model](docs/threat-model.md)
- [Artifact contract](docs/artifact-schema.md)
- [Related-work positioning](docs/related-work.md)
- [Clean-environment procedure](docs/reproducibility.md)

## Preparation pipeline

Run:

```powershell
$env:PYTHONPATH="src"
python -m fixproof.scan_pipeline `
  --target sample_apps\vulnerable-js-app\app.js `
  --name vulnerable-js-app
```

Current stages:

```text
[1/4] Semgrep
[2/4] Normalize
[3/4] Correlate
[4/4] Build remediation contexts
```

Artifacts:

```text
data/raw_scans/<name>.json
data/normalized/<name>.json
data/correlated/<name>.json
data/contexts/<name>.json
```

## Finding normalization

`semgrep_parser.py` converts raw Semgrep output into the FixProof schema and extracts source context because Semgrep OSS can return login placeholders for `lines`/fingerprint fields.

Normalized metadata includes scanner/rule information, CWE, severity, confidence, likelihood, impact, message, file, line range, source context, status, and validation state.

Current MVP `FP-*` IDs are location-sensitive, so they are not used alone for cross-version tracking.

### Pending parser change

Preserve scanner rule provenance:

```python
if metadata.get("fixproof_controlled_rule") is True:
    rule_origin = "fixproof_controlled"
else:
    rule_origin = "semgrep_oss"
```

Propagate `rule_origin` into correlated scanner evidence.

## Finding correlation

`finding_correlator.py` currently groups normalized findings by:

```text
file + CWE + start line
```

It preserves every scanner evidence record under one canonical finding rather than silently discarding duplicate rules.

Current canonical IDs use `CF-*` hashes. Do not correlate by CWE alone because separate lines/routes can represent separate vulnerabilities.

## Context builder

`context_builder.py` prefers an enclosing Express route when possible and otherwise falls back to a line window.

Typical route context:

```text
context_type = express_route
```

Ground-truth labels must never be included in source comments or AI context.

## Prompt builder

`prompt_builder.py` creates deterministic remediation prompts and stores them under `data/prompts/` before an API call.

The remediation model is instructed to:

- address one supplied finding;
- preserve intended behavior;
- avoid unrelated changes;
- avoid introducing new weaknesses;
- never suppress/bypass the scanner;
- not remove functionality merely to clear a finding;
- not assume the scanner is automatically correct;
- prefer a minimal patch;
- not validate its own patch.

Structured candidate schema:

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

## Remediation agent

`remediation_agent.py` calls the OpenAI API with structured Pydantic output, checks that the returned canonical ID matches the requested finding, and writes the candidate to `data/remediations/`.

It does not edit the original application.

## Patch workspace

`patch_workspace.py` creates attempt-specific isolated copies:

```text
workspaces/<canonical-id>/attempt-01/
workspaces/<canonical-id>/attempt-02/
```

It produces:

```text
app/
candidate.patch
workspace.json
```

The metadata records attempt number, model, response ID, original/candidate/patch SHA-256 hashes, and confirms the baseline was not modified.

## Preliminary validation

`validation_runner.py` performs:

1. JavaScript syntax check with `node --check`;
2. candidate Semgrep rescan;
3. normalization/correlation;
4. baseline vs candidate comparison.

Cross-version comparison does not rely on line-sensitive `CF-*` IDs. The current Express semantic identity is:

```text
filename|CWE|route
```

Example:

```text
app.js|CWE-79|express:get:/hello
```

## Targeted security validation

`security_validator.py` currently supports the controlled reflected CWE-79 case. It starts the isolated Express candidate, reuses the baseline application's `node_modules` through `NODE_PATH`, sends controlled payloads, inspects the reflected user-controlled region, stores evidence, and stops the app.

Current limitation: it does not execute JavaScript in a browser. Report this as a targeted CWE-79 test, not proof that the full application is secure.

## Functional validation

`functional_validator.py` compares user-visible semantics rather than requiring one exact HTML encoding implementation. It HTML-decodes the reflected value and compares it to the expected input.

This stage detected the Attempt 1 regression.

## Decision engine

Current policy:

```text
0.2-evidence-aware
```

### `REJECT`

Used when a concrete automated validation failure exists, such as syntax failure, new security findings, targeted security failure/inconclusive result, or functional regression.

### `READY_FOR_HUMAN_REVIEW`

Used when:

```text
syntax = pass
target SAST = resolved
new findings = 0
security validation = pass
functional validation = pass
```

The candidate is still not automatically approved.

### `NEEDS_HUMAN_ADJUDICATION`

Used when:

```text
syntax = pass
target SAST = persistent
new findings = 0
security validation = pass
functional validation = pass
```

This captures static/runtime evidence conflict without forcing another automatic retry.

## Retry loop

`retry_prompt_builder.py` feeds measured validation evidence from a rejected attempt back into the remediation model. It includes the previous candidate, syntax/SAST/security/functional outcomes, concrete failed functional cases, decision classification, reason codes, and evidence conflict.

It does not provide a manually authored correct fix.

## Ground truth

Ground truth belongs under:

```text
data/ground_truth/
```

Ground truth is evaluator-only and must not leak into AI prompts, source comments, or scanner assumptions.

## Controlled Semgrep rules

Project-specific rules belong under `rules/` and must supplement, not replace, default scanner evidence.

The working controlled SQLi rule uses a taint source of `req.query.$PARAM`, sinks such as `db.all($QUERY, ...)`, `db.get`, `db.run`, and `db.exec`, and `focus-metavariable: $QUERY` so only tainted SQL text is treated as the sink.

The rule is intentionally labeled with:

```yaml
fixproof_controlled_rule: true
```

## Evaluation reporting

The evaluation layer uses an explicit manifest to select authoritative artifacts. This prevents superseded decisions, such as the original XSS Attempt 2 policy output, from being double-counted. It validates canonical IDs and decision evidence, recomputes metrics from the underlying validation artifacts, and records SHA-256 digests for auditability.

Generate both report formats with:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.report_builder
```

Inputs and outputs:

```text
data/evaluation/experiment-manifest.json   authoritative artifact selection
data/evaluation/experiment-report.json     machine-readable matrix and metrics
docs/evaluation-report.md                  human-readable experiment report
```

## Human adjudication

FixProof creates immutable adjudication packets for automated SAST/runtime disagreements:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.adjudication init
```

All three original disagreement packets have completed reviewer results from Tony Tran with `ACCEPT_CANDIDATE`. Each result remains bound to its immutable packet. After SQLi rule-v2 revalidation, SQLi is now `READY_FOR_HUMAN_REVIEW`; its earlier disagreement adjudication is retained as historical evidence. The two cases that still require adjudication in the authoritative matrix are completed 2/2.

After personally reviewing every bound artifact, a reviewer can inspect the result command and allowed verdicts with:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.adjudication record --help
```

The `record` command requires a reviewer identifier, rationale, verdict, separate output path, and explicit confirmation that all required checks were completed. It never overwrites the packet or changes the automated decision. Add the completed result as `adjudication_result` in the corresponding manifest entry, then regenerate the report.

## Current evaluation matrix

| Case | CWE | Attempt | SAST | Security | Functional | New findings | Decision |
|---|---:|---:|---|---|---|---:|---|
| XSS | 79 | 1 | Persistent | Pass (4/4) | Fail (4/6) | 0 | Reject |
| XSS | 79 | 2 | Persistent | Pass (4/4) | Pass (6/6) | 0 | Human adjudication |
| SQLi | 89 | 1 | Resolved | Pass (2/2) | Pass (3/3) | 0 | Ready for human review |
| Path traversal | 22 | 1 | Persistent | Pass (2/2) | Pass (3/3) | 0 | Human adjudication |

The generated primary AI-attempt metrics are: SAST remediation success 1/4, targeted security validation 4/4, functional preservation 3/4, new-security-finding rate 0/4, false-success count 0, SAST/runtime disagreement count 2, retry improvement 1/1, human adjudication 2/4, and adjudication completion 2/2.

A **false success** means the target SAST finding was resolved but downstream security/functional/new-finding validation still failed. XSS Attempt 1 is not a false success because the SAST target remained persistent.

The policy's false-success outcome is exercised by a deterministic static-output XSS negative control. It resolves the SAST target by removing reflection but fails functionality and makes targeted security testing inconclusive. The manifest labels it `deterministic_non_ai` and `outcome_coverage_only`; the report excludes it from every primary AI-attempt metric. This demonstrates the policy branch without misrepresenting the control as AI-generated evidence.

The generated [evaluation report](docs/evaluation-report.md) is the authoritative human-readable matrix; rerun the builder after selecting any new attempt in the manifest.

## Reproducibility verification

The final-experiment verification command rebuilds both reports from the
authoritative manifest, validates experiment and control separation, checks
required policy-outcome and decision-state coverage, confirms adjudication and
artifact bindings, and runs the complete automated test suite:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.reproduce --verify
```

Use the project virtual-environment interpreter shown above. A bare `python`
may resolve to a different system installation with the wrong dependencies.

To verify first and then launch the dashboard:

```powershell
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

The reproducibility command is deterministic and does not call the OpenAI API,
rerun Semgrep, generate a new remediation, modify benchmark source, or approve
a candidate. It regenerates only the two derived evaluation reports.

## Controlled demo command

Use the manifest-selected SQLi candidate for a reproducible runtime-validation
and dashboard demonstration:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.demo `
  --case sqli `
  --validate `
  --serve
```

Supported case selections are `sqli`, `xss`, and `path-traversal`. XSS defaults
to its latest selected attempt; add `--attempt 1` to demonstrate the functional
regression and `REJECT` outcome from its first attempt.

Live demo results are written to a unique directory under Windows `TEMP` and
are explicitly non-authoritative. The default command reuses the recorded
candidate-SAST result while rerunning security, functional, and decision
stages. The command does not call the model or overwrite experiment data.

To rerun candidate syntax and Semgrep as well, use the guided fresh-SAST mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case sqli `
  -Attempt 1 `
  -FreshSast `
  -SkipVerification
```

The CLI prints an evidence plan labeling every input as recorded or live. Fresh
SAST artifacts are stored beside the disposable runtime outputs under `TEMP`.
The served dashboard always remains the authoritative recorded experiment.

See the [demonstration guide](docs/demo-guide.md) for the baseline SQLi exploit,
candidate-patch walkthrough, supported outcomes, and suggested presentation
sequence.

For the simplest Windows follow-along test, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Case sqli
```

Add `-Serve` to keep the verified read-only dashboard running after the
controlled validation completes.

Run all controlled vulnerability and decision test sets with:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
```

## Read-only dashboard

The local dashboard reads the generated JSON report and does not run scans, call the remediation model, modify artifacts, or approve candidates.

Regenerate the report and start the server:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.evaluation.report_builder
.\.venv\Scripts\python.exe -m fixproof.evaluation.dashboard
```

Open:

```text
http://127.0.0.1:8080/ui/
```

The dashboard presents primary metrics, outcome coverage, the experiment matrix, attempt-level evidence, rule provenance, artifact bindings, human-adjudication status, and the separated false-success control. Its local server exposes only `/ui/*` and `data/evaluation/experiment-report.json`; other repository paths are blocked.

## Scope guardrails for CS6727

Do not turn FixProof into a general-purpose SAST replacement, full DAST product, multi-language framework, production autonomous deployment system, or Semgrep accuracy benchmark.

The strongest semester project is a complete validation-oriented prototype across a small controlled set of vulnerabilities with clear methodology, measured outcomes, and documented limitations.
