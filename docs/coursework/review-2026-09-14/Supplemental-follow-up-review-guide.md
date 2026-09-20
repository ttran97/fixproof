# Supplemental follow-up review guide

Use this guide after reading `docs/supplemental-results-v1.md`. The commands record new follow-up conclusions only; they do not change the original `primary-v1` review results or metrics.

## Verified evidence checkpoint

- 3 supplemental baselines characterized.
- 15 saved candidates evaluated.
- 140 candidate-case observations: 120 pass, 15 fail, and 5 inconclusive.
- Security category: 55 executable passes, 0 failures, and 5 inconclusive symlink cases.
- Repository suite: 111 tests passed on September 14.

## Review 1: XSS attempt 04

Relevant evidence:

- All three supplemental security cases passed.
- Four of five behavioral-parity cases passed.
- `XSS-P01` demonstrated HTTP 200 with heading text `Hello ` instead of the frozen baseline `Hello undefined`.
- The entity-looking-input robustness case passed.

Under the frozen strict-preservation criterion, `FOLLOW_UP_REJECT_CANDIDATE` is the most consistent conclusion. This is a functional-parity conclusion; it is not evidence that the candidate remains exploitable by the registered XSS attacks.

Suggested rationale to review and rewrite in your own words:

> I reviewed the candidate patch, all nine supplemental XSS outcomes, and the original review. The candidate passed all three supplemental security cases and the entity-looking-input check. However, XSS-P01 confirmed that an omitted name changes from the baseline text "Hello undefined" to "Hello ". Because the frozen supplemental protocol treats that observable output as required behavioral parity, I reject this candidate for the bounded benchmark. This decision is based on the demonstrated behavior change, not on the persistent SAST warning, and it does not claim that the tested XSS payloads remain exploitable.

Record only after personally confirming the packet and result:

```powershell
$trial = "primary-v1-xss-initial-04"
$packet = "data/supplemental/v1/follow-up-reviews/$trial/packet.json"
$output = "data/supplemental/v1/follow-up-reviews/$trial/result.json"
$rationaleFile = "dist/follow-up-rationale-xss-04.txt"

$rationale = Read-Host "Enter your evidence-based follow-up rationale for XSS 04"
$rationale | Set-Content -LiteralPath $rationaleFile -Encoding UTF8

$env:PYTHONPATH = (Resolve-Path .\src).Path
& .\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_followup record `
    --project-root . `
    --packet $packet `
    --output $output `
    --reviewer "Tony Tran" `
    --verdict FOLLOW_UP_REJECT_CANDIDATE `
    --rationale-file $rationaleFile `
    --confirm-all-required-checks
```

## Review 2: XSS attempt 05

XSS attempt 05 has the same registered outcome pattern as attempt 04: 3/3 security, 4/5 parity, and 1/1 robustness, with `XSS-P01` as the sole failure. Apply the same decision criterion, but personally review its distinct patch and result before recording.

Use the preceding command with these substitutions:

```powershell
$trial = "primary-v1-xss-initial-05"
$rationaleFile = "dist/follow-up-rationale-xss-05.txt"
```

## Review 3: path-traversal attempt 01

Relevant evidence:

- All five executable supplemental security cases passed.
- `PATH-S06` is inconclusive because Windows did not permit creation of the symlink fixture.
- `PATH-P01` failed: the candidate returned HTTP 400 for the legitimate in-root file `..notes.txt`.
- `PATH-R03` failed: repeated filenames returned HTTP 404 instead of the predefined HTTP 400 scalar-input response.

Under the frozen criteria, `FOLLOW_UP_REJECT_CANDIDATE` is the most consistent conclusion. The two demonstrated failures are sufficient to reject the current candidate even though the separate symlink case remains inconclusive.

Suggested rationale to review and rewrite in your own words:

> I reviewed the candidate patch, all eleven supplemental traversal outcomes, and the original review. The candidate passed all five executable security cases, but the symlink-boundary case remains inconclusive because the Windows fixture could not be created. The candidate also returned HTTP 400 for the legitimate in-root file "..notes.txt" and HTTP 404 rather than the predefined HTTP 400 response for repeated filenames. These results confirm an overbroad filename check and a robustness-contract failure. I reject this candidate for the bounded benchmark while preserving the symlink result as inconclusive.

Record after confirmation:

```powershell
$trial = "primary-v1-path-traversal-initial-01"
$packet = "data/supplemental/v1/follow-up-reviews/$trial/packet.json"
$output = "data/supplemental/v1/follow-up-reviews/$trial/result.json"
$rationaleFile = "dist/follow-up-rationale-path-01.txt"

$rationale = Read-Host "Enter your evidence-based follow-up rationale for traversal 01"
$rationale | Set-Content -LiteralPath $rationaleFile -Encoding UTF8

$env:PYTHONPATH = (Resolve-Path .\src).Path
& .\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_followup record `
    --project-root . `
    --packet $packet `
    --output $output `
    --reviewer "Tony Tran" `
    --verdict FOLLOW_UP_REJECT_CANDIDATE `
    --rationale-file $rationaleFile `
    --confirm-all-required-checks
```

## Verify a recorded conclusion

```powershell
$result = Get-Content -Raw -LiteralPath $output | ConvertFrom-Json
$result | Format-List status, trial_id, verdict, reviewer, reviewed_at, rationale
```

The current supplemental report is bound into these packets and must not be overwritten after recording a conclusion. After all three results exist, create a separate verified follow-up summary artifact. Do not manually insert verdict counts into the existing machine-readable report.
