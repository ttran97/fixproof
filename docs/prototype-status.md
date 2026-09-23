# FixProof prototype status

Updated September 21, 2026. This is the implementation status following the September 4
alignment review. The earlier review remains a historical assessment. New
features are post-collection additions; primary-v1 inputs, candidates,
decisions, and the frozen implementation are preserved.

| Capability | Status and evidence |
|---|---|
| Three-CWE repair/validation workflow | Implemented; pilot evidence remains separate |
| Primary collection | All 15 initial attempts recorded |
| Primary report and verification | Implemented in `evaluation/primary_report.py`; verifies the completed schedule, frozen inputs, prompt reconstruction, 105 attempt-artifact bindings, workspace content, scanner normalization/correlation, tests, decisions, and metrics |
| Primary dashboard | `/ui/primary.html` shows the 15 attempts, measured evidence, code/diffs, and actual conflict-review status |
| Human conflict review | All ten reviews recorded: seven ACCEPT_CANDIDATE and three REQUEST_ADDITIONAL_TESTING (XSS 04–05 and traversal 01) |
| Finding history | New/persistent/resolved/reopened tracking implemented in `findings/lifecycle.py`; nine focused tests cover transitions, ambiguity, replay, coverage changes, tampering, and storage |
| Verification commands | `reproduce --verify` rebuilds/checks pilot and primary reports and runs the complete tests; run `supplemental_report --check` separately for saved supplemental bindings |
| Current automated checks | September 22: 119 tests passed; primary verification passed for all 15 attempts and ten original reviews; supplemental verification passed for three baselines and 15 saved candidates; all 14 supplemental human packet/result bindings verified. |
| September 12 artifact audit | Saved hashes and decision/count consistency checked, including all three review bindings; Python tests and live scanner/runtime checks were not rerun in this checkout |
| Fresh environment check | September 5: all 87 tests passed in an isolated working-copy snapshot with a newly installed Python environment; all six apps' locked Node dependencies installed; all four pilot runtime demos matched recorded decisions |
| Controlled scope | Purpose-built Express fixtures and AI-generated remediation candidates; no claim to have evaluated a representative AI-generated application corpus |
| Course final deliverables | Final paper, slides/video, personal review, and Canvas checks remain student work |

See the [September 13 checkpoint and Video II package](coursework/review-2026-09-13/Current-progress-and-next-steps.md)
for that historical checkpoint, reviewed slides and narration. Use the
[September 21 Report 3 assessment](coursework/review-2026-09-21/CS6727-Progress-Report-3-readiness.md)
for current progress, feedback alignment, file map, and next tasks.
Today's repository checks did not rerun the historical Express applications,
Chromium attacks, model calls or live SAST scans. Report 2 and Video II are
submitted or posted according to Tony's September 14 update; this repository
does not verify Canvas receipts. Video II peer feedback is due September 27 in
the supplied schedule.

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

Standalone evidence verification also includes the supplemental report:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_report --check
```

The primary report commands are:

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

## Supplemental validation and follow-up reviews are complete

Initial conflict reviews are complete. XSS trials 04–05 and path-traversal 01
request additional testing. Preserve the review records and record supplemental
results and follow-up conclusions separately. The ten packets are
under `data/primary_reviews/v1/<trial-id>/packet.json`. They bind each selected
candidate to its evidence. Actual conclusions must be recorded separately
as `result.json`; a generated packet or dashboard visit is not a review.

All five SQLi candidates remain `READY_FOR_HUMAN_REVIEW`, which is not an
approval. The conflict-adjudication workflow concerns the ten XSS/path-traversal
disagreements. Completing those reviews does not automatically approve the
SQLi candidates or make deployment part of this prototype.

The dated, author-approved protocol is at
[`docs/supplemental-protocol-v1.md`](supplemental-protocol-v1.md). It contains
pre-registered security, behavioral-parity, and robustness oracles. Its
September 14 freeze hash is stored in `data/supplemental/v1/protocol-lock.json`.
The runtime was restored and the later preflight passed. All three baselines
and all 15 saved candidates were then evaluated in disposable copies. The
verified report is `data/supplemental/v1/supplemental-report.json`, with a
professor-readable interpretation in `docs/supplemental-results-v1.md`.
All three follow-up conclusions were recorded September 15 under
`data/supplemental/v1/follow-up-reviews/`: XSS 04, XSS 05, and traversal 01
received `FOLLOW_UP_REJECT_CANDIDATE`. Original reviews remain unchanged.
On September 21, Tony applied the same frozen parity criterion to the previously
accepted XSS 01 and 02 candidates and recorded separate
`FOLLOW_UP_REJECT_CANDIDATE` qualifications. Their original primary acceptances
and all primary metrics remain unchanged.

The supplement recorded 55 security passes and five inconclusive cases,
40 behavioral-parity passes and five failures, and 25 robustness passes and
ten failures. XSS 01, 02, 04, and 05 share the missing-input parity failure.
Traversal 03/05 and all SQLi candidates also have supplemental robustness limitations.
See the results document for the distinction between original and new contracts.

September 21 verification exposed an old-checkout absolute-path dependency.
The supplemental verifier now uses registered source paths in the active
checkout and still checks their hashes. Saved experiment records were unchanged.

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

- Strengthen the related-work comparison and prepare Report 3 and Video III.
- Retain the symlink inconclusive result or collect a separately dated follow-up.
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
