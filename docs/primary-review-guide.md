# Reviewing the ten primary disagreements

Ten packets were prepared initially. Consult the generated primary report for
the current completion count; results are recorded separately by the reviewer.

| Case | Trials requiring review | Packet directory |
|---|---|---|
| Reflected XSS | `primary-v1-xss-initial-01` through `05` | `data/primary_reviews/v1/<trial-id>/` |
| Path traversal | `primary-v1-path-traversal-initial-01` through `05` | `data/primary_reviews/v1/<trial-id>/` |

Start the verified dashboard with `python -m fixproof.reproduce --serve` in
the project environment, then open `/ui/primary.html`. Select a trial and
inspect these four evidence groups:

1. **Candidate patch:** compare baseline and candidate behavior; look for
   unrequested removal of functionality or assumptions the tests do not cover.
2. **SAST finding and provenance:** inspect the target rules, warning location,
   and candidate source. A persistent warning with passing tests is a conflict
   to investigate, not automatically a false positive.
3. **Targeted security observations:** inspect payloads, response status/body,
   and XSS browser execution observations. Consider relevant cases outside
   the small fixed test set.
4. **Functional observations:** check which normal inputs were tested and
   whether their expected behavior is appropriate.

Record one of `ACCEPT_CANDIDATE`, `REJECT_CANDIDATE`, or
`REQUEST_ADDITIONAL_TESTING`, with a concrete rationale. Acceptance is a
review conclusion within the controlled scope, not a production-security
guarantee. If you cannot justify a verdict from the evidence, request further
testing and describe what is missing.

The existing CLI validates the evidence bindings and requires explicit
confirmation that the four review checks were actually completed:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.adjudication record --help
```

For the first XSS trial, the input packet is:

```text
data/primary_reviews/v1/primary-v1-xss-initial-01/packet.json
```

Use that directory's `result.json` as the output. Supply your real reviewer
identity, your chosen verdict, and your own rationale. The required flag
`--confirm-all-required-checks` is an attestation by the reviewer; do not use
it before doing the review. The command records the current timestamp unless
an explicit offset-aware review timestamp is provided. It refuses to overwrite
an existing result or the packet.

After recording a result, regenerate the report:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.primary_report
```

### Windows PowerShell: rationale containing quotes

Use `--rationale-file` when review text contains quotation marks. Older Windows
PowerShell can change embedded quotes when passing text to a native executable.
After personally reviewing a trial, save your own rationale as UTF-8:

```powershell
$reviewRationale = Read-Host "Enter your evidence-based rationale"
$reviewRationale | Set-Content -LiteralPath .\dist\review-rationale.txt -Encoding UTF8
```

The `dist` directory must exist first (`New-Item -ItemType Directory -Force dist`).
In the record command, replace `--rationale "$reviewRationale"` with
`--rationale-file "dist/review-rationale.txt"`. The command reads and embeds
the text in `result.json`; the temporary text file is not an evidence dependency.
The verdict and confirmation requirements remain unchanged. This option accepts
UTF-8 with or without the BOM produced by Windows PowerShell.

The report discovers the result at the trial's fixed review path, verifies its
packet binding, and updates the human-review column and completion count.
The automated decision and the primary outcome metrics remain unchanged.
Requesting additional testing completes the act of review; it does not mean
the candidate was accepted or that the requested follow-up work is complete.

If new evidence is collected after review, keep it separate and document a
follow-up review/version. Do not overwrite a result or retroactively change
the frozen primary tests. A manual edit to a bound packet invalidates its
existing result binding.
