# FixProof Architecture

## Purpose and boundary

FixProof is a validation-oriented research prototype for AI-generated
vulnerability remediation. It does not automatically deploy or approve a
patch. Its boundary ends at an evidence-backed disposition and a separate
human review record.

The system has two deliberately separated planes:

- The remediation plane creates one candidate from scanner evidence and
  focused source context.
- The validation plane independently applies, tests, classifies, and reports
  that candidate without asking the remediation model to judge its own work.

## End-to-end data flow

```text
Benchmark application
        |
        v
Semgrep scan (default rules + labeled controlled rules)
        |
        v
Normalize findings -> correlate evidence -> build focused context
        |
        v
Structured remediation prompt -> AI candidate artifact
        |
        v
Isolated attempt workspace + candidate patch
        |
        +-------------------+--------------------+
        |                   |                    |
        v                   v                    v
Syntax/build check     Candidate SAST      Runtime validators
                            rescan          security + function
        |                   |                    |
        +-------------------+--------------------+
                            |
                            v
                 Deterministic decision policy
                            |
           +----------------+----------------+
           |                |                |
           v                v                v
        REJECT      READY_FOR_HUMAN_   NEEDS_HUMAN_
                         REVIEW          ADJUDICATION
                            |
                            v
           Manifest-selected evaluation + dashboard
```

## Components

| Component | Responsibility | Primary implementation |
|---|---|---|
| Scanner runner and parser | Run Semgrep, normalize findings, retain rule origin | `src/fixproof/scanners/` |
| Finding correlator | Merge scanner evidence into stable canonical findings | `src/fixproof/findings/` |
| Context and prompt builders | Select the relevant code boundary and create a structured remediation task | `src/fixproof/agent/context_builder.py`, `prompt_builder.py` |
| Remediation agent | Call the configured model and save the structured response unchanged | `src/fixproof/agent/remediation_agent.py` |
| Patch workspace | Copy the benchmark, apply one candidate, record hashes, and preserve the baseline | `src/fixproof/patches/patch_workspace.py` |
| Preliminary validation | Check syntax and semantically compare baseline and candidate SAST findings | `src/fixproof/validation/validation_runner.py` |
| Runtime validation | Execute CWE-specific security and functional tests | `security_validator.py`, `functional_validator.py` |
| Decision engine | Convert evidence into a deterministic disposition and reason codes | `src/fixproof/validation/decision_engine.py` |
| Human adjudication | Bind immutable evidence packets to separate reviewer results | `src/fixproof/evaluation/adjudication.py` |
| Evaluation report | Select authoritative artifacts, validate consistency, and compute metrics | `src/fixproof/evaluation/report_builder.py` |
| Dashboard | Display only the generated machine-readable report | `src/fixproof/evaluation/dashboard.py`, `ui/` |
| Reproducibility gate | Rebuild reports, verify study invariants, run tests, and optionally serve the dashboard | `src/fixproof/reproduce.py` |
| Demo operator | Select a supported authoritative attempt, rerun runtime validation into disposable outputs, compare the live decision, and optionally serve the dashboard | `src/fixproof/demo.py` |

## Artifact model

The filesystem is the prototype's evidence store. Each stage writes an
immutable or append-only JSON artifact instead of passing an unrecorded
in-memory conclusion to the next stage.

```text
data/raw_scans/             scanner output
data/normalized/            normalized findings and rule origin
data/correlated/            canonical findings and merged evidence
data/contexts/              focused source context
data/prompts/               structured remediation inputs
data/remediations/          unchanged model responses
workspaces/                 isolated applications, patches, and hashes
data/validation/            syntax and SAST comparison
data/security_validation/   targeted exploit-oriented checks
data/functional_validation/ regression checks
data/decisions/             deterministic policy results
data/adjudications/         immutable packets and separate human results
data/evaluation/            authoritative manifest and generated report
```

`data/evaluation/experiment-manifest.json` is the selection authority. This is
important because historical and revised evidence may coexist. The report
builder follows only selected paths, validates cross-artifact identities and
evidence, and records SHA-256 digests for every selected artifact.

## Security and trust boundaries

- The vulnerable benchmark is treated as untrusted code and is never patched
  in place.
- A candidate is model-generated, untrusted input until validation completes.
- Attempt workspaces are copies. They provide experiment isolation but are not
  hardened operating-system or container sandboxes.
- Ground truth and runtime tests are withheld from the remediation prompt, so
  model generation and evaluation remain separate.
- Controlled scanner rules are labeled `fixproof_controlled`; standard scanner
  evidence is labeled `semgrep_oss`; legacy evidence remains `unrecorded`
  instead of being inferred.
- Automated decisions cannot be overwritten by an adjudication. A reviewer
  result is a separate, evidence-bound artifact.
- The dashboard server exposes only `/ui/*` and the generated report JSON. It
  blocks access to the rest of the repository and applies restrictive browser
  security headers.
- API credentials come from environment variables and are never stored in
  artifacts or source code.

## Decision and human boundary

The evidence-aware policy uses three terminal dispositions:

- `REJECT` when syntax, security, functionality, or new-finding evidence shows
  a concrete failure.
- `READY_FOR_HUMAN_REVIEW` when the target SAST finding resolves and all other
  selected checks pass.
- `NEEDS_HUMAN_ADJUDICATION` when the SAST target persists while targeted
  security and functional evidence pass with no new findings.

This boundary avoids two unsafe shortcuts: treating scanner silence as proof of
correctness and repeatedly rewriting functional code only to silence a rule.

## Reproducibility and presentation layer

`python -m fixproof.reproduce --verify` rebuilds the two derived reports from
the manifest, verifies metric separation and required outcomes, checks
adjudication and artifact bindings, and runs all tests. `--serve` performs the
same verification before starting the dashboard. Neither mode reruns the model
or scanner.

The dashboard is therefore a view of recorded experiment state, not a workflow
engine. New experiment data enters through the command-line pipeline and the
manifest, after which the report is regenerated and the dashboard refreshed.

`python -m fixproof.demo --case sqli --validate --serve` is the bounded
presentation entry point. It uses the recorded preliminary SAST evidence,
reruns the independent runtime layers, writes only to a unique temporary
directory, and refuses to continue if the live decision differs from the
manifest-selected decision. The temporary results do not replace the
authoritative experiment artifacts shown by the dashboard.

## Known architectural limits

The prototype is intentionally scoped to JavaScript/Express benchmarks,
Semgrep CE/OSS, endpoint-specific runtime tests, filesystem workspaces, and a
small controlled sample. Primary-v1 executes controlled XSS payloads in
headless Chromium, but the route and payload set remain narrow. The controlled
SQLi rule is benchmark-oriented, and canonical fingerprinting remains
MVP-level. These limits constrain generalization but do not invalidate the
demonstrated validation workflow.
