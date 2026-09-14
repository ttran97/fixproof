# Video II recording script — September 13, 2026

Use with the reviewed copy of your seven-slide deck. Target approximately five minutes, depending on speaking pace; this is a rehearsal target, not a verified course time limit. The supplied 15-minute limit applies to the final presentation. Narration is also embedded in PowerPoint speaker notes.

## Slide 1: FixProof — Video II

Hi everyone. This is my second FixProof progress update. Progress Report 2 has been submitted. I’ll clarify what the prototype does, show the completed trial and review results, and explain what the next evaluation phase needs to test.

Evidence / references: Student-reported submission status; data/evaluation/primary-report.json.

## Slide 2: What FixProof is

Raymond asked what FixProof is and what I asked Codex to build. FixProof is the prototype I’m developing with AI assistance. To clarify my earlier reply, its orchestration is Python; the controlled applications are JavaScript and Express. My example request was to create a simple, deterministic Express app with controlled XSS, expected-behavior tests, and a security test demonstrating the vulnerability. Codex assists development. Separately, the runtime remediation model receives one finding and focused code and proposes a repair. The question is whether disappearance of the original SAST finding agrees with security and functional evidence. This covers small web routes, including browser execution for XSS.

Evidence / references: User-supplied example prompt; pyproject.toml; src/fixproof/agent/; docs/study-protocol-v1.md.

## Slide 3: Research-informed design

The design connects to prior research. Pearce and colleagues studied insecure generated code under defined security scenarios, which motivates controlled fixtures. Their vulnerability-repair work also identifies functional-correctness challenges, supporting separate benign-behavior tests. Kulsum and colleagues investigate external validation feedback in vulnerability repair, providing precedent for a bounded retry. FixProof does not claim that these ideas are new or that it outperforms those systems. My project evaluates an auditable evidence workflow in three controlled cases.

Evidence / references: https://arxiv.org/abs/2108.09293 ; https://arxiv.org/abs/2112.02125 ; https://arxiv.org/abs/2405.15690 . Preprint-year citations match submitted Report 2.

## Slide 4: From vulnerable baseline to review

Aluor asked whether the attack is run before and after repair. Yes: the baseline and candidate use the same route-specific attack and control suites. The candidate also receives syntax and SAST checks and functional tests. Cheick asked about new weaknesses and behavior changes. New scanner findings or failed checks trigger rejection. If the target warning persists while the other checks pass, the policy requests adjudication. The model does not grade its own patch. These copied workspaces separate files; they are not a security sandbox for arbitrary hostile code.

Evidence / references: src/fixproof/evaluation/benchmark_verifier.py; src/fixproof/validation/; docs/threat-model.md.

## Slide 5: Verified progress — September 13

Kiang asked about repetitions and measurement. The frozen plan used five initial calls per CWE, fifteen total, with the same baseline and prompt conditions within each case. All fifteen pass the fixed security and functional suites; five resolve the target SAST warning. All ten conflicts now have reviews: seven bounded acceptances and three requests for additional testing. The September thirteenth recorded-evidence verification and all eighty-nine repository tests passed. That was not a fresh run of the historical applications. There are eleven distinct candidate sources because all five SQLi calls produced identical source. No primary SAST false success was observed, so these results cannot estimate a detection rate for that failure mode.

Evidence / references: data/evaluation/primary-report.json; docs/primary-results.md; September 13 primary_report --check and unittest run (89 tests, OK).

## Slide 6: Passing fixed tests can leave an evidence gap

Compare SQLi attempt one with XSS attempt four. SQLi uses a parameterized query and passes the recorded attack/control and functional checks. It is ready for human review, not already approved. XSS passes four security and six functional checks, yet code review found that an omitted name changes from the original undefined text to an empty value. That input was absent from the frozen suite. This is a code-review observation awaiting supplemental runtime testing, not a newly measured exploit. Similar missing-input concerns also affect accepted XSS attempts one and two, as the supplement acknowledges. Raymond’s point is central: validation quality depends on test coverage, not simply a passing counter.

Evidence / references: data/primary_trials/v1/cases/sqli/attempt-01/; data/primary_trials/v1/cases/xss/attempt-04/; data/primary_reviews/v1/primary-v1-xss-initial-04/result.json; docs/coursework/review-2026-09-12/xss-review-supplement.md.

## Slide 7: Next phase and feedback

My next milestone is a predefined supplemental matrix, beginning with XSS four and five and traversal one. I’ll include the related accepted XSS candidates when testing missing inputs, preserve every outcome separately from the primary study, and document follow-up conclusions. Controlled bad patches can exercise failures without assuming AI will generate a desired result. Failure-handling tests will cover malformed output, scanner timeout, and startup problems. I’ll keep three CWEs rather than expand to the OWASP Top Ten at this stage. The remaining deliverables include supplemental results, the final paper and reproducible package, and the final video due November fifteenth. I’d welcome feedback on the best additional tests and the value of a second reviewer. ChatGPT and Codex assisted implementation, analysis, and presentation preparation; I remain responsible for the claims and review decisions.

Evidence / references: Human REQUEST_ADDITIONAL_TESTING records; supplied course dates; prototype limitations and user-provided AI-use disclosure.
