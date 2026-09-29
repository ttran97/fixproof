# FixProof Post Video III: outline and narration script

Updated September 29, 2026. Target length: about five minutes. This script is
aligned with the corrected Progress Report 3, the frozen primary-v1 report,
the supplemental-v1 report, and the 14 verified later human records.

## Recording outline

| Time | View | Purpose |
| --- | --- | --- |
| 0:00-0:20 | Slide 1 | Introduce FixProof and state what changed since Video II. |
| 0:20-0:50 | Slide 2 | State the research question and bounded three-fixture scope. |
| 0:50-1:25 | Slide 3 | Explain primary-v1 chronologically, then the separate supplemental-v1 layer. |
| 1:25-2:00 | Slide 4 | Explain the 15-attempt primary results and SAST/runtime disagreement. |
| 2:00-2:35 | Slide 5 | Explain the 140 supplemental observations with separate category denominators. |
| 2:35-3:45 | Slide 6 and public site | Filter to Reflected XSS and inspect XSS 04. |
| 3:45-4:25 | Slide 7 | Compare XSS 03 and XSS 04 and explain the parity decision. |
| 4:25-5:00 | Slide 8 | Summarize human records, limits, next steps, feedback request, and AI disclosure. |

Slide 9 is backup only. Use it if someone asks about the bounded SQLi
acceptances or the traversal requests for more testing.

## Full narration script

### Slide 1 - introduction

Hello everyone. This is my third FixProof update. Since Video II, I completed
the supplemental evaluation, recorded the remaining follow-up decisions,
submitted Progress Report 3, and published a sanitized reference for all 15
candidates. I will show why later evidence qualified some earlier decisions.

### Slide 2 - research question and scope

The question is whether FixProof can identify failed or behavior-changing
patches that SAST alone could classify as successful. The benchmark uses one
controlled Express application per vulnerability: XSS, SQL injection, and path
traversal. I held
the model, prompt template, tool setting, and five-call schedule constant. The
model could not run tools or tests; FixProof performed validation separately.
The 15 calls are repeated repairs of three applications, not a production
success-rate estimate.

### Slide 3 - workflow

The primary workflow moves left to right. A frozen fixture and Semgrep finding
provide focused context to the model. The model proposes code but cannot approve
or deploy it. FixProof applies the candidate in a copied workspace, runs syntax,
SAST, security, and functional checks separately, and uses deterministic policy
to route the result. Every automated outcome goes into the primary record.
Selected cases branch to human review, and the verdict and rationale return to
that record.

Supplemental-v1 later reused the saved baseline and 15 candidates, made no new
model calls, and ran cases frozen in the project's internal registry. Its
separate outcomes and the original primary evidence inform human follow-up.
Those later records qualify the result without rewriting primary-v1.

### Slide 4 - frozen primary results

The primary protocol completed 15 calls, five per CWE. Five target SAST findings
resolved, all in SQL injection. All 15 candidates passed their complete primary
security and functional suites. XSS and traversal therefore produced 10
SAST/runtime disagreements: their scanner findings remained while registered
runtime tests passed. For XSS and traversal, 0/5 target-SAST resolution does not
mean 0/5 runtime security; it means the evidence channels disagreed and human
adjudication was required.

### Slide 5 - supplemental results

The supplement produced 140 candidate-case observations, not 140 patches.
Security had 60 observations: 55 passed and five symlink cases were inconclusive.
Parity had 45: 40 passed and five failed. Robustness had 35: 25 passed and 10
failed. These categories answer different questions, so they are not one
security success rate. Inconclusive is not a pass.

### Slide 6 - public evidence demonstration

[Switch to `https://fixproof.netlify.app/`. Select **Reflected XSS** and open
**XSS 04**.]

This read-only reference presents the complete saved evidence. XSS 04 passed its
primary suites while the target SAST finding persisted. It also passed all three
supplemental XSS security cases. However, XSS-P01 omitted `name` and observed a
blank after `Hello` instead of the frozen baseline `Hello undefined`.

The original review requested more testing. The later record rejects XSS 04
under exact parity. This does not mean the registered attacks still worked. The
site displays sanitized evidence only; it runs no applications, tests, model
calls, approvals, or deployments.

If I need to show the backend, the validators launched the saved candidate
`app/app.js` on `127.0.0.1` inside a disposable workspace copy. The raw patch
and JSON results are technical backups; the public site is only a viewer.

[Return to Slide 7.]

### Slide 7 - XSS 03 versus XSS 04

The code difference explains the result. XSS 03 uses `String(value)`, so a
missing value remains `undefined` and all five parity cases pass. XSS 04 uses
`String(value ?? "")`, so the value becomes blank and XSS-P01 fails. Both
blocked all three registered supplemental XSS attacks. FixProof therefore keeps
exploit behavior and behavioral preservation separate.

### Slide 8 - human judgment, limits, and next steps

There are 10 original reviews: seven acceptances and three requests for more
testing. Fourteen later records add five rejections, five bounded SQLi
acceptances, and four traversal requests. No primary record was overwritten.

The main limits are one application per CWE, repeated calls rather than 15
independent applications, one distinct SQLi source, and an inconclusive symlink
case. For Report 4, I will summarize this feedback, freeze any new test plan,
attempt PATH-S06 in a symlink-capable environment, and verify the controls,
failure handling, and reproduction steps.

My feedback question is: which next step would increase your confidence more—
testing FixProof on another vulnerable application or completing the
path-traversal test that Windows could not run?

Codex and ChatGPT assisted implementation, analysis, documentation, and slides.
Separate saved API calls proposed repairs. I made the human decisions and remain
responsible for the claims. Thank you.

## If asked where `app.js` is tested

> The frozen vulnerable source is under `benchmarks/primary/v1`. Each repair is
> applied to its own copied workspace under `data/primary_trials/v1`, and the
> validators launch that candidate `app.js` locally on `127.0.0.1`. Supplemental
> validation creates another disposable copy before running its registered
> cases. The Netlify site displays the saved results; it does not run the app.

For XSS 04, keep these repository-relative locations available as backup:

- `benchmarks/primary/v1/xss/app.js`
- `data/primary_trials/v1/cases/xss/attempt-04/.../app/app.js`
- `tests/supplemental/v1/cases.json`
- the saved XSS 04 supplemental `result.json`

## Short answers for likely questions

**Why accept SQLi when SQL-R01 failed?**  The five candidates passed all
registered supplemental injection-security and parity cases and returned no
unauthorized rows. SQL-R01 remains a disclosed low-impact repeated-input
robustness failure, so the acceptance is bounded rather than full conformance.

**Why request more traversal testing?**  PATH-S06 could not verify symlink-target
containment on the Windows environment. Traversal 03 and 05 also retain recorded
robustness failures. An inconclusive security case cannot support a symlink-safe
claim.

**Why is 0/5 XSS target-SAST resolution not 0/5 security?**  The SAST column
records whether the target scanner finding disappeared. The security column
records whether the candidate passed the registered runtime attacks. They are
different evidence channels.

**What does “the model could not run tools or tests” mean?**  The model received
the frozen finding and code context and returned a proposed patch. It could not
use a terminal, browser, scanner, repository search, application, or test
runner. FixProof performed those checks afterward.

**Why five calls per fixture?**  The frozen schedule required five initial calls
for each of the three applications, or 15 total, without stopping early after a
favorable result. These are calls, not necessarily unique patches, and retries
are excluded from the primary denominator.

## Pre-recording checklist

- Open `FixProof - Video III - Final Validated Recording Deck.pptx`, not an
  earlier recording deck.
- Open `https://fixproof.netlify.app/`, filter to Reflected XSS, and test the XSS
  04 dialog before recording.
- Keep Slide 9, the evidence appendix, and the raw `app.js` files as backups;
  skip them during the main recording unless asked.
- Present slides full-screen and increase browser zoom if evidence text is small.
- Disable notifications and keep `.env`, absolute machine paths, response IDs,
  credentials, and raw logs off screen.
- Do not describe the dashboard as a live test runner or the supplemental study
  as part of the frozen primary metrics.
- Aim for five minutes unless Canvas specifies another limit.

