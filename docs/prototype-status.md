# FixProof prototype status

Updated September 5, 2026. This is the implementation status following the September 4
alignment review. The earlier review remains a historical assessment. New
features are post-collection additions; primary-v1 inputs, candidates,
decisions, and the frozen implementation are preserved.

| Capability | Status and evidence |
|---|---|
| Three-CWE repair/validation workflow | Implemented; pilot evidence remains separate |
| Primary collection | All 15 initial attempts recorded |
| Primary report and verification | Implemented in `evaluation/primary_report.py`; verifies the completed schedule, frozen inputs, prompt reconstruction, 105 attempt-artifact bindings, workspace content, scanner normalization/correlation, tests, decisions, and metrics |
| Primary dashboard | `/ui/primary.html` shows the 15 attempts, measured evidence, code/diffs, and actual conflict-review status |
| Human conflict review | Ten pending evidence-bound packets prepared; zero completed human results at this checkpoint |
| Finding history | New/persistent/resolved/reopened tracking implemented in `findings/lifecycle.py`; nine focused tests cover transitions, ambiguity, replay, coverage changes, tampering, and storage |
| Verification command | `reproduce --verify` now rebuilds/checks both reports and runs the complete tests; it reports evidence verification separately from human completion |
| Fresh environment check | September 5: all 87 tests passed in an isolated working-copy snapshot with a newly installed Python environment; all six apps' locked Node dependencies installed; all four pilot runtime demos matched recorded decisions |
| Controlled scope | Purpose-built Express fixtures and AI-generated remediation candidates; no claim to have evaluated a representative AI-generated application corpus |
| Course final deliverables | Final paper, slides/video, personal review, and Canvas checks remain student work |

The narrow prototype is close to feature completion. This does not establish
that the CS6727 submission is complete: human conclusions, interpretation,
the final paper/presentation, and required course participation remain.
The fresh-environment check used the same Windows host and shared browser
cache; it was not a new operating system or a committed clean-archive check.
See [reproducibility](reproducibility.md) for the verification record and limits.

## Start here

```powershell
.\.venv\Scripts\python.exe -m fixproof.reproduce --verify
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

Open `http://127.0.0.1:8080/ui/primary.html` for the primary study. The root UI
remains the pilot, with navigation between the two views. Select a primary
trial to inspect source, patch, scanner findings, runtime observations,
functional tests, and bound artifact paths. Model-generated/source content
is displayed as text, not rendered as executable HTML.

The standalone report command is:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.primary_report
.\.venv\Scripts\python.exe -m fixproof.evaluation.primary_report --check
```

The first writes `data/evaluation/primary-report.json` and
`docs/primary-results.md`; the second verifies the underlying study and checks
that both derived reports are current without rewriting them. The adapter is
for a completed primary-v1 collection and fails on missing/incomplete attempts
instead of silently reducing its denominator. Verification checks recorded
observations; it does not rerun the scanner/model/runtime tests or establish
cryptographic authenticity of the original observations.

## Human review is the next concrete milestone

Use [the primary review guide](primary-review-guide.md). The ten packets are
under `data/primary_reviews/v1/<trial-id>/packet.json`. They bind each selected
candidate to its evidence. Actual conclusions must be recorded separately
as `result.json`; a generated packet or dashboard visit is not a review.

All five SQLi candidates remain `READY_FOR_HUMAN_REVIEW`, which is not an
approval. The conflict-adjudication workflow concerns the ten XSS/path-traversal
disagreements. Completing those reviews does not automatically approve the
SQLi candidates or make deployment part of this prototype.

## Four-state finding history

The new lifecycle component runs separately from the frozen two-snapshot
primary comparator. It consumes saved Semgrep JSON plus the corresponding
source tree and records a versioned history. Identity uses **relative file
path + CWE + Express scope**, so same-named files in different directories
remain distinct. Ambiguous same-CWE findings at different locations in one
scope are rejected instead of silently merged. It remains a controlled
Express matcher, not a general semantic program-analysis engine.

```powershell
# Example first snapshot, using the recorded primary SQLi baseline
.\.venv\Scripts\python.exe -m fixproof.findings.lifecycle `
  --history data/lifecycle/my-sqli-history.json `
  --raw-scan data/primary_baselines/raw_scans/sqli-configured.json `
  --source-root benchmarks/primary/v1/sqli `
  --version v1 `
  --ruleset-id recorded-primary-v1-sqli-auto-plus-rule-v2

# Verify the supplied deterministic lifecycle demonstration
.\.venv\Scripts\python.exe -m fixproof.findings.lifecycle `
  --history data/lifecycle/sqli-recorded-replay.json --check
```

The supplied demonstration replays the saved vulnerable baseline, the saved
SQLi attempt-1 candidate, and the baseline reintroduced as a third snapshot.
Its target becomes `new → resolved → reopened`; the unrelated persistent
CSRF finding remains visible. This is a deterministic replay of recorded
evidence, not a newly generated repair or a new live three-version experiment.

Subsequent snapshots must use unique version labels, identical scanned-file
coverage, the same scanner version, and the same declared ruleset identifier.
A repeated identical version is idempotent; conflicting evidence under an
existing version is rejected. Scanner errors or empty coverage cannot resolve
findings. The ledger checks its hash chain and derived state when read, and
uses a lock plus atomic replacement for CLI writes.

The operator must pair a scan with its corresponding source snapshot. The
ruleset ID is an explicit comparability declaration; it does not fetch or
prove equality of remote `auto` rule definitions. Preserve source snapshots
and rule configurations when collecting new histories. `--check` verifies
the stored ledger's internal consistency, not a new scan or the continued
existence of every historical source file.

## Remaining scope and research work

- Personally review the ten conflict packets and record measured conclusions;
  request more testing when the evidence does not justify acceptance.
- State the controlled-app/AI-generated-repair scope in the next progress
  report. Benchmark-authoring AI assistance and evaluation of an AI-generated
  application corpus are different claims.
- Interpret the recorded primary findings honestly: 5/15 target resolutions,
  10/15 SAST/runtime disagreements, and zero observed primary false successes.
- Use the remaining semester for literature comparison, held-out validation
  if justified, limitations, documentation, presentation, and course progress.
- Preserve primary-v1. Any expanded tests or corpus belong to a documented
  supplemental study, not a rewrite of completed primary observations.

The repository walkthrough and final-paper/presentation outlines are in
[the updated submission guide](cs6727-submission-guide.md). The
[documentation index](README.md) distinguishes active references, frozen
study material, historical notes, and disposable local files.
