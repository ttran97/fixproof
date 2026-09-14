# FixProof Progress Report 3 Work Plan

**Prepared:** September 14, 2026  
**Target recorded in the local course schedule:** October 4, 2026 at 11:59 p.m.; verify the live Canvas assignment before submission  
**Current phase:** frozen supplemental definition and environment restoration

## Verified starting point

The saved primary report currently verifies 15 of 15 initial attempts and 10 of 10 required conflict reviews. The ten human verdicts are seven `ACCEPT_CANDIDATE` and three `REQUEST_ADDITIONAL_TESTING`. The additional-testing verdicts are XSS attempts 04–05 and path-traversal attempt 01.

These are primary-study facts. They do not mean that the accepted candidates are application-wide secure, and they do not count any supplemental work that has not yet run.

Tony reported that Progress Report 2 and Video II were submitted or posted. This repository does not verify Canvas submission receipts. Peer feedback for Video II remains a separate course activity due September 27 according to the supplied course schedule.

## Report 3 objective

Show that FixProof moved from identifying limitations to testing them with a predefined, reproducible follow-up protocol. The central contribution should be a baseline/candidate comparison that the primary fixed suite could not make.

## Work sequence

| Order | Deliverable | Evidence of completion | Status |
| --- | --- | --- | --- |
| 1 | Review and freeze `docs/supplemental-protocol-v1.md` | Author approval, freeze date, and SHA-256 | Complete September 14 |
| 2 | Implement the isolated supplemental runner | Definition verifier and preflight implemented; live runner still required | In progress |
| 3 | Create disposable fixtures and manifest | 28-case manifest created; disposable runtime fixtures remain | In progress |
| 4 | Execute baseline characterization | One result per registered test ID; no candidate execution if a baseline oracle is wrong | Not started |
| 5 | Execute all comparable saved candidates | Complete XSS, traversal, and SQLi result matrices | Not started |
| 6 | Review the three requested follow-ups | Separate dated conclusions; original reviews unchanged | Not started |
| 7 | Draft Report 3 and Video III evidence comparison | One concise comparison plus limitations and next step | Not started |

## Suggested timeline

| Date | Focus |
| --- | --- |
| September 14–16 | Approve/freeze protocol and implement result schema plus fixtures |
| September 17–20 | Implement runner and automated tests; run baseline characterization |
| September 21–24 | Run saved candidates and preserve every outcome |
| By September 27 | Complete the required substantive peer-feedback activity |
| September 25–29 | Record follow-up conclusions and select one comparison |
| September 30–October 3 | Draft, cross-check, and visually inspect Progress Report 3 |
| October 4 | Verify Canvas instructions and submit by the live deadline |

Dates after September 14 are planning targets, not claims that the work occurred.

## Current gate before live testing

The September 14 preflight verified the frozen protocol and all 28 registered case definitions without launching an application. It found that Node and npm are not on PATH, Chromium is not installed for this Python environment, and `node_modules` is absent from all three primary benchmark directories. These are environment blockers, not candidate failures.

After installing a supported Node.js LTS release and opening a new PowerShell terminal, use this sequence from the inner `fixproof` repository root:

```powershell
node --version
npm --version

foreach ($case in @("xss", "sqli", "path-traversal")) {
    Push-Location "benchmarks\primary\v1\$case"
    npm ci
    Pop-Location
}

.\.venv\Scripts\python.exe -m playwright install chromium
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_protocol preflight `
    --project-root . `
    --output data/supplemental/v1/environment-preflight.json `
    --require-ready
```

This command is only a readiness check. The following development step is the live runner and disposable fixture builder; baseline characterization comes after those components pass repository tests.

## Evidence to collect for the report

- Frozen protocol identifier, date, and hash.
- Supplemental runner test count and repository-test result.
- Baseline and candidate totals separated by security, behavioral parity, robustness, and inconclusive outcomes.
- One case-level comparison with input, oracle, observed result, and interpretation.
- Any environment limitations, especially Chromium or Windows symlink/junction availability.
- Actual hours from Tony's work log; do not reuse or estimate hours from Progress Report 2.
- Updated generative-AI disclosure describing implementation/editing assistance and Tony's personal evidence review and final conclusions.

## Recommended Report 3 structure

1. **Reporting period and effort:** dates, actual hours, and completed tasks.
2. **Problem and purpose:** fixed passing tests can omit important behavioral and boundary cases.
3. **Methods update:** pre-registration, isolated supplemental fixtures, baseline/candidate symmetry, and separate oracles.
4. **Results to date:** report only executed and saved results; include one compact comparison table.
5. **Interpretation and limitations:** distinguish a security failure from a parity or robustness failure.
6. **Next work:** follow-up conclusions, failure controls, Video III, and remaining project package.
7. **AI disclosure:** tools used, what they assisted with, what Tony personally verified, and who made the final conclusions.

## Quality gate before submission

- Every number traces to a saved machine-readable artifact.
- No supplemental result is included before execution and review.
- Primary and supplemental denominators remain separate.
- No claim treats a persistent or removed SAST finding as proof by itself.
- The report explains why the new tests were selected from recorded review gaps.
- Prior professor or peer feedback is named and connected to a concrete change.
- The live Canvas due date, template requirements, file rendering, and submission receipt are checked.
