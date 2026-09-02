# Progress Report I Alignment Review

Reviewed: September 1, 2026

Source document: `C:\Users\Tony Tran\OneDrive\Progress Report 1 (Tony Tran).docx`

## Overall verdict

The report is technically aligned with the current FixProof implementation and the CS6727 practicum objectives. It defines a cybersecurity problem, describes an implemented technical solution, presents a controlled evaluation method, identifies deliverables, and supplies a semester timeline. The project scope—three controlled JavaScript/Express vulnerability classes—is appropriate for a practicum when the contribution is the depth and auditability of validation rather than the number of vulnerability classes.

The report should receive one editing pass before submission. Its implementation claims are supportable, but the Word document contains visible grammar errors, an unclear section field, and timing language that could make completed and planned work look inconsistent.

## Repository evidence supporting the report

| Report claim | Current implementation evidence | Assessment |
|---|---|---|
| Semgrep scanning, normalization, and correlation | `src/fixproof/scanners/`, `src/fixproof/scan_pipeline.py`, and `src/fixproof/findings/finding_correlator.py` | Aligned |
| Focused context and AI remediation generation | `src/fixproof/agent/context_builder.py`, `prompt_builder.py`, `remediation_agent.py`, and `retry_prompt_builder.py` | Aligned |
| Candidate isolation | `src/fixproof/patches/patch_workspace.py` and per-attempt `workspaces/` artifacts | Aligned |
| Syntax, SAST, security, and functional validation | `src/fixproof/validation/` and benchmark-specific validator tests | Aligned |
| Deterministic policy decisions | `src/fixproof/validation/decision_engine.py` and `data/decisions/` | Aligned |
| Human review without overwriting automated decisions | `src/fixproof/evaluation/adjudication.py` and `data/adjudications/` | Aligned |
| Evaluation report and dashboard | `report_builder.py`, `dashboard.py`, `docs/evaluation-report.md`, and `ui/` | Aligned |
| Three controlled CWE benchmarks | `sample_apps/vulnerable-js-app/`, `vulnerable-sqli-app/`, and `vulnerable-path-traversal-app/` | Aligned |
| Initial Semgrep smoke test found CWE-798 and CWE-78 | `sample_apps/python-smoke-test/app.py`, `data/raw_scans/semgrep-results.json`, and ground truth | Aligned |
| Reproducible readiness gate | `src/fixproof/reproduce.py` and the unit tests | Aligned; 37/37 tests passed on September 1 |

The current authoritative experiment contains three cases, four AI remediation attempts, and one separately labeled non-AI outcome-coverage control. Current pilot metrics are:

- Target SAST resolved: 1/4 (25.0%)
- Targeted security validation passed: 4/4 (100.0%)
- Functionality preserved: 3/4 (75.0%)
- New SAST findings: 0/4 (0.0%)
- Retry improved: 1/1 (100.0%)
- SAST/runtime disagreements: 2
- Required human adjudications completed: 2/2 (100.0%)

These are small controlled-pilot results, not production success rates.

## Required corrections before submission

1. Replace `Section: CS OCY,OC1` with the exact section shown in Canvas. This value currently looks corrupted or ambiguous.
2. Use the canonical title consistently: **FixProof: A Validation-Oriented Agentic Security System for AI-Generated Vulnerability Remediation**.
3. Correct the report’s grammar and typographical errors. Examples include `has been already evaluated`, `purpose ... is to investigates`, `identified and compare`, `an controlled scan`, `to generating`, and `evbaluated`.
4. Clarify the timeline status. On September 1, the W2 range extends through September 4. Use `Completed as of Sept. 1` for tasks already finished, or list their actual completion dates; do not imply that future days have already been worked.
5. Confirm that the 31.5-hour breakdown is your actual work log. The syllabus asks for approximately 30 hours, but the submitted total must reflect your own time.
6. Add the exact pilot metrics above to the completed-work or evaluation section. The current report states the experiment size but omits the most useful measured results.
7. Describe the SQLi Semgrep rule precisely as a clearly labeled, benchmark-focused controlled rule. Do not suggest that default Semgrep CE detected CWE-89; runtime ground truth established the issue and the controlled rule made scanner comparison reproducible.
8. State that the XSS and path-traversal human conclusions are stored separately from automated `NEEDS_HUMAN_ADJUDICATION` decisions. Human acceptance did not rewrite the automated evidence.
9. Keep repeated trials and the SAST-only comparison explicitly labeled as planned work. They are not part of the current four-attempt pilot.
10. Standardize citation formatting. The Pearce, VRpilot, and 1Password claims are supportable, but the references currently mix styles and the Semgrep web citation needs a complete access/publication treatment consistent with the chosen format.
11. Keep the AI disclosure, but use the corrected version below. Never attach `.env`, an API key, raw credentials, or screenshots exposing them.

## Copy-ready revisions

### Related-work positioning

> Prior work has evaluated LLM-generated vulnerability repairs using security and functional tests, and VRpilot has examined validation feedback as a way to improve candidate patches (Pearce et al., 2023; Kulsum et al., 2024). FixProof does not claim to be the first system to validate AI-generated security remediations. Its contribution is a controlled and auditable JavaScript/Express workflow that preserves SAST and rule-provenance evidence, runtime security results, functional results, before-and-after finding comparisons, retry evidence, deterministic dispositions, and human adjudication as separate evidence channels.

### Current pilot results

> As of September 1, 2026, the authoritative pilot includes four AI-generated remediation attempts across three controlled CWE cases and one separately labeled non-AI policy control. The target SAST finding resolved in 1/4 AI attempts, targeted security validation passed in 4/4, functionality was preserved in 3/4, and no attempt introduced a new SAST finding. One measured retry improved functional preservation, two attempts produced SAST/runtime disagreements, and both required adjudications were completed. These descriptive results apply only to the controlled pilot and are not estimates of production performance.

### Generative-AI disclosure

> Generative AI disclosure: I used OpenAI ChatGPT/Codex to support brainstorming, code changes, debugging and test orchestration, documentation editing, and preparation of this progress-report draft. FixProof used the OpenAI API to generate candidate remediation artifacts, which the pipeline then evaluated using independent scanner, runtime-security, functional, deterministic-policy, and human-review evidence. I reviewed the resulting work and remain responsible for its accuracy. I will retain sanitized records of relevant tools, prompts, and outputs for attribution and reproducibility while excluding API keys and other credentials.

## Scope assessment

The scope is currently balanced. Three CWE classes are enough because each is evaluated through multiple independent evidence channels and produces auditable artifacts. Adding more vulnerability classes now would weaken the study if it reduces trial repetition, ground-truth quality, or analysis depth. The next high-value work is clean-environment reproducibility, repeated trials, a clearly defined SAST-only comparison, and careful limitations—not a larger UI or more CWE classes.

## Submission recommendation

Submit after correcting the section field, grammar, timeline status, metrics paragraph, and AI disclosure. Open the final DOCX in Word, inspect page breaks and table layout, run spelling/grammar review, export a PDF if Canvas accepts it, and upload only the sanitized report—not the repository or `.env` file.
