# FixProof Video IV deck validation

Validated October 21, 2026 against the recorded FixProof repository evidence.
The deck is a seven-slide, approximately five-minute PATH-S06 update. It does
not claim that Progress Report 4, peer feedback, the public-site update, or the
clean-package rehearsal is complete because no newer supporting artifact was
available in the repository.

## Deliverables

- PowerPoint: `FixProof - Video IV - PATH-S06 Recording Deck.pptx`
- PDF: `FixProof - Video IV - PATH-S06 Recording Deck.pdf`
- Rendered slides: `video-iv-rendered-slides/`
- Contact sheet: `Video-IV-contact-sheet.png`
- Under-three-minute script: `Video-IV-under-3-minute-script.md`
- Package verification: `Video-IV-deck-verification.json`
- Rebuild script: `build-video-iv-deck.ps1`

## Evidence checked

- `docs/path-s06-extension-v1-protocol.md`
- `docs/path-s06-extension-v1-results.md`
- `data/extensions/path-s06-v1/protocol-lock.json`
- `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/summary.json`
- Traversal 02 candidate result under the same run directory
- `data/extensions/path-s06-v1/human-review-approval.json`
- `docs/coursework/review-2026-09-30/PATH-S06-extension-human-review.md`
- `docs/coursework/review-2026-10-01/FixProof-student-evidence-validation.json`

## Accuracy checks

- The original supplemental `PATH-S06` result is described as inconclusive
  because the Windows environment could not create the registered link fixture.
- HTTP 400 for Traversal 02's direct `../../` request is described as the
  desired rejection, not as a security risk.
- The security failure is the registered symbolic-link request returning HTTP
  200 with `FIXPROOF_CONTROLLED_TRAVERSAL_SECRET`.
- The vulnerable baseline is a gate and is excluded from the five-candidate
  denominator.
- Candidate totals match the bound summary: zero pass, five fail, and zero
  inconclusive.
- The extension is labeled as a separate later evidence layer with no new
  model calls and no SAST reruns.
- Primary-v1 and supplemental-v1 are described as preserved rather than
  rewritten.
- Traversal 02 is the only candidate described as manually reproduced.
- The conclusion is bounded to the registered symbolic-link case and does not
  claim application-wide security or a production repair-success rate.

## CS6727 alignment

- The problem, selected method, oracle, environment, and excluded alternatives
  are explained rather than presented as unsupported choices.
- The deck distinguishes automated observations from human qualifications.
- It shows a concrete request, response, output, and interpretation instead of
  relying only on summary percentages.
- Limitations and generalization boundaries are stated on the main slides.
- The final speaker notes contain the AI-use disclosure and Tony's responsibility
  for evidence review and submitted claims.
- The closing feedback question asks for an actionable comparison between
  independent reproduction and one additional controlled fixture.

## Package and visual verification

- PowerPoint package contains seven slides and seven speaker-note pages.
- The synchronized speaker notes contain 370 words, approximately 2 minutes
  51 seconds at 130 words per minute.
- Required evidence labels and interpretation terms are present.
- Slide and note XML contains no detected replacement or mojibake characters.
- PDF and 1600x900 PNG renders were generated successfully.
- All seven rendered slides were inspected. Text is readable, cards do not
  overlap, result colors are consistent, and the direct-versus-symlink
  distinction is visible without relying on narration alone.

## Personal checks before posting

1. Open the PowerPoint in Slide Show mode and rehearse from the speaker notes.
2. Add any actual peer-feedback update verbally only if it has been received
   and documented; do not invent a feedback result.
3. Confirm the live Canvas Video IV and peer-feedback instructions.
4. Verify the public evidence page before demonstrating it. The deck itself
   does not depend on the live site.
5. Save the posting receipt or screenshot with the coursework artifacts.
