# FixProof Demonstration Guide

These runtime demos replay selected **pilot** candidates. The 15-attempt
primary study has a separate evidence view at `/ui/primary.html`, served by
`python -m fixproof.reproduce --serve`. The lifecycle demonstration is a
separately labeled recorded replay; see [prototype status](prototype-status.md).

## Follow-along demo test

This is the recommended classroom demonstration. It uses an authoritative,
previously recorded AI candidate, reruns independent validation, and leaves the
benchmark and experiment artifacts unchanged.

### Choose the evidence mode first

The guided command prints an evidence plan before it starts. There are two
candidate-validation modes:

| Mode | Recorded inputs | Live work | Best use |
|---|---|---|---|
| Default replay | AI candidate, baseline SAST, candidate SAST | Runtime security, functional regression, decision | Fast, deterministic classroom explanation |
| `-FreshSast` | AI candidate, baseline SAST | Candidate syntax/Semgrep, runtime security, functional regression, decision | Prove that the candidate is actually rescanned |

Both modes write newly generated outputs to a unique directory under Windows
`TEMP`. Neither mode calls the OpenAI API, changes the vulnerable baseline, or
adds results to the authoritative experiment. The dashboard always shows the
recorded authoritative experiment.

Recommended learning order:

1. Run XSS attempt 1 in the default mode to see a functional regression.
2. Run XSS attempt 2 in the default mode to see an evidence disagreement.
3. Run one selected case with `-FreshSast` to include an actual candidate
   Semgrep rescan.

### Run the complete test-set matrix

Use this command when you want to demonstrate that FixProof handles more than
one vulnerability or outcome correctly:

```powershell
Set-Location "C:\path\to\fixproof"
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
```

The suite runs the readiness gate once and then executes four isolated runtime
candidate validations:

| Set | Vulnerability/evidence condition | What the test proves | Expected decision |
|---|---|---|---|
| TS-01 | Reproducibility and policy checks | All 37 automated tests, artifact bindings, metric separation, adjudication completion, and false-success control coverage | `READY` |
| TS-02 | SQL injection, CWE-89 | Parameterization resolves the target while preserving legitimate lookups | `READY_FOR_HUMAN_REVIEW` |
| TS-03 | XSS attempt 1, CWE-79 | A security improvement with a functional regression must be rejected | `REJECT` |
| TS-04 | XSS attempt 2, CWE-79 | Static/runtime disagreement must cross the human boundary | `NEEDS_HUMAN_ADJUDICATION` |
| TS-05 | Path traversal, CWE-22 | Conflicting evidence must cross the human boundary | `NEEDS_HUMAN_ADJUDICATION` |

A test set passes when live runtime and functional validation reproduce its
expected policy outcome using the selected candidate and candidate-SAST mode.
Therefore, TS-03 passing means FixProof correctly produced `REJECT`; it does
not mean the rejected patch is safe to deploy.

The suite uses new directories under Windows `TEMP` and never overwrites the
manifest-selected evidence. `-Serve` is intentionally limited to a single-case
demo so the all-case suite can finish and print its complete summary.

### Run one test set

From Windows PowerShell:

```powershell
Set-Location "C:\path\to\fixproof"
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Case sqli
```

To include a fresh candidate syntax check and Semgrep rescan:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case sqli `
  -Attempt 1 `
  -FreshSast `
  -SkipVerification
```

The fresh scan's raw, normalized, correlated, and preliminary artifacts are
stored beside the disposable runtime outputs. If the fresh result no longer
matches the recorded decision, the demo fails visibly instead of hiding the
drift.

Follow these checkpoints in the output:

1. The reproducibility gate finishes with `37 tests`, `OK`, and `READY`.
2. The selected finding is `CF-345f0ac3d7ae` / `CWE-89`.
3. Both targeted SQL-injection tests pass.
4. All three functional regression tests pass.
5. The deterministic decision is `READY_FOR_HUMAN_REVIEW`.
6. `Recorded decision match: yes` confirms that fresh runtime evidence agrees
   with the authoritative experiment.

To finish by opening the dashboard, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case sqli `
  -Serve
```

Open `http://127.0.0.1:8080/ui/` in your browser. Press `Ctrl+C` in
PowerShell to stop the server.

The runner supports the other controlled outcomes:

```powershell
# Functional regression causes rejection.
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case xss `
  -Attempt 1

# Static/runtime disagreement requires human adjudication.
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case xss `
  -UseLatestAttempt

# Path-traversal evidence requires human adjudication.
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 `
  -Case path-traversal
```

Use `-SkipVerification` only when you have already shown the readiness gate and
want a shorter repeat of the runtime demonstration.

### Files involved in the SQLi demo

| Role | File |
|---|---|
| Vulnerable benchmark | `sample_apps/vulnerable-sqli-app/app.js` |
| Controlled CWE-89 context | `data/contexts/vulnerable-sqli-app-rule-v2.json` |
| Recorded AI remediation | `data/remediations/CF-345f0ac3d7ae-attempt-01.json` |
| Isolated patched candidate | `workspaces/revalidations/sqli-rule-v2/CF-345f0ac3d7ae/attempt-01/app/app.js` |
| Candidate patch | `workspaces/revalidations/sqli-rule-v2/CF-345f0ac3d7ae/attempt-01/candidate.patch` |
| Authoritative experiment | `data/evaluation/experiment-manifest.json` |
| Dashboard report | `data/evaluation/experiment-report.json` |

The CLI tests the isolated candidate under `workspaces/`; it does not edit or
run remediation directly against the vulnerable baseline.

### Optional live OpenAI generation

The classroom demo above does not require or spend API credit. If you explicitly
want to demonstrate fresh AI generation, keep `.env` off screen and use a
disposable output:

```powershell
$env:PYTHONPATH="src"
$liveOutput = Join-Path $env:TEMP `
  ("fixproof-live-sqli-" + [guid]::NewGuid().ToString("N") + ".json")

.\.venv\Scripts\python.exe -m fixproof.agent.remediation_agent `
  --input data\prompts\vulnerable-sqli-app.json `
  --canonical-id CF-345f0ac3d7ae `
  --output $liveOutput

Write-Host "Disposable remediation: $liveOutput"
```

This sends the remediation prompt and included source context to OpenAI. It
generates a candidate only; it does not add that candidate to the authoritative
dashboard or approve it. The recorded-candidate command remains the recommended
graded demonstration because it is reproducible and exercises the validation
and decision layers without model-output variability.

## Recommended command

From the repository root:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.demo `
  --case sqli `
  --validate `
  --serve
```

The command selects the authoritative SQLi candidate from the experiment
manifest, reruns targeted security and functional validation, recomputes the
decision, verifies that it matches the recorded decision, and then starts the
read-only dashboard at `http://127.0.0.1:8080/ui/`.

Press `Ctrl+C` to stop the dashboard.

The recorded-candidate demo does not require an API key. For an optional live
remediation call, populate the ignored repository `.env` once and run
`fixproof.agent.remediation_agent`; the agent automatically loads that file.
Never show `.env` during a screen recording or presentation.

## Safety and reproducibility behavior

The demo command:

- uses only AI-generated attempts selected by
  `data/evaluation/experiment-manifest.json`;
- checks that the baseline was not modified;
- does not call the OpenAI API;
- reuses the recorded preliminary SAST result by default;
- reruns candidate syntax and Semgrep only when `--fresh-sast`/`-FreshSast`
  is selected, writing those outputs under `TEMP`;
- writes fresh security, functional, decision, and summary JSON files to a
  unique directory under Windows `TEMP`;
- does not overwrite authoritative artifacts;
- refuses to start live validation when port 3000 is already occupied;
- checks that live classification and disposition match the recorded decision;
- refuses to serve a stale or non-ready dashboard report.

The dashboard continues to show the authoritative experiment, not disposable
demo outputs.

## Supported cases

| Command selection | Default attempt | Expected live decision |
|---|---:|---|
| `--case sqli` | 1 | `READY_FOR_HUMAN_REVIEW` |
| `--case xss` | 2 | `NEEDS_HUMAN_ADJUDICATION` |
| `--case path-traversal` | 1 | `NEEDS_HUMAN_ADJUDICATION` |
| `--case xss --attempt 1` | 1 | `REJECT` |

When a case has multiple selected attempts, the command defaults to the latest
attempt. Use `--attempt` to demonstrate an earlier selected attempt.

Run validation without serving the dashboard:

```powershell
.\.venv\Scripts\python.exe -m fixproof.demo --case xss --attempt 1 --validate
```

Inspect a selected case without starting an application:

```powershell
.\.venv\Scripts\python.exe -m fixproof.demo --case path-traversal
```

The command prints the vulnerable source and candidate patch paths.

## Suggested seven-minute presentation

### 1. Establish the SQLi ground truth

In terminal 1:

```powershell
node .\sample_apps\vulnerable-sqli-app\app.js
```

In terminal 2, show a normal lookup:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:3000/user?username=alice" |
  ConvertTo-Json
```

Then show the injection returning all three seeded users:

```powershell
Invoke-RestMethod `
  "http://127.0.0.1:3000/user?username=%27%20OR%20%271%27%3D%271" |
  ConvertTo-Json
```

Stop terminal 1 with `Ctrl+C`. The demo validator cannot run until port 3000
is free.

### 2. Show the recorded AI patch

```powershell
Get-Content `
  .\workspaces\revalidations\sqli-rule-v2\CF-345f0ac3d7ae\attempt-01\candidate.patch
```

Point out the change from SQL string concatenation to a parameterized query.

### 3. Run the controlled demo

```powershell
.\.venv\Scripts\python.exe -m fixproof.demo `
  --case sqli `
  --validate `
  --serve
```

The live output should show two security passes, three functional passes,
`validated_candidate`, and `READY_FOR_HUMAN_REVIEW`.

### 4. Use the dashboard to explain why validation matters

Show these experiment rows:

- XSS Attempt 1: runtime security passed but functionality failed, so FixProof
  rejected it.
- XSS Attempt 2: functionality improved, but SAST and runtime evidence
  disagreed, so FixProof required adjudication.
- SQLi Attempt 1: SAST resolved and both runtime layers passed, so the candidate
  became ready for human review.
- The non-AI static-output control: SAST silence did not hide functional
  failure, and the control remained excluded from AI metrics.

## Scope statement

This command demonstrates recorded candidates for the three controlled
JavaScript/Express benchmarks. It is not an upload-any-repository remediation
product. New applications can enter the staged scanner pipeline, but complete
runtime validation currently requires one of the supported CWE-specific
Express patterns.
