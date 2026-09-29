# Video III reviewed deck validation

Validated September 29, 2026 against the current FixProof repository.

## Deliverables

- `FixProof - Video III - Reviewed Recording Deck - Report 4 Feedback.pptx`
- `FixProof - Video III - Reviewed Recording Deck - Report 4 Feedback.pdf`
- `video-iii-reviewed-rendered-slides/Slide1.PNG` through `Slide9.PNG`
- `Video-III-outline-and-script.md`

The supplied final deck was preserved. The reviewed deck is a separate file.

## Evidence checks

- `python -m fixproof.evaluation.primary_report --check`: 15 of 15 primary
  attempts verified; 10 of 10 conflict reviews complete.
- `python -m fixproof.evaluation.supplemental_report --check`: three baselines
  and 15 saved candidates verified.
- `pytest` for the primary and supplemental report modules: 15 tests passed.
- Follow-up records: 14 total — five reject, five accept under a bounded
  criterion, and four request more testing.
- Trial metadata confirms `gpt-5.2`, prompt template `1.0`, and five planned
  attempts per CWE.
- The supplemental runner copies the saved candidate to a disposable directory,
  launches that copy's `app.js`, and binds to `127.0.0.1`.

## Deck checks

- Nine slides and nine speaker-note sections are present.
- All nine slides were rendered at 1600 by 900 and visually inspected.
- The main narration is 698 words, approximately 5.0 to 5.4 minutes at 140 to
  130 words per minute; slide 9 remains backup only.
- Primary metrics shown in the deck match `data/evaluation/primary-report.json`:
  15 calls, 5/15 target-SAST resolutions, 15/15 primary security-suite passes,
  15/15 primary functional-suite passes, and 10/15 SAST/runtime disagreements.
- Supplemental metrics match `docs/supplemental-results-v1.md`: security
  55 pass, 0 fail, 5 inconclusive; parity 40 pass, 5 fail; robustness 25 pass,
  10 fail; 140 candidate-case observations total.
- XSS 03 and XSS 04 wording distinguishes attack blocking from exact behavioral
  parity. XSS 04 is described as a parity rejection, not an exploitable-XSS
  result.
- The workflow now says `Frozen case registry` and explicitly identifies it as
  internal; the deck does not claim an external public preregistration.
- Slide 6 identifies the tested application as the saved candidate `app/app.js`
  launched on localhost in a disposable copy. It also states that Netlify is a
  read-only evidence viewer, not a test runner.
- The Report 3 deadline was removed from the current-milestones list because the
  report was already submitted. The slide now identifies the October 6/11 Video
  III cycle, the October 18 Report 4 deadline, and Report 4's immediate scope.
- The earlier second-reviewer question was replaced with an actionable Report 4
  choice: add a second fixture or resolve PATH-S06 on a symlink-capable system.

## Recording recommendation

Use slides 1 through 8 for the main recording. Keep slide 9 as a Q&A backup.
When switching to the public site, open Reflected XSS / XSS 04 and return to
slide 7 for the XSS 03 versus XSS 04 comparison.
