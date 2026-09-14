# Video II: presentation and evidence walkthrough

Use the **seven-slide reviewed PowerPoint**, not the earlier five-slide outline. This outline is synchronized with that deck. Evidence checkpoint: September 13, 2026. Posting target supplied by Tony: September 22.

Recommended format: slides plus a **60–90-second walkthrough of saved results**. Show what the prototype produces and why the evidence matters. A fresh model call, full test-suite run, or live attack is not needed for this progress narrative. The exact Video II rubric/time limit was not supplied, so this is a presentation recommendation, not a statement that every course requirement is satisfied.

Aim for about five minutes. The walkthrough replaces most of slide 6's narration; do not deliver both as duplicate explanations. If the assignment imposes a shorter limit, use slide 6's comparison and omit the browser switch.

## Slide order and timing

| Time | Slide / view | What to explain | What the viewer should see |
|---|---|---|---|
| 0:00–0:15 | 1. FixProof — Video II | Name, project, Report 2 submitted, purpose of this update. | Title slide. |
| 0:15–0:55 | 2. What FixProof is | Python prototype; three Express fixtures; Codex development assistance versus runtime repair generation. | Scope and research question. Give the short example prompt verbally. |
| 0:55–1:25 | 3. Research-informed design | Security scenarios motivate controlled fixtures; repair correctness motivates functional checks; external feedback motivates bounded retry. | Three research-to-design connections. Do not read full references aloud. |
| 1:25–2:00 | 4. Workflow | Establish baseline behavior, generate candidate, repeat security/functional checks, compare findings and route to human review. | Four workflow steps. Explicitly state that the model does not approve its repair. |
| 2:00–2:45 | 5. Verified progress | 15 attempts; five target resolutions; ten reviews; seven acceptances and three testing requests. Explain what passing means. | Summary metrics. Mention 89 repository tests passed on September 13, not a fresh run of all historical attacks. |
| 2:45–4:00 | 6, then dashboard | Contrast a SQLi readiness result with XSS 04's unresolved coverage gap. | Two-column comparison or the saved evidence views described below. |
| 4:00–4:50 | 7. Next phase and feedback | Supplemental tests for XSS 04–05/traversal 01, same criteria for related accepted candidates, scope limits, two questions, AI disclosure. | Concrete next steps and feedback questions. |

Timings are rehearsal allocations. Speak naturally and shorten background before rushing the evidence explanation. The full speaker-note script is available separately; it is a reference, not text that must be read verbatim.

## Exactly what to demonstrate

Before switching to the browser, say:

> “I’ll show saved primary-study results that were verified on September 13. This is a walkthrough of the evidence, not a new scan, AI call, or attack execution.”

**1. Summary — about 10 seconds.** Open `/ui/primary.html`, not the pilot homepage. Point to 15 initial attempts, five ready for review, ten SAST/runtime disagreements, and ten completed conflict reviews. Mention that three reviews request additional testing. Do not read every table row.

**2. SQLi attempt 01 — about 25 seconds.** Select **SQL injection 1**. The detail heading should be `primary-v1-sqli-initial-01`.

- Show **Candidate patch**: point to the parameterized query replacing SQL string construction. Explain it in one sentence.
- Show **Decision evidence** or the summary row: target resolved, security 2/2, functional 3/3, READY_FOR_HUMAN_REVIEW.
- Say: “The security total includes one attack and one benign control. These checks support review readiness; no primary SQLi human approval is recorded.”

**3. XSS attempt 04 — about 35–45 seconds.** Return to the table and select **Reflected XSS 4**. Confirm `primary-v1-xss-initial-04`.

- Show the summary/decision evidence: persistent SAST target, security 4/4, functional 6/6.
- Show **Human review record**: point to REQUEST_ADDITIONAL_TESTING and the missing-name rationale. The table's `completed` label describes review completion, not acceptance.
- Briefly show **Candidate patch** and `String(value ?? "")` if readable.
- Say: “Code review found that an omitted name changes from the original ‘undefined’ text to an empty value. The frozen tests do not cover that input. This is a review finding awaiting supplemental runtime testing. The point is that a passing counter is only as good as its tests.”

Return to slide 7. Similar omitted-name behavior in accepted XSS 01–02 is acknowledged in the supplement; the next tests should use the same criteria across those candidates. Do not imply that XSS 04 is the only affected patch.

Keep each detail panel focused. The dashboard's actual sections include **Candidate patch**, **Security observations**, **Functional observations**, **Decision evidence**, and **Human review record**. If you want to show a specific HTTP response, choose it during rehearsal; do not search through JSON during the recording.

## Should you show tests running?

**Show the results and one example of how you interpret them.** That is the recommended Video II demonstration. Do not spend the short video waiting for 89 tests, generating another candidate, installing dependencies, or troubleshooting Node.

The 89 repository checks test FixProof's machinery and saved-evidence consistency. They are different from the per-candidate HTTP/browser checks. State this distinction verbally rather than calling all of them security tests.

If you already have a working, rehearsed live runtime demo and the rubric asks for it, substitute one brief baseline/candidate comparison and explicitly identify what was rerun. Do not describe a dashboard click as a live security test. Otherwise, the saved-results walkthrough is sufficient to communicate the current progress and evaluation approach.

If browser switching is distracting, keep slide 6 visible and explain its two columns. A screenshot captured from the current dashboard is another option; label it “Recorded primary-v1 evidence; verified September 13.” Do not invent a screenshot or display an example outcome as an observed run.

## Local preparation

Run from the inner Git root, `C:\Users\tonyt\Documents\fixproof-main\fixproof`:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
& .\.venv\Scripts\python.exe -m fixproof.evaluation.primary_report --check
```

If verification succeeds, start the evidence dashboard in the same terminal:

```powershell
& .\.venv\Scripts\python.exe -m fixproof.evaluation.dashboard
```

Open `http://127.0.0.1:8080/ui/primary.html`. This dashboard command serves existing evidence; it does not itself regenerate or verify it. Node is not required merely to serve the evidence dashboard. Leave the terminal running during recording and stop it with Ctrl+C afterwards. If port 8080 is occupied, use `--port 8081` and the corresponding URL.

Prepare the browser before recording, rehearse the two trial selections, and adjust zoom until code and results are readable. Keep unrelated windows and credentials out of the captured area. Presenter notes should remain on your private display or separate script, not cover the slides.

## Accurate claims to retain

| Say | Avoid |
|---|---|
| Fifteen initial attempts on three fixtures; eleven distinct sources. | Fifteen independent applications or fifteen distinct repairs. |
| Ten reviews recorded: seven bounded acceptances and three testing requests. | Ten approved fixes or all review issues resolved. |
| Fixed security/functional suites passed for all primary attempts. | Every input is secure and functional. |
| Five target findings resolved; SQLi candidates ready for review. | All scanner warnings disappeared or all SQLi candidates are approved. |
| Zero primary SAST false successes observed. | The primary trials proved detection of AI patches that clear SAST and remain exploitable. |
| The constructed control clears SAST but fails functionality; security evidence is inconclusive. | An AI candidate failed all security and functional tests after clearing SAST. |
| September 13 verification passed 89 repository tests. | “Today's tests passed” in a September 22 recording without a new dated check. |

One relevant failed check can be enough to reject a repair; it does not need to fail every security and functional test.

## Closing and feedback

Use two focused questions:

1. “Which additional tests would best address the missing-input and path-boundary gaps identified in review?”
2. “Would a second reviewer provide more useful evidence than adding another vulnerability class?”

Replace “Should I run another test that AI candidate remediated SAST findings but failed all functional and security tests?” with:

> “Would separately labeled bad-patch controls strengthen evaluation of cases where SAST clears but a security or functional check fails?”

Keep this as an optional alternative to one of the two questions, not a third long discussion topic. Testing should evaluate predefined expectations, not search until an AI produces a preferred failure.

Closing line:

> “The initial trials and conflict reviews are complete. My next step is supplemental testing of the identified gaps, with all new results kept separate from the frozen study. ChatGPT and Codex assisted implementation, analysis, and presentation preparation; I remain responsible for the claims and review decisions.”

## Final PowerPoint check

The content covers project identity, motivation, research-informed approach, implementation, measured progress, an evidence example, limitations, next work, peer questions, and AI-use disclosure. That is a coherent progress presentation. Assignment-specific timing or required sections still take precedence if Canvas specifies them.

The reviewed deck uses seven slides with speaker notes and a two-column slide 6. Technical package checks do not confirm visual layout: open Slide Show mode and check line wrapping, contrast, code readability, and speaker notes before recording. Keep research references in notes or accompanying materials; the script includes their full URLs. The submitted report and original OneDrive PowerPoint remain unchanged.
