# FixProof Post Video V PowerPoint outline

Prepared October 25, 2026. Target: seven main slides and approximately three
minutes. This is a final-project checkpoint, not a new experiment. The primary,
supplemental, and PATH-S06 evidence remain frozen and separately reported.

## Presentation through-line

Video V should answer one question: **What does the completed FixProof evidence
support, and how can another reviewer inspect or reproduce it?**

The chronological connection to earlier coursework is:

1. Video I / Progress Report 1: defined the problem, research question, three
   CWEs, and pilot pipeline.
2. Video II / Progress Report 2: completed and reviewed the 15-attempt frozen
   primary study.
3. Video III / Progress Report 3: evaluated the same candidates with 140
   supplemental observations and published the evidence viewer.
4. Video IV / Progress Report 4: resolved the Windows-inconclusive PATH-S06
   case in a separately versioned WSL2 extension.
5. Video V / Progress Report 5: demonstrates traceability, clean reproduction,
   claim boundaries, and final-deliverable readiness.

## Main slides

| Slide | Title | On-screen content | Visual and repository evidence | Speaking goal |
| ---: | --- | --- | --- | --- |
| 1 | **FixProof: final evidence checkpoint** | Subtitle: "From AI-proposed patch to reviewable evidence"; Video V; Tony Tran; CS6727 | Use the same navy/light-blue design as Videos III-IV | State that this update consolidates results and reproducibility; it does not add a new experiment |
| 2 | **How the project progressed** | Five-step timeline: problem/pilot; primary-v1; supplemental-v1; PATH-S06; reproducible package | Refer to Video I-IV and Progress Reports 1-4; keep each step to one line | Show a chronological research progression rather than a list of disconnected activities |
| 3 | **Python coordinates; separate authorities decide** | `Fixture + finding -> model proposal -> copied workspace -> validators -> deterministic policy -> human record`; note "No automatic approval or deployment" | `src/fixproof/primary_trials.py`; `src/fixproof/validation/`; `data/primary_trials/v1/`; `data/primary_reviews/v1/` | Explain that Python invokes stages and writes artifacts; validators measure, policy routes, and a human records acceptance or follow-up |
| 4 | **Three evidence layers, three denominators** | Primary-v1: 15 candidates, 100 observations; supplemental-v1: 140 observations, 120/15/5 P/F/I; PATH-S06: 5 observations, 0/5/0 P/F/I; 29 separately labeled human records | `data/evaluation/primary-report.json`; `data/supplemental/v1/supplemental-report.json`; `data/extensions/path-s06-v1/.../summary.json` | Prevent the audience from pooling categories into one security rate |
| 5 | **What the evidence changed** | Three rows: XSS—attacks blocked, four missing-name parity failures; SQLi—injection cases passed, SQL-R01 disclosed; traversal—direct `../` rejected, PATH-S06 marker disclosed by all five | Use one request/response example only; keep full candidate matrix in the public reference/appendix | Demonstrate why attack blocking, behavior preservation, robustness, and later qualification are separate decisions |
| 6 | **Reproducible and reviewable package** | Clean export; fresh environments/dependencies; 131 tests passed; live artifact hashes matched; public viewer: 15 candidates, 245 case rows, 29 human records | `scripts/verify-clean.ps1`; `docs/coursework/review-2026-10-22/`; `https://fixproof.netlify.app/`; `final-deliverable/` | Show that the evidence can be inspected and the package can be rehearsed without rerunning model generation |
| 7 | **Bounded conclusion and next milestones** | Supported: auditable decisions for registered cases. Not supported: a production repair-success rate. Video IV feedback: retain the PATH-S06 audit trail, treat a second fixture as future work, and do not label the author-run rehearsal independent. Next: self-contained final report, manifest/checksums, final presentation rehearsal | `docs/coursework/review-2026-10-25/Video-IV-peer-feedback-disposition.md`; `final-deliverable/01-final-report/` through `04-manifest-and-checksums/` | Close with the contribution, limitations, feedback disposition, next work, one new clarity question, and AI-use disclosure |

## Recommended Slide 4 table

| Layer | Scope | Result shown |
| --- | --- | --- |
| Primary-v1 | 15 saved candidates; 40 security + 60 functional observations | 15/15 candidates passed complete primary security and functional suites; target SAST resolved for 5/15; 10/15 required adjudication because SAST and runtime evidence disagreed |
| Supplemental-v1 | Same 15 candidates; 140 new registered observations | 120 pass, 15 fail, 5 inconclusive across separately labeled security, parity, and robustness categories |
| PATH-S06 extension-v1 | Five saved traversal candidates; one Linux symbolic-link case each | 0 pass, 5 fail, 0 inconclusive |

Do not add the 100, 140, and five observations into one success percentage.
Their protocols and decision rules differ.

## Recommended Slide 5 table

| CWE | What passed | What later evidence added | Bounded interpretation |
| --- | --- | --- | --- |
| Reflected XSS | Registered attack cases | XSS 01, 02, 04, and 05 failed XSS-P01 missing-name parity | Security repair evidence remained, but four candidates were rejected for exact behavioral parity |
| SQL injection | Primary and supplemental injection cases; supplemental parity | All five identical saved sources failed SQL-R01 repeated-parameter handling | Bounded injection repair accepted with the robustness limitation disclosed |
| Path traversal | Registered direct parent-segment request | PATH-S06 returned HTTP 200 and disclosed the marker for all five candidates | Direct rejection did not prove symbolic-link target containment; all five received later rejection qualifications |

## Optional live demonstration

If the course video permits a 15-second browser segment, open
`https://fixproof.netlify.app/`, show the three evidence-layer filters, and open
one candidate. Say explicitly that the site is a read-only viewer of saved
evidence; it does not run a model, scanner, application, attack, approval, or
deployment.

## Backup slides only

1. Repository structure and exact evidence paths.
2. XSS 03 versus XSS 04 missing-name behavior.
3. Traversal 02 direct request versus PATH-S06 response.
4. Full 15-candidate matrix and human-rationale reference.
5. Clean-reproduction environment and dependency-advisory limitation.

## Feedback question

> For the final presentation, is the separation between validator results,
> deterministic routing, and the later human decision clear from one candidate
> example, or should I spend more time on the evidence-layer diagram?

This asks for actionable communication feedback without proposing a new broad
experiment at the end of the course.

## Accuracy rules for the slides

- Say "15 model calls" or "15 candidates," not 15 independent applications.
- Say primary candidate suites passed; do not turn 15/15 into a production
  security-success rate.
- Keep primary-v1, supplemental-v1, and PATH-S06 extension counts separate.
- Describe the vulnerable PATH-S06 baseline as a positive-control gate, not a
  secure pass.
- Describe SQL-R01 as a registered robustness failure even though the bounded
  injection repair was accepted.
- Describe the four XSS follow-up rejections as parity decisions, not proof
  that the registered XSS payloads remained exploitable.
- Say the public website displays saved evidence and the Python project runs
  validation; do not call the website a live testing dashboard.
- Do not claim independent replication. The completed activity was a clean
  reproduction rehearsal of the same frozen snapshot.

