# FixProof documentation and repository guide

Updated September 24, 2026. Start with [prototype status](prototype-status.md)
for current capabilities and remaining work. Use
[the submission guide](cs6727-submission-guide.md) to understand the source
tree, explain the project, and prepare the paper and presentation.

## Active references

| Document | Purpose |
|---|---|
| [Report 3 readiness assessment](coursework/review-2026-09-21/CS6727-Progress-Report-3-readiness.md) | Current evidence, file map, syllabus/feedback alignment, remaining work and deadlines |
| [Report 3 writing starter](coursework/review-2026-09-21/Progress-Report-3-writing-starter.md) | Verified progress text to adapt into the required template with actual dates/hours |
| [Report 3 full draft](coursework/review-2026-09-21/Progress-Report-3-draft.md) | Full working report with verified results and clearly marked personal fields |
| [Report 3 working DOCX](<coursework/review-2026-09-21/Progress Report 3 (Tony Tran) - Working Draft September 24 - Website and Feedback Aligned.docx>) | Report 2-format document updated through September 24, 14 verified supplemental human records, four completed Video II feedback responses, and the public reference site; inspect in Word and complete personal fields before submission |
| [Report 3-to-final roadmap](coursework/review-2026-09-21/Progress-Report-3-to-final-roadmap.md) | Dated coursework tasks, file-structure audit, and bounded final-video demo plan |
| [Video III final outline](coursework/review-2026-09-24/Video-III-final-outline.md) | Recording-ready chronological structure, public-dashboard demonstration, feedback question, and claim checks |
| [Video III recording deck](<coursework/review-2026-09-22/FixProof - Video III - Recording Deck.pptx>) | Nine-slide presentation aligned with the frozen primary study, supplemental evidence, human decisions, and current public reference |
| [September 24 validation summary](coursework/review-2026-09-24/CS6727-validation-summary.md) | Repository, public-site, deck, report, metrics, and remaining personal checks |
| [Video III 15-candidate evidence appendix](coursework/review-2026-09-22/Video-III-15-candidate-evidence-appendix.pdf) ([HTML](coursework/review-2026-09-22/Video-III-15-candidate-evidence-appendix.html)) | Backup matrices with all ten original primary and 14 supplemental human rationales; distinguishes bounded acceptance from failed robustness cases |
| [September 22 follow-up review worksheet](coursework/review-2026-09-22/remaining-follow-up-review-worksheet.md) | Source-linked rationale and patch excerpts used for five SQLi bounded acceptances and four traversal requests for more testing |
| [Slide-ready workflow chart](coursework/review-2026-09-22/fixproof-workflow-slide.svg) ([PDF](coursework/review-2026-09-22/fixproof-workflow-slide.pdf), [PNG](coursework/review-2026-09-22/fixproof-workflow-slide.png)) | Primary repair workflow and later supplemental qualification, shown as separate evidence tracks |
| [XSS 01–02 review record](coursework/review-2026-09-21/XSS-01-02-supplemental-review-checklist.md) | Human-readable summary of the two September 21 consistency qualifications |
| [Supplemental results](supplemental-results-v1.md) | Category-specific outcomes and all 14 later human decisions, kept separate from frozen primary metrics |
| [Prototype status](prototype-status.md) | Current implementation, limits, and next milestone |
| [September 13 checkpoint / Video II](coursework/review-2026-09-13/Current-progress-and-next-steps.md) | Historical checkpoint: ten reviews, 89-test verification, reviewed PowerPoint/narration |
| [September 12 assessment / Report 2](coursework/review-2026-09-12/FixProof-assessment.md) | Historical Report 2 audit, revised DOCX, and feedback mapping |
| [Understanding and defending FixProof](fixproof-understanding-and-defense.md) | Concepts, live/recorded demo distinctions, reference-to-claim map, and professor questions |
| [Primary results](primary-results.md) | Generated 15-attempt results; regenerate rather than manually edit |
| [Primary review guide](primary-review-guide.md) | Personally inspect and record the ten conflict reviews |
| [Submission guide](cs6727-submission-guide.md) | File structure, professor-facing explanation, paper/video outline |
| [Architecture](architecture.md) | Current components and trust boundaries |
| [Reproducibility](reproducibility.md) | Installation, evidence checks, live demos, packaging |
| [Pilot evidence map](evidence-map.md) | Selected pilot artifacts and separate non-AI control |
| [Pilot evaluation report](evaluation-report.md) | Generated four-attempt pilot metrics |
| [Demo guide](demo-guide.md) | Rehearsing the recorded pilot candidates with live runtime checks |
| [Methodology](methodology.md), [threat model](threat-model.md), [artifact schema](artifact-schema.md) | Design background; consult the frozen protocol for primary-v1 conditions |
| [Related work](related-work.md) | Literature/contribution background to personally verify and develop for the final paper |

## Preserve frozen and historical material

- [Study protocol v1](study-protocol-v1.md), `benchmarks/primary/v1/`, the
  primary manifests/trial plan, selected baseline evidence, and
  `data/primary_trials/v1/` define the completed study. Do not change them to
  make later code or results appear part of the original experiment.
- The primary manifest also binds 13 implementation files. The report
  verifier checks those hashes. Supplemental work belongs outside that
  frozen implementation boundary.
- [Initial course alignment review](cs6727-alignment-review.md) records the
  September 4 audit. Its original missing-feature list and work estimate are
  historical; use the current status page for remaining work.
- [Historical implementation notes](../IMPLEMENTATION_GUIDE.md) preserve the
  development sequence. Their old next-step instructions are not the active
  backlog.
- `sample_apps/python-smoke-test/` is an early scanner exercise. It does not
  demonstrate Python remediation support. Keep it as labeled history.
- Older pilot scans, decisions, and adjudications can coexist with selected
  evidence. The pilot manifest determines what counts. Retain these records
  unless a later, separately reviewed cleanup proves that no evidence or
  document links depend on them.

## What to keep or exclude

| Paths | Treatment |
|---|---|
| `src/`, `tests/`, `ui/`, `rules/`, `scripts/`, package manifests and lockfiles | Keep: implementation and reproducibility inputs |
| `benchmarks/`, `data/`, tracked `workspaces/`, `sample_apps/` | Keep: curated experiment inputs and evidence; do not bulk-delete or relocate |
| `docs/`, root README | Keep: active references, frozen protocol, labeled history |
| `.env` | Keep local if needed; never include in submission |
| `.venv/`, `node_modules/`, `__pycache__/`, package build metadata | Rebuildable local dependencies/cache; excluded from submission |
| `dist/` | Generated archives, screenshots, verification copies/logs; retain useful logs locally and exclude from source archive |

No experimental artifacts need removal to complete the prototype. The useful
cleanup is clearer navigation and current terminology. A tracked-file archive
already avoids shipping installed dependencies and local configuration.
Keep the verification copy until its logs and any needed outputs have been
reviewed; deleting it is optional disk-space housekeeping.

## Next work, in order

1. Finalize Progress Report 3: reconcile actual hours, verify citations and the
   AI-use disclosure, inspect the rendered DOCX, submit, and retain the receipt.
2. Explain the refined scope in the next course report: three deliberately
   vulnerable Express fixtures, AI-generated repairs, a controlled 15-attempt
   study, and a separate lifecycle replay. Do not claim a representative
   AI-generated application corpus.
3. Record Video III with the public reference as a short evidence walkthrough,
   then complete the October 11 peer-feedback assignment and preserve receipts.
4. Review and commit the intended snapshot, run the clean-archive checks,
   then build and inspect the final submission archive.
