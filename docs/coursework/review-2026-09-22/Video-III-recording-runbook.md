# FixProof Post Video III recording runbook

Prepared September 23, 2026. The deck is designed for an approximately five-minute update. Check the live Canvas instructions before recording because this timing is a recommendation, not a claimed course requirement.

## Main message

FixProof does not treat a scanner result or a passing attack test as sufficient by itself. It preserves separate static, runtime-security, behavioral, policy, and human evidence so that a later finding can qualify an earlier decision without rewriting the frozen primary study.

## Recording sequence

| Time | View | What to explain |
| --- | --- | --- |
| 0:00-0:20 | Slide 1 | Introduce FixProof as an evidence-first workflow for three controlled Express fixtures. State that this update focuses on evidence that changed later human review. |
| 0:20-0:55 | Slide 2 | State the research question and scope boundary. The model proposes code; validators measure it; a human makes bounded decisions. The benchmark supports a workflow demonstration, not a production repair-success rate. |
| 0:55-1:30 | Slide 3 | Walk left to right through primary-v1, then through supplemental-v1. Explain that supplemental cases were defined and frozen in the internal registry before candidate execution. Do not imply an external public preregistration. |
| 1:30-2:05 | Slide 4 | Explain 15 scheduled calls, 5/15 target SAST findings resolved, 15/15 candidates passing their complete frozen primary security and functional suites, and 10/15 SAST/runtime disagreements. Explain that 0/5 resolved means the target finding persisted, not that the tested attacks succeeded. |
| 2:05-2:35 | Slide 5 | Explain the separate supplemental denominators: security 60, parity 45, and robustness 35. The 140 total is a count of mixed candidate-case observations, not patches and not one security success rate. |
| 2:35-3:45 | Slide 6, then [public evidence site](https://fixproof.netlify.app/) | Explain that the site is a sanitized, read-only presentation layer. Filter to Reflected XSS, open XSS 04, and follow its primary result, XSS-P01 failure, human records, and patch excerpt. State clearly that no model call or test execution is occurring. |
| 3:45-4:30 | Slide 7 | Compare `String(value)` with `String(value ?? "")`. Both passed 3/3 supplemental XSS security cases. XSS 03 preserved all five parity cases; XSS 04 changed the missing-name output and failed XSS-P01. The rejection is about the frozen parity rule, not continued XSS exploitability. |
| 4:30-5:00 | Slide 8 | State the separate human-record counts and limits. Ask the focused feedback question. Mention the October 4 Report 3 deadline, October 6 video date, and October 11 feedback deadline. Close with the AI-use disclosure below. |

Slide 9 is backup only. Use it if someone asks about the bounded SQLi acceptances or why traversal needs more testing.

Recommended closing disclosure:

> Codex and ChatGPT assisted implementation, analysis, and presentation preparation. Separate saved OpenAI API calls proposed the experimental repairs. I made the recorded human decisions and remain responsible for the claims.

## Evidence demo: public site first, raw files as backup

Open [https://fixproof.netlify.app/](https://fixproof.netlify.app/) before recording. Use the vulnerability-family filter, select **Reflected XSS**, and choose **View evidence** for **XSS 04**. Point to the frozen primary result, the supplemental P/F/I counts, `XSS-P01`, the original and later human records, and the patch excerpt. Open XSS 03 only if time permits.

The public site contains sanitized saved evidence. It does not call a model, run a scanner, start an application, replay an attack, or approve a candidate.

For a technical question, use the raw evidence chain below as backup.

Open these tabs before recording and zoom the editor so only the relevant lines are visible:

1. [Frozen trial plan](../../../data/evaluation/trial-plan.json): show `plan_status` near line 5, `planned_attempts_per_case` near line 82, and the complete-all-15 stopping rule near line 84.
2. [Primary dashboard](../../../ui/primary.html): serve it locally and show the XSS rows or the primary totals. Say that the page displays saved evidence.
3. [XSS 03 patch](../../../data/primary_trials/v1/cases/xss/attempt-03/workspace/CF-209ae17232b1/attempt-03/candidate.patch): show `String(value)` near line 9.
4. [XSS 04 patch](../../../data/primary_trials/v1/cases/xss/attempt-04/workspace/CF-209ae17232b1/attempt-04/candidate.patch): show `String(value ?? "")` near line 9.
5. [XSS 03 supplemental result](../../../data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-03/result.json): show `XSS-P01` near line 55, `<h1>Hello undefined</h1>` near line 66, and `status: pass` near line 93.
6. [XSS 04 supplemental result](../../../data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-04/result.json): show `XSS-P01` near line 55, `<h1>Hello </h1>` near line 66, and `status: fail` near line 93.
7. [XSS 04 follow-up decision](../../../data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-04/result.json): show `FOLLOW_UP_REJECT_CANDIDATE` near line 10 and briefly identify the rationale as a later parity qualification.

Recommended transition sentence:

> I am following one saved evidence chain through the public reference, not rerunning the model. The frozen plan fixes the denominator; the two patches show the code difference; the same registered parity case records different outputs; and the later human record preserves that qualification separately.

## Dashboard preparation

From the repository root, start the read-only evidence server before recording:

```powershell
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

Open `http://127.0.0.1:8080/ui/primary.html`. Stop the server with `Ctrl+C` after recording. Serving the dashboard does not rerun the historical model calls.

## Claims to avoid

- Do not call the 15 attempts 15 independent applications; they are repeated repairs of three fixtures, with one distinct SQLi source across five responses.
- Do not say 15/15 primary suite passes establish production safety.
- Do not describe all 140 supplemental observations as security tests.
- Do not call the five traversal symlink observations passes; they are inconclusive.
- Do not say XSS 04 remained exploitable. Its registered supplemental security cases passed; its later rejection is a behavioral-parity decision.
- Do not display credentials, `.env`, API keys, or personal terminal history.

## Backup references

- [Full 15-candidate evidence appendix](Video-III-15-candidate-evidence-appendix.pdf)
- [Supplemental results summary](../../supplemental-results-v1.md)
- [Primary results summary](../../primary-results.md)
- [Workflow figure](fixproof-workflow-slide.png)
