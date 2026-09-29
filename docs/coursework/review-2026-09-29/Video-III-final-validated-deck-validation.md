# Video III final deck validation

Validated September 29, 2026 against the current FixProof repository.

## Recording files

- `FixProof - Video III - Final Validated Recording Deck.pptx`
- `FixProof - Video III - Final Validated Recording Deck.pdf`
- `Video-III-outline-and-script.md`
- `video-iii-final-validated-rendered-slides/Slide1.PNG` through `Slide9.PNG`

The supplied reviewed deck remains unchanged. The final validated deck is a
separate recording copy.

## Evidence validation

- Primary check: 15 of 15 initial attempts verified; 10 of 10 original conflict
  reviews complete.
- Supplemental check: three baselines and 15 saved candidates verified.
- Primary metrics: 15 calls; 5/15 target-SAST resolutions; 15/15 complete
  primary security-suite passes; 15/15 complete primary functional-suite
  passes; 10/15 SAST/runtime disagreements.
- Supplemental metrics: security 55 pass, zero fail, five inconclusive; parity
  40 pass and five fail; robustness 25 pass and 10 fail; 140 case-level
  observations total.
- Human records: 10 original reviews and 14 later records. The later records are
  five rejections, five bounded SQLi acceptances, and four traversal requests
  for more testing. No primary record or metric is overwritten.

## Presentation validation

- Nine slides and nine speaker-note sections are present.
- All nine slides rendered successfully at 1600 by 900. Slides 2, 3, and 8
  were re-inspected after the final edits; the remaining slides are unchanged
  from the previously reviewed render.
- No mojibake or obsolete `Fixed generation`, `Separate authority`, or
  second-reviewer wording remains in the PowerPoint package.
- Slide 2 now explains the controlled model setup in plain language: the model
  received the frozen prompt and proposed code but could not run tools or tests.
  Five initial calls were scheduled per fixture, for 15 calls total; these are
  repeated repairs of three applications, not 15 independent applications.
- Slide 3 distinguishes the three policy paths: all automated outcomes go to
  the primary record, selected cases branch to human review, and primary
  evidence plus supplemental outcomes inform later follow-up. The lower flow
  does not rewrite primary-v1.
- Slide 8 presents a bounded Progress Report 4 plan and asks a concrete feedback
  question about adding another vulnerable application versus completing the
  Windows-blocked path-traversal test.
- The main narration is approximately 675 words, or about 4.8 to 5.2 minutes at
  140 to 130 spoken words per minute. Slide 9 remains a Q&A backup.

## Test caveat

The repository's primary and supplemental evidence check commands pass. A
separate targeted `pytest` attempt could not copy the open PowerPoint temporary
lock file (`~$FixProof - Video III - Reviewed Recording Deck.pptx`) into its
test fixture. That is an Office file-lock condition, not an evidence-check or
FixProof implementation failure. Close the source deck before rerunning that
optional test command.

## Recording recommendation

Use slides 1 through 8 for the main recording. On Slide 6, briefly open the
public site, filter to Reflected XSS, and inspect XSS 04. Return to Slide 7 for
the XSS 03 versus XSS 04 comparison. Keep Slide 9 and raw evidence paths as
Q&A backups rather than showing them during the main five-minute narration.
