# FixProof Reproducibility Procedure

The current verifier rebuilds both pilot and primary reports. It keeps evidence
verification separate from pending primary human reviews. The primary-only
read-only check is `python -m fixproof.evaluation.primary_report --check`;
the primary dashboard is `/ui/primary.html`.

On a machine where `py -3.11` is unavailable but the project Python 3.11
environment exists, use its interpreter to create another environment:
`.\.venv\Scripts\python.exe -m venv <new-environment-path>`.
The clean-check script uses that interpreter when available and falls back to
the Python launcher otherwise.

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

The package metadata pins direct dependencies used by the recorded study, including
Semgrep `1.136.0` as recorded in the raw scan artifacts.

## Verification commands

```powershell
python -m fixproof.reproduce --verify
python -m fixproof.evaluation.primary_report --check
python -m fixproof.findings.lifecycle --history data/lifecycle/sqli-recorded-replay.json --check
powershell -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
```

`reproduce --verify` includes the full automated test suite. The demo suite
reruns four pilot candidates' runtime checks with recorded SAST evidence.

The primary benchmark verifier was used to establish frozen baseline ground
truth and capture scanner evidence. Its default output paths belong to the
completed study. Do not rerun it with defaults after collection. For new
supplemental baseline testing, inspect
`python -m fixproof.evaluation.benchmark_verifier --help` and select separate
output paths before running it. New scanner calls may use changed remote rules.

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

## September 5, 2026 verification checkpoint

The current working tree was copied using tracked plus non-ignored new files
into `dist/verification/current-checkout/`, excluding `.env`, installed
environments, Node dependencies, and generated distribution files. This was a
sanitized **working-copy snapshot**, not an export of a clean committed HEAD.

- A new Python 3.11 environment installed the declared package dependencies.
  Imports resolved to that copy and its environment.
- `npm ci` installed all six pilot/primary apps from their lockfiles.
  Playwright's Chromium installer completed, using the host browser cache.
- `fixproof.reproduce --verify` passed **87 tests** and verified both studies,
  including all 15 primary attempts. Primary human completion remained 0/10.
- The guided demo suite, run after that verification with `-SkipVerification`,
  reproduced all **four** selected pilot runtime decisions using recorded SAST.
- A browser smoke check of the current primary dashboard showed 15 rows and
  nine evidence sections per selected trial, no page errors, and no document
  overflow at desktop width 1440 or mobile width 390.

Local logs are retained under ignored `dist/verification/`:
`python-install.log`, `fresh-verification.log`, `fresh-demo.log`,
`dashboard-smoke.json`, and `frozen-dry-run.log`. The verification-copy source
manifest records file hashes; dependency installation logs also remain in
each copied application's directory.

This checks dependency restoration and evidence relocation on the same
Windows host. It does not establish cross-platform support, a pristine OS
installation, new primary runtime observations, or regeneration of the
original model responses. Transitive Python dependencies are not fully
lockfile-pinned. New scanner/model experiments require their own recorded
conditions and outputs. A final committed-archive check and packaging remain
to be run after reviewing and committing the intended snapshot.
