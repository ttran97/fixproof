# Progress Update Video 1

Due dates supplied in the assignment:

- Upload video by September 8, 2026
- Provide thoughtful feedback on at least four peer projects by September 13, 2026

## Recommended format

Use five simple slides with voice-over. Aim for about four minutes. Show the dashboard for 20–30 seconds if convenient, but a live technical demo is not required for this progress update.

## Slide plan

1. Project and security problem
2. FixProof validation architecture
3. Work completed and pilot evidence
4. Work planned for the next week
5. Areas where feedback would help

## Timed script (approximately four minutes)

### 0:00–0:35 — Project and problem

Hello, my name is Tony Tran, and my capstone project is FixProof: a validation-oriented agentic security system for AI-generated vulnerability remediation.

The problem I am addressing is that an AI-generated patch can look correct without actually being trustworthy. A static-analysis finding might disappear even when the patch breaks intended behavior, and a finding might remain even when targeted runtime evidence indicates that the exploitable behavior has been removed. FixProof therefore treats SAST as one evidence source rather than proof that a remediation is correct.

### 0:35–1:25 — Architecture and activities completed

Over the past reporting period, I narrowed the project to three controlled JavaScript and Express benchmarks: reflected cross-site scripting, SQL injection, and path traversal. I implemented a pipeline that scans the baseline with Semgrep, normalizes and correlates the finding, gives focused source context to an OpenAI remediation model, and saves the model’s candidate without letting the model approve its own output.

The candidate is applied only in an isolated workspace. FixProof then performs syntax checking, a SAST rescan and before-and-after comparison, vulnerability-specific runtime security tests, and separate functional regression tests. A deterministic decision engine produces reject, ready for human review, or needs human adjudication. Human conclusions are recorded as separate evidence rather than overwriting the automated result.

### 1:25–2:25 — Pilot results and lesson learned

The current pilot contains three cases, four AI remediation attempts, and one separately labeled non-AI control used only to test a policy branch. Across the four AI attempts, the target SAST finding resolved in one attempt, or 25 percent. Targeted security validation passed in all four attempts, functionality was preserved in three of four, and no attempt introduced a new SAST finding.

The most useful case was reflected XSS. The first candidate passed the targeted security tests but failed functional tests, so FixProof rejected it. A retry built from measured validation feedback preserved both security and functionality. However, its SAST finding remained, so the system escalated the evidence disagreement to a human instead of automatically approving it or repeatedly rewriting the code to satisfy the scanner.

The authoritative artifacts now pass all 37 automated tests, and both required human adjudications are complete. These results describe only a small controlled pilot; they are not a claim about production success rates.

### 2:25–3:15 — Week ahead

During the next week, I plan to strengthen the research design rather than add more vulnerability classes. I will refine the threat model and ground-truth procedure, make the experiment record and artifact schema more explicit, and improve clean-environment reproducibility by removing hard-coded local assumptions and documenting pinned dependencies.

I also plan to define the repeated-trial protocol and the SAST-only comparison baseline. That will let the final evaluation compare a scanner-only interpretation with the complete FixProof decision process across the same controlled cases.

### 3:15–4:00 — Feedback requested

I would appreciate feedback in three areas. First, is three deeply evaluated CWE classes an appropriate scope, or would a fourth class add enough value to justify the reduced depth? Second, is a clearly labeled benchmark-specific Semgrep rule methodologically acceptable when ground truth is established independently and rule provenance is preserved? Third, for SAST and runtime disagreements, is human adjudication the right boundary, and what evidence would make that reviewer packet more persuasive?

Thank you. I am especially interested in feedback on the experimental scope and on how clearly I distinguish scanner evidence from security ground truth.

## Optional dashboard recording

Run this from PowerShell and leave the terminal open:

```powershell
cd "C:\Users\Tony Tran\Documents\fixproof"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m fixproof.reproduce --serve
```

Then open:

```text
http://127.0.0.1:8080/ui/
```

Show the summary metrics, the experiment matrix, and one XSS attempt. Do not show `.env`, the API key, raw prompt secrets, or browser/terminal history containing credentials.

## Recording checklist

- Update “week ahead” if additional work is completed before September 8.
- Keep the recording between three and five minutes.
- Define SAST the first time it appears if the audience may not know the term.
- Say that results are a controlled pilot, not production performance.
- Check that no credentials or private notifications are visible.
- Post by September 8 and schedule time to watch every group video.
- Submit brief but substantive feedback on at least four projects by September 13.
