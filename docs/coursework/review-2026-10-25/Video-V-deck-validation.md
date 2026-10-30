# FixProof Video V deck validation

Validated October 25, 2026 against the frozen FixProof repository evidence,
the corrected Progress Report 5 submission candidate, and the Canvas schedule
supplied by Tony.

## Deliverables

- PowerPoint: `FixProof - Video V - Final Evidence Checkpoint.pptx`
- PDF: `FixProof - Video V - Final Evidence Checkpoint.pdf`
- Speaker script: `Video-V-under-3-minute-script.md`
- Slide outline: `Video-V-PowerPoint-outline.md`
- Rendered slides: `video-v-rendered-slides/`
- Contact sheet: `Video-V-contact-sheet.png`
- Package verification: `Video-V-deck-verification.json`
- Rebuild script: `build-video-v-deck.ps1`

## Structure and timing

- Seven slides and seven speaker-note pages are present.
- The main narration contains 378 words, approximately 2.8 minutes at 135
  words per minute.
- The PDF contains seven nonblank pages.
- Slide and note XML contains no replacement-character/mojibake marker.
- The PowerPoint and PDF SHA-256 values are stored in the verification JSON.

## Evidence checks

- Slide 2 accurately traces the progression from the pilot through primary-v1,
  supplemental-v1, PATH-S06, and the final reproducibility checkpoint.
- Slide 3 states that Python coordinates stages, validators measure, policy
  routes, and a human records the final rationale. It makes no automatic
  approval or deployment claim.
- Slide 4 keeps the three denominators separate: 100 primary observations, 140
  supplemental observations, and five PATH-S06 extension observations.
- Slide 4 accurately reports 15 candidates, 5/15 target-SAST resolution, 15/15
  primary-suite completion, 10 SAST/runtime disagreements, supplemental
  120/15/5 pass/fail/inconclusive, PATH-S06 0/5/0, and 29 human records.
- Slide 5 accurately distinguishes XSS security from parity, SQLi security and
  parity from SQL-R01 robustness, and direct traversal rejection from the
  PATH-S06 symbolic-link failure.
- Slide 6 accurately reports the clean Git export, fresh Python environment,
  six Node dependency trees restored from lockfiles, 131 repository tests,
  controlled demo decisions, and the read-only public viewer counts.
- Slide 7 states the bounded conclusion and does not claim production repair
  reliability, scanner accuracy across repositories, or application-level
  generalization.
- Slide 7 accurately summarizes the October 25 Video IV feedback: the existing
  PATH-S06 audit trail is retained, a second fixture is identified as future
  work, and the author-run clean rehearsal is not described as independent.
- Slide 7 uses the supplied Canvas milestones: Report 5 on November 1, Video V
  on November 3, final presentation on November 15, and final report on
  December 6.

## Visual inspection

All seven 1600-by-900 renders were reviewed individually and as a contact
sheet. Titles, cards, arrows, labels, footers, and slide numbers are visible;
no text is clipped; no shapes overlap unexpectedly; and the navy, blue,
orange, purple, and green evidence-layer colors remain consistent with Videos
III and IV.

The densest slides are Slides 3 through 6, but their main claims remain readable
at full-screen presentation size. The complete candidate matrix and raw
request/response evidence remain backup materials rather than main-slide
content.

## Recording guidance

1. Rehearse once from the embedded speaker notes and remain near 135 words per
   minute.
2. Present Slides 1-7 in order; do not add the full 15-candidate appendix to the
   main route.
3. If demonstrating the public site, use no more than 15 seconds and state that
   it is a read-only viewer of saved evidence.
4. Do not describe the 131 repository tests as 131 security attacks.
5. Keep primary-v1, supplemental-v1, and PATH-S06 results separate in speech.
6. Verify the exported recording and retain the Video V posting receipt.

