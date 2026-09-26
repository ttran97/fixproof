# FixProof CS6727 validation summary

Validated September 24, 2026. This is a delivery/readiness check; it does not
change frozen primary-v1 evidence or recorded human decisions.

## Current verdict

FixProof is on track for Progress Report 3 and Post Video III. The technical
artifact is about 90% complete as a planning estimate: the bounded workflow,
primary collection, supplemental evaluation, human records, evidence appendix,
presentation deck, and public reference exist. Remaining work is primarily
personal submission review, rehearsal, receipts, and final packaging rather
than another repair feature or CWE.

The broader semester project remains roughly 65% complete as a planning
estimate, not a measured research result or course grade. Later progress
reports, feedback cycles, the final presentation, paper, and reproducible final
archive are still outstanding.

## Verified implementation and evidence

- `python -m fixproof.reproduce --verify` passed with 119 automated tests.
- Primary-v1 verification passed for 15/15 attempts and 10/10 original human
  reviews.
- Supplemental-v1 verification passed for three baselines, 15 saved candidates,
  and all saved candidate bindings.
- There are 14 later human packet/result bindings. XSS 03 intentionally has no
  later follow-up because all nine of its registered supplemental cases passed.
- Frozen primary metrics remain 5/15 target SAST resolutions, 15/15 complete
  registered primary security-suite passes, 15/15 complete registered primary
  functional-suite passes, and 10/15 SAST/runtime disagreements.
- Supplemental candidate-case observations remain 140 total: security 55 pass,
  0 fail, 5 inconclusive; parity 40 pass, 5 fail, 0 inconclusive; robustness 25
  pass, 10 fail, 0 inconclusive. These categories have separate meanings and
  must not be combined into one security success rate.

## Public reference validation

The deployed [FixProof public reference](https://fixproof.netlify.app/) returned
successfully and passed the browser interaction check:

- 15 primary rows and 15 supplemental rows render;
- the case filter reduces each matrix correctly;
- candidate details display primary evidence, case outcomes, patch excerpts,
  and human rationale;
- the public data contain 10 original reviews, 14 later records, and the correct
  140-observation summary;
- referenced CSS, JavaScript, JSON, image, and PDF assets return successfully;
  and
- security headers include a restrictive content policy, frame denial, MIME
  sniffing protection, referrer protection, permissions restrictions, and HSTS.

Netlify attempts two optional inline hosting-layer injections that the site's
content policy blocks. They do not affect the application. Keep the strict
policy instead of allowing inline code. The site is a sanitized, read-only
presentation layer over saved evidence; it does not run tests, call a model,
approve a candidate, or collect student feedback.

## Video III package

- The recording deck has nine slides and speaker notes on all nine slides.
- The PowerPoint package structure passed inspection and the PDF/rendered slides
  were regenerated after adding the public reference.
- The workflow slide distinguishes the frozen primary path from the later
  supplemental qualification path.
- The main demonstration uses one focused XSS comparison. The full 15-candidate
  matrices and rationales remain backup material, avoiding an unreadable main
  presentation.
- The public site should occupy about 60-75 seconds of the video. Filter to
  Reflected XSS and open XSS 04; do not scroll through all 15 candidates.

## Progress Report 3 package

- The September 24 DOCX reflects 14 later records, four completed Video II
  feedback responses, the public reference, the confirmed October 4 deadline,
  and the 16.5-hour September 14-24 estimate supplied by Tony.
- The DOCX package is structurally valid, contains three tables, and rendered to
  seven pages in Word.
- The evaluation keeps primary and supplemental denominators separate and
  explains that XSS/traversal `0/5` target SAST resolution does not mean the
  registered attacks succeeded.
- SQLi bounded acceptances disclose `SQL-R01`; traversal decisions retain the
  unresolved symlink limitation and other registered failures.

## Repository and presentation structure

Use these areas when explaining the project:

| Path | Purpose |
| --- | --- |
| `src/fixproof/` | Python orchestration, validators, policy, evidence, and reports |
| `benchmarks/primary/v1/` | Frozen controlled Express fixtures |
| `data/primary_trials/v1/` | Fifteen original repair attempts and saved evidence |
| `data/primary_reviews/v1/` | Ten original human-review records |
| `data/supplemental/v1/` | Frozen supplemental protocol, saved evaluations, and 14 later human records |
| `tests/` | Implementation checks; 119 passing tests are not 119 repair experiments |
| `ui/` | Local saved-evidence dashboard |
| `fixproof-public/` | Sanitized static presentation reference for Netlify |
| `docs/` | Protocol, results, coursework drafts, slides, and reproducibility guidance |

Keep `.env`, local model-response identifiers, machine paths, credentials,
`.venv`, `node_modules`, and debug logs out of the video and submission archive.
Do not edit frozen primary records to make later results look original.

## Personal checks still required

1. Reconcile any actual September 11-13 work and update the September 14 onward
   hours through the date used in the submitted report. Do not count planned
   future hours as completed work.
2. Open the latest DOCX in Word and personally inspect all seven pages. Confirm
   the timeline-table page break, row wrapping, dates, name/course fields, and
   personal wording before submission.
3. Personally verify every citation and the AI-use disclosure against the tools
   and sources actually used.
4. Submit Progress Report 3 on the intended date, no later than October 4 at
   11:59 p.m., and retain the receipt.
5. Rehearse the five-minute Video III sequence, confirm the deployed site just
   before recording, post by October 6, and retain the October 11 feedback
   receipt.
6. Before the final project package, review the intended tracked/untracked files,
   exclude secrets and temporary Word lock files, and run verification from the
   exact archive or clean snapshot being submitted.

