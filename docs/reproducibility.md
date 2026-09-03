# FixProof Reproducibility Procedure

## Reproducibility levels

FixProof distinguishes three claims:

1. **Recorded-evidence verification** rebuilds reports, verifies bindings and
   policy invariants, and runs unit tests without network or model calls.
2. **Controlled demo reproduction** reruns runtime security and functional
   validation against recorded candidates in disposable directories.
3. **New experimental trial** reruns scanning and model generation and therefore
   requires frozen settings, network access, credentials, and a new attempt ID.

The first two are appropriate for a professor-facing demonstration. They must
not be described as regenerating the original stochastic model response.

## Clean installation

Use Python 3.11 and Node.js with npm:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m playwright install chromium

Push-Location sample_apps\vulnerable-js-app
npm ci
Pop-Location

Push-Location sample_apps\vulnerable-sqli-app
npm ci
Pop-Location

Push-Location sample_apps\vulnerable-path-traversal-app
npm ci
Pop-Location

Push-Location benchmarks\primary\v1\xss
npm ci
Pop-Location

Push-Location benchmarks\primary\v1\sqli
npm ci
Pop-Location

Push-Location benchmarks\primary\v1\path-traversal
npm ci
Pop-Location
```

The package metadata pins the versions used by the recorded pilot, including
Semgrep `1.136.0` as recorded in the raw scan artifacts.

## Verification commands

```powershell
python -m unittest discover -s tests -v
python -m fixproof.reproduce --verify
python -m fixproof.evaluation.benchmark_verifier
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
```

The primary benchmark verifier starts each frozen baseline on loopback, checks
its bound hashes and restore copy, confirms functional-pass/security-fail
ground truth, requires browser execution for CWE-79, and captures Semgrep
evidence. It does not invoke the remediation model or generate an attempt.

The evidence-map document lists the artifacts a reviewer can inspect after the
commands complete.

## Primary trial collection

Before any model call, verify the frozen schedule and prompt boundary:

```powershell
python -m fixproof.primary_trials --dry-run
```

This command uses a temporary preparation directory, writes nothing into the
repository, and makes no model call. The live `--execute` path additionally
requires the exact `PRIMARY-V1-15` confirmation value and a committed
implementation state. Trial artifacts are stored separately under
`data/primary_trials/v1/`; the four historical AI attempts remain pilot
evidence and are not inserted into the new primary schedule. The immutable
schedule is `primary-experiment-manifest.json`; resumable state and primary-only
metrics are kept separately in `collection-state.json`.

## Clean-archive check

After committing the intended snapshot, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-clean.ps1
```

The script exports tracked files to a unique temporary directory and runs the
recorded-evidence verification there. Add `-InstallDependencies` to create a
fresh virtual environment, or `-RunDemoSuite` after Node dependencies are
available in the extracted copy.

## Submission boundary

Build the final archive only from a clean Git snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-submission.ps1
```

This excludes the configured `.env`, the development `.venv`, installed
`node_modules`, temporary workspaces outside the curated evidence allowlist,
and local editor files. Never package the working directory with File Explorer.

## Known clean-environment checks

- The authoritative manifest and every selected artifact must exist.
- Historical workspace paths must relocate under the extracted project root.
- The report and adjudication hashes must still validate.
- No command may use the original checkout as hidden evidence.
- The dashboard must serve only its allowlisted UI and report paths.
- Recorded and live/disposable evidence must remain visibly labeled.
