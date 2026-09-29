# FixProof Post Video III - final recording outline

Updated September 28, 2026. Target length: approximately five minutes unless the live Canvas instructions specify a different limit. Progress Report 3 was submitted September 28, ahead of the October 4 deadline.

## One-sentence purpose

FixProof preserves separate static, runtime-security, behavioral, policy, and human evidence so that later testing can qualify an earlier patch decision without rewriting the frozen primary study.

## Recording sequence

| Time | View | Main points |
| --- | --- | --- |
| 0:00-0:20 | Slide 1 | Introduce FixProof as an evidence-first workflow for reviewing AI-generated vulnerability repairs. State that Report 3 is submitted and this video focuses on evidence that changed later human review. |
| 0:20-0:50 | Slide 2 | State the research question and scope. The benchmark has one controlled Express fixture for each of three CWEs and five initial calls per fixture. It supports a workflow demonstration, not a production repair-success estimate. |
| 0:50-1:25 | Slide 3 | Walk through primary-v1: controlled fixture, model-proposed patch, copied workspace, separate validators, deterministic policy, and selected human review. Then explain supplemental-v1: predefined and frozen cases reused the same saved candidates without new model calls or changes to primary metrics. |
| 1:25-2:00 | Slide 4 | Explain the frozen primary results: 15 calls, 5/15 target SAST findings resolved, 15/15 candidates passed their complete registered primary security and functional suites, and 10/15 produced SAST/runtime disagreement. Clarify that 0/5 SAST resolution does not mean the tested attacks succeeded. |
| 2:00-2:30 | Slide 5 | Explain the 140 supplemental candidate-case observations using separate denominators: security 60, behavioral parity 45, and robustness 35. Five symlink cases remain inconclusive. Do not describe 140 as one security success rate. |
| 2:30-3:45 | Slide 6, then [public evidence site](https://fixproof.netlify.app/) | Tell students that the site is a sanitized, read-only reference. Filter to **Reflected XSS**, open **XSS 04**, and show its primary evidence, `XSS-P01` failure, original review, later rationale, and patch excerpt. Compare XSS 03 verbally or open it if time permits. State that the site presents saved evidence; it does not execute tests or call the model. |
| 3:45-4:25 | Slide 7 | Compare `String(value)` in XSS 03 with `String(value ?? "")` in XSS 04. Both passed 3/3 supplemental security cases. XSS 03 preserved all five parity cases; XSS 04 changed `Hello undefined` to `Hello ` and failed the frozen missing-input parity case. The later rejection concerns parity, not continued XSS exploitability. |
| 4:25-5:00 | Slide 8 | State the review totals: 10 original reviews, 14 later records, and zero overwritten primary records. State the key limits and that Report 3 was submitted September 28. Give students `fixproof.netlify.app` for the complete evidence and ask the focused feedback question. Close with the AI-use disclosure. |

Slide 9 is backup only. Use it if someone asks why the SQLi candidates received bounded acceptances despite `SQL-R01`, or why traversal candidates require more testing.

## Suggested website narration

> I created this read-only reference so you can inspect all 15 candidates without watching me read every table row. It shows the frozen primary result, the later supplemental categories, the original human review when one existed, and the later qualification. It contains sanitized saved evidence only; it does not run attacks, call the repair model, or approve a patch.

For XSS 04:

> XSS 04 passed all three registered supplemental security cases, so this is not evidence that the registered XSS attacks still worked. The missing-name parity case failed because the patch converted an absent value to an empty string. Under the frozen exact-parity criterion, the later human record rejects this candidate for the bounded benchmark while preserving the original review.

## If asked where `app.js` is tested

> The vulnerable baseline is preserved under `benchmarks/primary/v1`. FixProof never patches that file directly. Each generated repair is applied to its own copied workspace under `data/primary_trials/v1`, and the validators launch that candidate `app.js` locally on `127.0.0.1`. Supplemental validation makes another disposable copy of the saved candidate before running the registered cases. The Netlify site only displays the resulting saved evidence; it does not execute the application.

For XSS 04, the repository-relative evidence chain is:

1. `benchmarks/primary/v1/xss/app.js` - frozen vulnerable baseline.
2. `data/primary_trials/v1/cases/xss/attempt-04/.../app/app.js` - saved candidate.
3. `tests/supplemental/v1/cases.json` - registered supplemental case definitions.
4. `data/supplemental/v1/runs/.../attempt-04/result.json` - recorded outcomes.

Keep these files pre-opened only as backup. Do not navigate the long workspace path during the main five-minute recording.

## Focused feedback question

> For the next phase, would a second reviewer of selected disagreement cases improve confidence more than another CWE, or should I prioritize rerunning the symlink case in a capable environment?

## Closing AI-use disclosure

> Codex and ChatGPT assisted implementation, analysis, documentation, and presentation preparation. Separate saved OpenAI API calls proposed the experimental repair candidates. I made the recorded human decisions and remain responsible for the claims.

## Evidence and claim checks

- The 15 attempts are repeated repairs of three fixtures, not 15 independent applications.
- The five SQLi responses contain one distinct candidate source; XSS and traversal each contain five.
- Primary `15/15` values count candidates whose complete registered suite passed, not individual test cases.
- Supplemental security, parity, and robustness are not interchangeable.
- `PATH-S06` is inconclusive, never passed.
- XSS 04's follow-up rejection is a behavioral-parity judgment, not evidence of a surviving registered exploit.
- The public site is a presentation layer over saved evidence. It performs no model, scanner, application, or approval action.
- Keep raw files, `.env`, model response identifiers, local paths, and credentials off screen.

## Deadlines to state consistently

- Progress Report 3 submitted: September 28, 2026.
- Official Progress Report 3 deadline: October 4, 2026 at 11:59 p.m.
- Post Video III: October 6, 2026.
- Peer Feedback Report III: October 11, 2026 at 11:59 p.m.

## Pre-recording checklist

- Update Slide 8 from “planned early Report 3 submission: October 1” to “Report 3 submitted: September 28.”
- Open `https://fixproof.netlify.app/`, select **Reflected XSS**, and confirm XSS 04 opens before recording.
- Keep the deck full-screen; increase browser zoom if the evidence text is small.
- Keep XSS 03 and XSS 04 `app.js` files and the evidence appendix open only as Q&A backups.
- Turn off notifications and keep `.env`, absolute machine paths, model-response identifiers, and raw logs off screen.
- State that saved evidence is being demonstrated; do not call the website a live test run.
- End near five minutes unless Canvas gives a different limit.

