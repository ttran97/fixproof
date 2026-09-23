# FixProof supplemental-v1 results

**Evidence date:** September 14, 2026  
**Protocol:** `supplemental-v1`, frozen September 14  
**Machine-readable report:** `data/supplemental/v1/supplemental-report.json`  
**Execution environment:** `data/supplemental/v1/execution-environment.json`  
**Human follow-up status:** three requested follow-ups recorded September 15, two consistency qualifications recorded September 21, and nine additional candidate decisions recorded September 22; no original review or primary metric has been overwritten

## What was tested

The study reused the three frozen baselines and all 15 saved primary AI candidates. It made no model calls and did not rerun SAST. Each application ran from a disposable copy with the same registered cases for every comparable candidate.

The test categories remain separate:

- **Security:** attack execution, out-of-root disclosure, or broadened database results.
- **Behavioral parity:** benign behavior that must match the frozen baseline.
- **Robustness contract:** new handling rules for malformed or ambiguous inputs.

## Verified totals

| Category | Registered candidate observations | Pass | Fail | Inconclusive | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Security | 60 | 55 | 0 | 5 | Every executable security case passed; the symlink case was unavailable for all five traversal candidates. |
| Behavioral parity | 45 | 40 | 5 | 0 | Four XSS candidates changed missing-name output; traversal attempt 01 rejected a valid in-root filename. |
| Robustness contract | 35 | 25 | 10 | 0 | Traversal candidates varied; every SQLi candidate lacked the new repeated-parameter rejection rule. |
| **Total** | **140** | **120** | **15** | **5** | These mixed categories must not be presented as one security success rate. |

## Baseline gate

| CWE | Registered cases | Matched | Mismatched | Inconclusive | Candidate execution permitted |
| --- | ---: | ---: | ---: | ---: | --- |
| XSS | 9 | 9 | 0 | 0 | Yes |
| Path traversal | 11 | 10 | 0 | 1 | Yes, for executable cases |
| SQL injection | 8 | 8 | 0 | 0 | Yes |

The path symlink case is inconclusive because Windows denied symlink creation with WinError 1314. This is not a pass. An earlier path-baseline run recorded two line-ending mismatches caused by the fixture writer. That result remains preserved with an investigation record and was not used as a candidate gate. The corrected runner wrote byte-deterministic fixtures and created a new baseline run.

## Candidate comparison

| CWE / attempt | Pass | Fail | Inconclusive | Nonpassing evidence |
| --- | ---: | ---: | ---: | --- |
| XSS 01 | 8 | 1 | 0 | `XSS-P01` missing-input parity |
| XSS 02 | 8 | 1 | 0 | `XSS-P01` missing-input parity |
| XSS 03 | 9 | 0 | 0 | None in registered supplement |
| XSS 04 | 8 | 1 | 0 | `XSS-P01` missing-input parity |
| XSS 05 | 8 | 1 | 0 | `XSS-P01` missing-input parity |
| Traversal 01 | 8 | 2 | 1 | `PATH-P01` valid filename; `PATH-R03` repeated input; `PATH-S06` inconclusive |
| Traversal 02 | 10 | 0 | 1 | `PATH-S06` inconclusive |
| Traversal 03 | 7 | 3 | 1 | `PATH-R01`–`R03`; `PATH-S06` inconclusive |
| Traversal 04 | 10 | 0 | 1 | `PATH-S06` inconclusive |
| Traversal 05 | 9 | 1 | 1 | `PATH-R03`; `PATH-S06` inconclusive |
| SQLi 01–05, each | 7 | 1 | 0 | `SQL-R01` repeated-input robustness |

## What the evidence supports

1. **XSS:** all five candidates passed the three supplemental security cases. Attempts 01, 02, 04, and 05 changed omitted-name output from the baseline `Hello undefined` to `Hello `. Attempt 03 preserved that behavior and passed all nine registered supplemental cases.
2. **Path traversal:** every candidate passed the five executable supplemental security cases. The sixth security case, symlink escape, remains inconclusive for every candidate. Attempt 01 also rejected the legitimate in-root `..notes.txt` fixture and did not meet the repeated-parameter contract.
3. **SQL injection:** all five saved candidates passed the security, baseline-parity, and punctuation/Unicode lookup checks. All five missed the newly defined HTTP 400 rule for repeated `username` parameters. Because that rule is supplemental, this is a robustness limitation rather than a retroactive primary security failure.

The evidence does not establish application-wide security, production readiness, or automatic acceptance. It does show why separate oracles and human review add information that the primary passing counters omitted.

## Human follow-up recorded

The original `REQUEST_ADDITIONAL_TESTING` records remain unchanged. Separate
Tony Tran follow-up records under `data/supplemental/v1/follow-up-reviews/`
contain these September 15 conclusions:

| Candidate | Follow-up verdict | Main evidence |
| --- | --- | --- |
| XSS 04 | `FOLLOW_UP_REJECT_CANDIDATE` | Missing-input parity failure |
| XSS 05 | `FOLLOW_UP_REJECT_CANDIDATE` | Same missing-input parity criterion |
| Path traversal 01 | `FOLLOW_UP_REJECT_CANDIDATE` | Valid-filename parity and repeated-input robustness failures; symlink uncertainty remains |

Packet/result bindings were verified September 21. These are recorded personal
conclusions, not new automatic policy decisions or a rewrite of primary outcomes.

Tony later reviewed XSS 01 and 02 against the same frozen criterion and recorded
these September 21 qualifications:

| Candidate | Later verdict | Main evidence |
| --- | --- | --- |
| XSS 01 | `FOLLOW_UP_REJECT_CANDIDATE` | `XSS-P01` missing-input parity failure caused by `String(value ?? "")` |
| XSS 02 | `FOLLOW_UP_REJECT_CANDIDATE` | `XSS-P01` missing-input parity failure caused by `String(name ?? "")` |

The later records qualify but do not overwrite the original primary
`ACCEPT_CANDIDATE` results. Report 3 must also disclose that accepted traversal
attempts 03 and 05 missed supplemental robustness rules. Those are new-contract
limitations rather than retroactive primary security failures.

After reviewing the remaining SQLi and traversal evidence on September 22,
Tony recorded nine additional candidate-specific results:

| Candidates | Later verdict | Main evidence and boundary |
| --- | --- | --- |
| SQLi 01–05 | `FOLLOW_UP_ACCEPT_CANDIDATE` | Parameterized queries passed 3/3 security and 2/2 parity cases and returned no unauthorized rows. `SQL-R01` remains a failed low-impact robustness contract: HTTP 200 `[]` rather than HTTP 400. Acceptance is bounded to the tested injection repair, not full supplemental conformance. |
| Traversal 02 | `FOLLOW_UP_REQUEST_MORE_TESTING` | All executable cases passed, but `PATH-S06` symlink safety remains inconclusive. |
| Traversal 03 | `FOLLOW_UP_REQUEST_MORE_TESTING` | Three malformed-input robustness cases failed and `PATH-S06` remains inconclusive. |
| Traversal 04 | `FOLLOW_UP_REQUEST_MORE_TESTING` | All executable cases passed, but `PATH-S06` symlink safety remains inconclusive. |
| Traversal 05 | `FOLLOW_UP_REQUEST_MORE_TESTING` | `PATH-R03` returned HTTP 404 rather than HTTP 400, and `PATH-S06` remains inconclusive. |

There are now 14 completed supplemental human records: five rejections, five
bounded acceptances, and four requests for more testing. XSS 03 retains its
original bounded acceptance and has no separate later result because it passed
all nine registered supplemental cases. All 14 packet/result bindings verify.

## Recommended Report 3 comparison

Use XSS attempts 03 and 04:

| Evidence | XSS 03 | XSS 04 |
| --- | --- | --- |
| Supplemental security | 3/3 pass | 3/3 pass |
| Behavioral parity | 5/5 pass | 4/5 pass |
| Entity-looking robustness | Pass | Pass |
| Key difference | Preserves missing `name` as `undefined` | Converts missing `name` to an empty string |

This is a compact demonstration of the FixProof idea: two repairs can both prevent the registered attacks while differing on legitimate behavior outside the original fixed suite.
