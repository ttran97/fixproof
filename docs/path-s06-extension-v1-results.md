# FixProof PATH-S06 Extension v1 Results

**Protocol:** `path-s06-extension-v1`  
**Execution date:** September 30, 2026  
**Run ID:** `20260930T180925912688Z-path-s06-v1`  
**Run status:** Complete and hash-verified

## Scope

This separately versioned extension executed only the previously inconclusive
`PATH-S06` symbolic-link escape case. It used the vulnerable baseline and the
same five saved primary-v1 traversal candidates. It made no model calls and did
not rerun SAST. The original `supplemental-v1` outcomes and its 140-observation
matrix remain unchanged.

The frozen candidate pass rule required both conditions: the controlled outside
marker had to be absent, and the response status had to be exactly HTTP 400,
403, or 404.

## Environment

- WSL2 Ubuntu, Linux `6.6.87.2-microsoft-standard-WSL2`, x86-64
- Python 3.12.3 orchestration
- Native Linux Node.js 24.19.0 and npm 11.17.0
- Dependencies restored from the committed lockfile with `npm ci`
- Application workspaces and symbolic-link fixtures created in disposable
  Linux-native temporary directories

Python 3.12.3 differs from the project's declared Python 3.11 range. The
extension runner used only Python's standard library, and the application
runtime matched the recorded Node.js and npm versions. This difference is
disclosed rather than treated as an unrecorded equivalence claim.

## Recorded outcomes

| Target | HTTP | Outside marker | Registered outcome |
| --- | ---: | --- | --- |
| Vulnerable baseline | 200 | Disclosed | Baseline gate passed |
| Traversal 01 | 200 | Disclosed | Fail |
| Traversal 02 | 200 | Disclosed | Fail |
| Traversal 03 | 200 | Disclosed | Fail |
| Traversal 04 | 200 | Disclosed | Fail |
| Traversal 05 | 200 | Disclosed | Fail |

Candidate extension totals: **0 pass, 5 fail, 0 inconclusive**. The baseline is
a control gate and is not included in that five-candidate denominator.

## Interpretation

All five saved candidates checked only the lexical path computed from the
request. That check kept `public-files/link/outside-secret.txt` textually under
the allowed root, but `fs.readFile` followed `link` to the directory outside
the root. Each candidate therefore returned the controlled outside-file marker
with HTTP 200. This is evidence of an exploitable symbolic-link traversal in
the registered case, not merely a failure to return a preferred error code.

The automated result did not itself make a human acceptance decision. On
September 30, Tony reviewed the frozen protocol, baseline gate, run summary,
and all five candidate records and approved separate
`FOLLOW_UP_REJECT_CANDIDATE` qualifications for Traversal 01-05. Traversal 01's
earlier rejection is reaffirmed; Traversal 02-05 now have later rejection
qualifications while their earlier request-more-testing records remain
preserved. Tony also manually reproduced Traversal 02 in WSL2; that spot-check
supports his review but is not added to the registered extension counts.

## Integrity checks

- The frozen protocol, case definition, and runner bindings verified before
  execution.
- The vulnerable baseline disclosed the exact controlled marker before any
  candidate was judged.
- Every baseline and candidate result is bound by SHA-256 in the run summary.
- Before/after tree fingerprints confirm that `data/primary_trials/v1/` and
  `data/supplemental/v1/` were unchanged.
- Primary evidence reverified at 15/15 attempts and 10/10 original reviews.
- Supplemental-v1 reverified at three baselines, 15 candidates, and 14/14
  existing later human records.
- PATH-S06 extension human qualifications verified at 5/5 complete. All five
  are separately bound to the approval, review packet, candidate result, and
  preserved prior follow-up.

## Evidence locations

- Frozen protocol: `docs/path-s06-extension-v1-protocol.md`
- Protocol lock: `data/extensions/path-s06-v1/protocol-lock.json`
- Machine-readable case: `tests/extensions/path_s06/v1/case.json`
- Run summary:
  `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/summary.json`
- Environment record:
  `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/environment.json`
- Protected-data check:
  `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/protected-data-integrity.json`
- Human approval: `data/extensions/path-s06-v1/human-review-approval.json`
- Human qualification records: `data/extensions/path-s06-v1/human-reviews/`

