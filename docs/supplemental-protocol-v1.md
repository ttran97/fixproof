# FixProof Supplemental Validation Protocol v1

**Protocol ID:** `supplemental-v1`  
**Prepared:** September 14, 2026  
**Status:** FROZEN — approved by Tony Tran on September 14, 2026  
**Executions recorded under this protocol:** 0

## Purpose

This protocol tests evidence gaps found during human review of the frozen `primary-v1` study. It reuses the saved baseline applications and AI-generated candidates; it does not request new AI repairs or change any primary result.

The supplemental study asks a narrower question:

> Do the saved candidates remain secure and behaviorally acceptable when inputs and path boundaries omitted from the fixed primary suites are tested?

The primary study remains the source of truth for its original 15 attempts and 10 conflict reviews. Supplemental findings may qualify the follow-up interpretation, but they must not overwrite files under `data/primary_trials/v1/` or `data/primary_reviews/v1/`.

## Direction in plain language

1. Implement the registered cases and verify the runner with automated tests.
2. Restore Node, locked fixture dependencies, and Chromium as setup work.
3. Run each baseline first. If a registered baseline expectation is wrong, stop that CWE and revise the protocol before observing candidate outcomes.
4. Run the same cases against all five saved candidates for that CWE.
5. Report security, behavioral-parity, and robustness outcomes separately.
6. Use the saved evidence to write dated follow-up conclusions without changing the original reviews.

This sequence turns the review concerns into reproducible evidence. It does not seek a preferred pass or failure result.

## Evidence categories and outcome language

Each test has one primary category so different claims are not collapsed into a single passing counter.

| Category | Question | Allowed outcome |
| --- | --- | --- |
| Security | Did the attack execute, expose forbidden data, or broaden a database result? | `PASS`, `FAIL`, or `INCONCLUSIVE` |
| Behavioral parity | Did the candidate preserve a defined benign baseline behavior? | `PASS`, `FAIL`, or `INCONCLUSIVE` |
| Robustness contract | Did malformed or ambiguous input receive the response predefined here? | `CONFORMS`, `DOES_NOT_CONFORM`, or `INCONCLUSIVE` |

A candidate does not receive a new acceptance verdict automatically. The author records a dated follow-up conclusion after reviewing the three categories separately.

## Candidate and baseline sets

| CWE | Baseline | Comparable saved candidates |
| --- | --- | --- |
| CWE-79 reflected XSS | `benchmarks/primary/v1/xss/` | `xss/attempt-01` through `xss/attempt-05` |
| CWE-89 SQL injection | `benchmarks/primary/v1/sqli/` | `sqli/attempt-01` through `sqli/attempt-05` |
| CWE-22 path traversal | `benchmarks/primary/v1/path-traversal/` | `path-traversal/attempt-01` through `path-traversal/attempt-05` |

All five saved attempt IDs are executed even when their source hashes are identical. Source duplication is reported; it is not treated as five independent repair designs.

## Pre-registered test matrix

### Reflected XSS (CWE-79)

For every browser case, the runner records HTTP status, response text, `h1.textContent`, relevant DOM node counts, JavaScript dialogs, and browser errors. Query values are encoded exactly once unless a case explicitly supplies a raw URL.

| Test ID | Input | Baseline expectation | Candidate expectation | Security oracle | Functional oracle | Candidates |
| --- | --- | --- | --- | --- | --- | --- |
| XSS-P01 | Omit `name` | HTTP 200; `h1.textContent` is `Hello undefined` | Preserve the same observable text | No dialog or executable injected node | Exact status and `h1.textContent` parity | XSS 01–05 |
| XSS-P02 | `name=` | HTTP 200; `h1.textContent` is `Hello ` | Preserve the same observable text | No dialog or executable injected node | Exact status and `h1.textContent` parity | XSS 01–05 |
| XSS-P03 | `name=Tony&name=Admin` | HTTP 200; expected text is `Hello Tony,Admin` under the pinned Express parser | Preserve the same observable text | No dialog or executable injected node | Exact status and `h1.textContent` parity; halt and revise before candidate runs if baseline characterization differs | XSS 01–05 |
| XSS-P04 | `Zoë 漢字 😀` | HTTP 200 and exact Unicode text | Preserve exact Unicode text | No dialog or executable injected node | Exact `h1.textContent` | XSS 01–05 |
| XSS-P05 | `O'Reilly \`admin\`` | HTTP 200 and exact punctuation text | Preserve exact punctuation text | No dialog or executable injected node | Exact `h1.textContent` | XSS 01–05 |
| XSS-R01 | Literal entity-looking text `&lt;b&gt;Tony&lt;/b&gt;` | Characterize the baseline browser text; raw concatenation is expected to interpret the entity once | Display the literal submitted value as text | No `b`, `script`, `img`, or `svg` element created from input; no dialog | `h1.textContent` ends with the literal `&lt;b&gt;Tony&lt;/b&gt;` | XSS 01–05 |
| XSS-S01 | Mixed-case `<ScRiPt>alert(1)</ScRiPt>` | Vulnerable baseline is expected to create a script element and execute | Input appears only as text | No dialog; no attacker-created script element | HTTP 200 and one greeting `h1` | XSS 01–05 |
| XSS-S02 | Repeated values: safe `Tony`, then `<img src=x onerror=alert(1)>` | Vulnerable baseline is expected to create an image element and execute | Both values are rendered only as text | No dialog; no attacker-created image element | HTTP 200; deterministic greeting text is recorded | XSS 01–05 |
| XSS-S03 | All supplemental XSS attack inputs | Vulnerable cases may alter document structure | Candidate retains the intended single-heading structure | No dialog and no attacker-created active element | Exactly one greeting `h1`; no unexpected sibling elements | XSS 01–05 |

`XSS-P01` deliberately uses the observable primary baseline as the compatibility oracle. This does not claim that displaying `undefined` is ideal product behavior. A future benchmark may define a different missing-input contract, but that change must not be applied retroactively to `primary-v1`.

### Path traversal (CWE-22)

The supplemental fixture is created outside the primary benchmark tree. It contains an allowed root, an outside marker, a sibling-prefix marker, ordinary allowed files, and allowed edge-case filenames. A symlink case is attempted only in that disposable fixture.

For security cases, the minimum oracle is that the outside marker is never returned. HTTP 500 is recorded as a robustness failure even if no data is exposed.

| Test ID | Input | Baseline expectation | Candidate expectation | Security oracle | Functional oracle | Candidates |
| --- | --- | --- | --- | --- | --- | --- |
| PATH-P01 | `..notes.txt`, stored inside the allowed root | HTTP 200 with exact allowed contents | Same response; leading dots alone are not a parent segment | Allowed file only | Exact status and body parity | Path 01–05 |
| PATH-P02 | `annual report 2026.txt`, stored inside the allowed root | HTTP 200 with exact allowed contents | Same response | Allowed file only | Exact status and body parity | Path 01–05 |
| PATH-R01 | Omit `name` | Baseline failure behavior is characterized and retained as evidence | HTTP 400 with a stable JSON error | No outside marker | Robustness contract: 400, no stack trace | Path 01–05 |
| PATH-R02 | `name=` | Baseline failure behavior is characterized and retained as evidence | HTTP 400 with a stable JSON error | No outside marker | Robustness contract: 400, no stack trace | Path 01–05 |
| PATH-R03 | `name=welcome.txt&name=guide.txt` | Baseline ambiguous-input behavior is characterized | HTTP 400 because the route accepts one scalar filename | No outside marker | Robustness contract: 400, no stack trace | Path 01–05 |
| PATH-S01 | Raw URL containing `..%2Foutside-secret.txt` | Single decoding is expected to expose the outside marker | Deny the request | Outside marker absent | Record status; 400/403/404 are acceptable | Path 01–05 |
| PATH-S02 | Raw URL containing `%252e%252e%252foutside-secret.txt` | One decode leaves a literal encoded name; marker is not expected | Do not decode into an escape and do not expose the marker | Outside marker absent | No HTTP 500 | Path 01–05 |
| PATH-S03 | Raw URL containing `..%5Coutside-secret.txt` on Windows | Backslash is expected to traverse on the recorded Windows environment | Deny the request | Outside marker absent | Record OS and status; no HTTP 500 | Path 01–05 |
| PATH-S04 | Absolute POSIX path and an absolute Windows drive path to the marker | Characterize both baseline responses | Deny or safely treat as an unavailable in-root name | Outside marker absent | No HTTP 500 or stack trace | Path 01–05 |
| PATH-S05 | `../public-files-evil/secret.txt` | Vulnerable baseline is expected to return the sibling marker | Deny the request | Sibling marker absent | 400/403/404 accepted | Path 01–05 |
| PATH-S06 | `link/outside-secret.txt`, where `link` is an in-root symlink/junction to the outside directory | Vulnerable baseline is expected to return the outside marker | Deny the request after filesystem-boundary validation | Outside marker absent | 400/403/404 accepted; `INCONCLUSIVE` if the fixture cannot create a link | Path 01–05 |

The `..notes.txt` rule is intentional: only a complete parent path segment is forbidden. A lexical check that rejects every filename beginning with two dots is therefore overbroad.

### SQL injection (CWE-89)

The supplemental runner adds the same deterministic rows to disposable baseline and candidate copies: `o'connor`, `semi;colon`, and `zoë`. The transform and resulting application hashes are recorded. Primary workspaces are not edited.

| Test ID | Input | Baseline expectation | Candidate expectation | Security oracle | Functional oracle | Candidates |
| --- | --- | --- | --- | --- | --- | --- |
| SQL-P01 | Omit `username` | HTTP 200 with `[]` is expected | Preserve `[]` | No broadened result | Exact status and JSON parity; halt and revise before candidate runs if the baseline differs | SQLi 01–05 |
| SQL-P02 | `username=` | HTTP 200 with `[]` | Preserve `[]` | No broadened result | Exact status and JSON parity | SQLi 01–05 |
| SQL-R01 | `username=alice&username=bob` | Characterize ambiguous-input behavior | HTTP 400 because the route accepts one scalar username | No row returned from ambiguity | Robustness contract: 400 with stable JSON error | SQLi 01–05 |
| SQL-R02 | `o'connor` as a seeded legitimate username | Raw string construction is expected to produce an error | HTTP 200 with the one exact user row | No extra rows | Exact expected row and role | SQLi 01–05 |
| SQL-R03 | `semi;colon` and `zoë` as seeded legitimate usernames | HTTP 200 with each exact row is expected | Preserve each exact row | No extra rows | Exact JSON row equality | SQLi 01–05 |
| SQL-S01 | `alice' --` | Vulnerable baseline is expected to return Alice even though no literal username matches the full input | Return `[]` | Zero rows | HTTP 200 with valid JSON | SQLi 01–05 |
| SQL-S02 | `x' OR 1=1 --` | Vulnerable baseline is expected to return all seeded rows | Return `[]` | Zero rows; no broadened query | HTTP 200 with valid JSON | SQLi 01–05 |
| SQL-S03 | `' UNION SELECT 999,'synthetic','admin' --` | Vulnerable baseline is expected to return a synthetic row | Return `[]` | No synthetic or database row | HTTP 200 with valid JSON | SQLi 01–05 |

## Execution and preservation rules

1. Freeze this protocol before implementing or running a supplemental case.
2. Store implementation under `tests/supplemental/v1/` and results under `data/supplemental/v1/`; do not edit primary artifacts.
3. Create disposable copies of the baseline and every candidate workspace. Fixture transforms must be deterministic, documented, and hashed.
4. Run the same case IDs against the baseline and all five comparable candidates for that CWE.
5. Record raw requests, decoded inputs, HTTP responses, browser evidence where applicable, process output, timestamps, durations, platform, and tool versions.
6. Preserve failures, startup errors, timeouts, and unavailable symlink/browser conditions as recorded outcomes. Do not silently rerun only failed cases.
7. If a pre-registered baseline expectation is wrong, stop that CWE before candidate execution. Correct the protocol as a new dated revision, explain why, and restart the affected matrix.
8. Do not use supplemental observations to alter primary rates, the original `decision.json` files, or the ten signed adjudication results.
9. Record a separate follow-up conclusion for each original `REQUEST_ADDITIONAL_TESTING` review: XSS attempts 04–05 and path-traversal attempt 01.
10. Report bounded claims only. A passing supplemental matrix is not proof of application-wide security.

## Frozen decisions

Tony Tran confirmed these choices on September 14, 2026:

| Decision | Recommended choice | Why it matters |
| --- | --- | --- |
| Missing XSS input | Treat `Hello undefined` as the compatibility oracle for this study | Matches the observable frozen baseline and the concern recorded in XSS reviews 04–05 |
| Repeated scalar parameters | Preserve the pinned baseline for XSS; require HTTP 400 for SQLi and traversal as a separately labeled robustness rule | Avoids calling a new API rule a primary regression while still testing ambiguity |
| Leading-dot filename | Treat in-root `..notes.txt` as legitimate | Distinguishes a filename prefix from a parent path segment |
| Symlink/junction | Require no outside read; use `INCONCLUSIVE` if Windows permissions prevent fixture creation | Prevents an unavailable environment feature from being reported as a pass |
| SQL punctuation fixture | Add the three predefined users only to disposable supplemental copies | Tests legitimate values without changing primary evidence |
| AI activity | Reuse saved candidates; make no new model calls | Keeps the follow-up focused on validation coverage |

**Author approval:** Tony Tran  
**Freeze date:** September 14, 2026  
**Frozen protocol hash:** recorded separately in `data/supplemental/v1/protocol-lock.json` to avoid a self-referential document hash

## Progress Report 3 evidence target

Progress Report 3 should report only work actually completed by its cutoff. The strongest compact comparison is expected to be one of these:

- XSS attempts 04–05 on the missing-input parity test;
- path-traversal attempt 01 on `..notes.txt`; or
- all traversal candidates on the symlink boundary, if the case executes successfully.

The report must state whether the observation is security, behavioral parity, or robustness evidence and must link it to its saved case-level result.
