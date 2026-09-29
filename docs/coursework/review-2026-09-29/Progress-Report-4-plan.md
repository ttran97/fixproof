# FixProof Progress Report 4 plan

Prepared September 29, 2026. The supplied course schedule lists Progress Report
4 as due October 18 at 11:59 p.m.; confirm the live Canvas assignment before
submission.

## Report 4 objective

Report 4 should move from reporting the supplemental matrix to explaining what
the evaluation establishes, how the design compares with alternatives, and how
the package can be reproduced. It should not relabel primary-v1 or
supplemental-v1 outcomes.

The central claim remains bounded: FixProof demonstrates a traceable decision
workflow across three controlled Express fixtures. The observed percentages are
descriptive results, not repair-success estimates for arbitrary repositories.

## Video III feedback question

> Which bounded extension would strengthen confidence more: adding a second
> fixture for one existing CWE, or resolving PATH-S06 in a symlink-capable
> environment?

This replaces the earlier second-reviewer question. It asks peers to compare
benchmark breadth with closure of a known evidence gap and produces an
actionable Report 4 decision.

## Work that belongs in Report 4

1. **Summarize Video III feedback.** Record who raised each substantive point,
   how it affects the project, and whether it changes scope, interpretation, or
   presentation. Do not treat a vote as experimental evidence.
2. **Report the control and failure-handling evidence separately.** Explain the
   deterministic non-AI SAST false-success control, malformed-response policy,
   startup and timeout handling, and why controls are excluded from the 15 AI
   attempts. Re-run repository verification if code changes; do not present a
   software unit test as a new repair experiment.
3. **Strengthen the related-work comparison.** Compare benchmark type and size,
   repair input, validation oracle, retry behavior, success definition, and
   limitations. Separate research papers from OWASP, CWE, and Semgrep technical
   references.
4. **Explain translation beyond the benchmark.** State that the transferable
   contribution is the evidence structure—separate SAST, runtime-security,
   behavioral, policy, and human records—not the measured 5/15 or 15/15 values.
   Identify what would need reconfiguration for another repository.
5. **Exercise reproducibility.** Verify primary evidence, supplemental evidence,
   all human-record bindings, and the public-reference export from a documented
   environment. Record commands, versions, results, and any platform limits.
6. **Choose at most one bounded extension.** If the symlink rerun is selected,
   record it under a new dated supplemental revision and preserve PATH-S06's
   original inconclusive result. If a second fixture is selected, freeze its
   benchmark and oracle before generating or evaluating candidates and keep its
   results outside primary-v1.

## Timeline

| Date | Task | Expected evidence |
| --- | --- | --- |
| September 29–October 5 | Finalize and rehearse Video III; verify the public XSS 04 view and raw backup artifacts. | Reviewed deck, script, rendered slides, site check. |
| October 6 | Post Video III and retain the submission receipt. | Posted-video record. |
| October 7–11 | Complete Peer Feedback Report 3 and summarize responses to the new scope question. | Feedback log and short decision memo. |
| October 8–12 | Audit control/failure-handling artifacts and expand the source-checked related-work comparison. | Control table, failure-handling table, comparison matrix. |
| October 12 | Select the one bounded extension, or document why no new execution is justified before Report 4. | Dated scope decision. |
| October 13–15 | Execute the selected extension only under a frozen, separate protocol; otherwise perform the clean reproducibility rehearsal. | New-version evidence or verification transcript. |
| October 15–17 | Draft Report 4 with actual dates and hours, updated limitations, references, and AI-use disclosure; render and inspect it. | Submission-ready DOCX/PDF. |
| October 18 | Confirm Canvas instructions and submit by 11:59 p.m. | Submission receipt. |
| October 20 / 25 | Post Video IV and complete Peer Feedback Report 4. | Course deliverables. |

## Recommended default if feedback is mixed

Prioritize the symlink-capable PATH-S06 rerun because it closes a specific
inconclusive security observation while preserving the current three-CWE scope.
Treat a second fixture as the next breadth extension only if time remains and a
new frozen protocol can be completed without weakening documentation or
reproducibility.

## Report 4 completion checklist

- Actual dates and personal hours are reconciled through the report cutoff.
- Primary-v1 and supplemental-v1 metrics remain unchanged.
- Control evidence is labeled non-AI and excluded from AI denominators.
- Any new experiment has a new version/date and a frozen pre-execution plan.
- Peer feedback is summarized with dispositions, not copied without analysis.
- Related-work claims have direct, checked sources.
- The generalization boundary directly answers the professor's small-benchmark
  concern.
- Reproduction commands and platform limitations are documented.
- AI assistance and Tony's human-review responsibility are disclosed.
- The rendered submission is checked for page breaks, table wrapping, and stale
  dates.
