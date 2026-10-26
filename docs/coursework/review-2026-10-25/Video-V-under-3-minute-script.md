# FixProof Video V recording script

**Target:** approximately 2 minutes 45 seconds to 2 minutes 55 seconds.  
**Main route:** Slides 1-7.  
**Purpose:** final evidence and reproducibility checkpoint; no new experiment.

## Slide 1 — title (0:00-0:18)

Hi everyone. This is FixProof Video V. Since Video IV, I validated the public
evidence site, rehearsed the package from a clean export, and organized the
final deliverables. This update consolidates results; it adds no experiment.

## Slide 2 — project progression (0:18-0:42)

Video I defined the problem and pilot. Video II completed the frozen
15-candidate primary study. Video III added 140 supplemental observations and
the evidence viewer. Video IV resolved PATH-S06 in WSL2. Today I connect those
results to reproducibility and the final report.

## Slide 3 — orchestration and authority (0:42-1:08)

FixProof's Python code coordinates stages; it does not declare a patch secure.
The model proposes code from a finding and focused context. Python applies it
in a copied workspace and invokes syntax, Semgrep, security, and functional
validators. Policy routes the evidence to reject, ready for review, or human
adjudication. A person records the final rationale. Nothing is automatically
approved or deployed.

## Slide 4 — separated results (1:08-1:35)

The results stay in three layers. Primary-v1 has 15 candidates and 100
observations: five target SAST findings resolved, all candidates passed their
complete primary suites, and 10 produced SAST/runtime disagreement.
Supplemental-v1 has 140 observations: 120 passed, 15 failed, and five were
inconclusive. PATH-S06 adds five conclusive failures. These are different
protocols, not one combined rate.

## Slide 5 — what the evidence changed (1:35-2:05)

Different evidence channels changed the interpretation. Registered XSS attacks
were blocked, but four candidates changed the frozen missing-name behavior and
were rejected for parity. SQLi attacks were blocked, while SQL-R01 remains a
recorded repeated-parameter robustness failure. Direct traversal was rejected,
but all five candidates disclosed the marker through a symbolic link. One pass
did not erase another channel's failure.

## Slide 6 — reproducibility and review (2:05-2:30)

From a clean Git export, all 131 tests passed, evidence bindings verified, and
controlled demo decisions matched the saved records. The public site presents
15 candidates, 245 case rows, and 29 separately labeled human records. It is a
read-only viewer, not a live test runner.

## Slide 7 — conclusion and next steps (2:30-2:58)

My bounded conclusion is that FixProof exposed disagreements, regressions, and
later qualifications in three controlled Express fixtures. It does not estimate
production repair reliability. Next, I will synthesize peer feedback, finish
the final report, generate the release manifest and checksums, and rehearse the
final presentation.

Is one candidate example enough to explain the separation between validators,
policy, and human judgment?

ChatGPT and Codex assisted development, testing, documentation, and drafting. I
validated the evidence and remain responsible for the claims.

## Optional browser transition

If showing the public reference after Slide 6, say:

> This page presents saved evidence for review. The Python project performs the
> validation; the website does not rerun tests or approve candidates.

## Pre-recording checks

- Use the final Video V deck derived from the October 25 outline.
- Keep the main narration under three minutes; use backup slides only for
  questions.
- If demonstrating the public site, verify it in a private browser first.
- Do not expose usernames, machine paths, API response identifiers, or secrets.
- Keep primary, supplemental, and PATH-S06 results visibly separated.
- Do not describe the 131 tests as 131 security attacks; they are repository
  automated tests for implementation and evidence integrity.
- Do not call clean reproduction independent replication.
- Save the posted-video receipt and feedback evidence with the coursework
  artifacts.

