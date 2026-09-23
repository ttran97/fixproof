# Progress Report 3 DOCX verification — September 23, 2026

The latest generated report is `Progress Report 3 (Tony Tran) - Working Draft
September 23 - Professor Feedback Aligned.docx`. The pre-update September 22
report is preserved as `Progress Report 3 (Tony Tran) - Pre-Professor-Feedback-
Update September 23.docx`.

## Content alignment

The latest report now responds directly to the Progress Report 1 feedback:

- It states that the 15 attempts do not estimate a production repair-success
  rate. The benchmark supports a workflow-level conclusion about preserving
  multiple evidence channels and bounded human judgment.
- It connects that conclusion to the recorded primary and supplemental results:
  five parity failures, ten robustness failures, and five inconclusive symlink
  observations after all 15 candidates passed the frozen primary security and
  functional checks.
- It justifies the three minimal fixtures, fixed model and prompt, five calls
  per CWE, Semgrep plus runtime and functional checks, copied workspaces,
  deterministic policy, and the separate human boundary.
- It discloses that the 15 scheduled calls are not 15 unique patches. The five
  SQLi calls produced identical source; XSS and traversal each produced five
  distinct candidate sources.
- It moves the completed 15-candidate appendix out of future work and into the
  completed-task record.
- It preserves the category-specific supplemental denominators, `SQL-R01`
  failures, `PATH-S06` inconclusive outcomes, bounded SQLi acceptances, and
  traversal requests for more testing.
- It uses Tony's planned October 1 submission date while explicitly requiring
  confirmation of the live Canvas deadline instead of asserting the conflicting
  October 4 or October 11 dates.

## Package and layout checks

The Word package opens as a valid ZIP/OOXML document and `word/document.xml`
parses successfully. It contains 68 top-level body paragraphs and three tables.
The timeline has 16 rows; the primary and supplemental evaluation tables each
have five rows.

A read-only Microsoft Word pagination check reported seven pages, 202 Word
paragraph objects, approximately 4,042 words, and three tables. Each table fits
on page 5 without crossing a page boundary. This automated check does not
replace Tony's final visual review at the intended zoom, printer, and submission
settings.

## Evidence verification

The September 23 accuracy review passed 119 automated `unittest` tests. The
reproducibility verifier confirmed 15/15 primary attempts and 10/10 original
conflict reviews. Supplemental verification confirmed three baselines and 15
saved candidates, and all 14 supplemental packet/result bindings remain
verified. These checks reconstruct and validate saved evidence; they do not
make new model calls or rerun every historical scanner, browser, and application
experiment.

## Remaining personal checks

Before submission, Tony still needs to reconcile any September 11–13 effort,
extend the 1.5-hour-per-day estimate through the actual reporting cutoff,
confirm the live Canvas deadline and template, complete Video II peer feedback,
verify the AI-use disclosure and first-person wording, and visually inspect the
final DOCX in Word.
