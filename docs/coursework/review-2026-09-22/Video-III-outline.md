# FixProof Video III: evidence that changed the review

> Superseded for recording on September 23, 2026 by
> [FixProof - Video III - Recording Deck.pptx](FixProof%20-%20Video%20III%20-%20Recording%20Deck.pptx)
> and [Video-III-recording-runbook.md](Video-III-recording-runbook.md). Use the
> deck's eight main slides and optional ninth backup slide; this earlier outline
> remains as planning history.

Working outline prepared September 22, 2026. The supplied course listing says
post Video III by **October 6** and submit its peer-feedback report by **October
11**. Confirm the live Canvas instructions, duration, and posting mechanism.
This is a recommended approximately **4–5 minute** update, not a claim that the
assignment mandates that exact length. Progress Report 3 is separately listed
as due October 4; Tony intends to submit it October 1.

## One-sentence message

FixProof's original fixed security and functional suites passed the candidate
patches, but predefined and frozen supplemental tests exposed a missing-input behavior
change in four XSS candidates; later human decisions qualify the original
reviews without rewriting the frozen study.

## Slide and screen sequence

| Time | View | Say and show | Why it is here |
| --- | --- | --- | --- |
| 0:00–0:25 | **1. Research question and scope** | “A scanner warning disappearing is not enough to accept an AI-generated repair. Can separate evidence show what a patch fixes and what it changes?” State that FixProof is a **Python** orchestrator evaluating AI-generated repairs to three deliberately vulnerable **JavaScript/Express** fixtures: XSS, SQLi, traversal. Each fixture has a known vulnerable route, a baseline attack, and expected benign behavior. | Answers the professor's scope/application-construction concern and Raymond's language question. Do not say the 15 attempts represent 15 independent apps. |
| 0:25–1:10 | **2. Workflow diagram** | Show `fixproof-workflow-slide.svg` or its PDF. Point across: fixed fixture and Semgrep finding → focused prompt → model-proposed code → copied workspace → syntax/SAST/security/functional checks → deterministic policy → separate human review when required. Point below: later registered supplemental cases reuse saved candidates; follow-up decisions do not overwrite primary records. | Makes the model's limited authority and evaluation design concrete. Aluor's before/after question is answered by baseline characterization and candidate testing. |
| 1:10–1:50 | **3. Primary evidence, frozen** | Show a simple three-row result table or `/ui/primary.html`: five initial calls per CWE, **15 total**; **5/15** target SAST findings resolved; **10/15** SAST/runtime disagreements; all **15/15** passed the *original targeted* security and functional suites. Ten original conflict reviews: seven bounded acceptances and three additional-testing requests. | Answers Kiang's repetitions/measurement question. These are descriptive outcomes from three fixtures, not a general repair-success rate. Five SQLi “ready for human review” outcomes are not human approvals. |
| 1:50–3:20 | **4. XSS 03 versus XSS 04: the decisive comparison** | Display the patch excerpts and a small table: both passed **3/3 supplemental security** cases; XSS 03 passed **5/5 parity**, XSS 04 passed **4/5**. In `XSS-P01`, an omitted `name` gave the frozen baseline heading `Hello undefined`; XSS 04's `String(value ?? "")` gave `Hello `. XSS 03 retained the baseline behavior. Show XSS 04's later `FOLLOW_UP_REJECT_CANDIDATE` record. | Directly answers Cheick's changed-behavior question. Explain that the registered XSS attacks did **not** remain exploitable in these tests; this is a behavioral-parity decision. The original XSS 04 review requested more testing; the follow-up is a later, separate conclusion. |
| 3:20–4:15 | **5. Interpretation, limits, and next work** | Say XSS 01, 02, and 05 also failed the same missing-input parity case; XSS 01/02 original acceptances were later qualified with separate rejections. The supplement has **55 security passes, zero security failures, five inconclusive symlink cases**; its parity and robustness results are different categories. State one fixture per CWE, fixed payloads, local SQLi rule, and Windows symlink uncertainty. Next: source-checked related-work comparison, clean-package rehearsal, final paper/demo. | Shows consistent human review, transparent limitations, and tangible deliverables. Avoid pooling 140 mixed observations into a “security success rate.” |
| 4:15–4:40 | **6. Feedback request / close** | Ask: “Would a second reviewer of the XSS parity decisions improve confidence more than another vulnerability class?” Optionally ask whether an environment-capable symlink rerun should be prioritized. Close with brief AI-use disclosure: Codex/ChatGPT assisted development and presentation; separate saved OpenAI API calls proposed experimental repairs; Tony personally made the recorded follow-up decisions. | Invites feedback on the most relevant research-design tradeoff, not a vague request for suggestions. |

The workflow graphic uses audience-friendly names for the three automated
outcomes: “Reject,” “Ready for human review,” and “Needs human adjudication.”
These correspond to the exact recorded values `REJECT`,
`READY_FOR_HUMAN_REVIEW`, and `NEEDS_HUMAN_ADJUDICATION`. None is an automatic
human approval.

If Canvas requires a shorter video, keep slides 1, 2, 4, and 6; place the primary
counts and limitations as brief callouts on slide 4. Do not speed-read all 140
observations.

## Evidence to have open before recording

1. [Slide-ready workflow figure](fixproof-workflow-slide.svg) or
   [PDF](fixproof-workflow-slide.pdf). The SVG is editable vector artwork; a
   PNG is provided if the presentation app does not import SVG well. The
   [Graphviz source](fixproof-workflow.dot) is a more detailed alternative.
2. [Primary results](../../primary-results.md) and the dashboard at
   `http://127.0.0.1:8080/ui/primary.html` after starting the local server.
   The dashboard presents **saved evidence**; selecting a row is not a new
   scan, model call, or attack execution.
3. [Supplemental results](../../supplemental-results-v1.md), especially the
   XSS 03/04 comparison and the category-separated totals.
4. XSS 03 [original human review](../../../data/primary_reviews/v1/primary-v1-xss-initial-03/result.json)
   and [supplemental result](../../../data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-03/result.json);
   XSS 04 [original review](../../../data/primary_reviews/v1/primary-v1-xss-initial-04/result.json),
   [supplemental result](../../../data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-04/result.json),
   and [later follow-up](../../../data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-04/result.json).
5. For the consistency point only, the XSS [01](../../../data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-01/result.json)
   and [02](../../../data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-02/result.json)
   follow-up results. Do not spend video time opening every case file.
6. [Full 15-candidate evidence appendix](Video-III-15-candidate-evidence-appendix.pdf)
   ([browser-readable HTML](Video-III-15-candidate-evidence-appendix.html))
   as a backup reference or post-video handout. It has both matrices, ten
   original primary rationales, and all 14 supplemental human rationales. The
   SQLi entries distinguish their missing original primary verdicts from the
   later bounded acceptances. Keep the live video focused on the smaller
   comparison above.

## Recording and claim checks

- Before recording, run `.\.venv\Scripts\python.exe -m fixproof.reproduce --verify`
  and `.\.venv\Scripts\python.exe -m fixproof.evaluation.supplemental_report --check`
  from the repository root, or leave dated verified screenshots/results if a
  live command would consume the short video. These verify stored evidence and
  current software tests; they do not reproduce the historical model calls.
- If using the guided `demo-test.ps1` live replay, label it **pilot**. Its
  selected pilot cases are not primary XSS 01–05 or the saved supplemental
  run. A slide/saved-evidence walkthrough is sufficient for this video.
- Show baseline and candidate results for the *same registered case*.
  `XSS-P01` tests exact behavioral parity, not whether `Hello undefined` is
  ideal product design. The chosen criterion was frozen before supplemental
  candidate execution.
- Do not claim the custom HTML-escaping code is secure in every output context,
  that zero new SAST findings prove zero new vulnerabilities, or that symlink
  escape passed. The copied workspace protects experimental inputs; it is not
  an isolation sandbox for arbitrary hostile code.
- Keep credentials, `.env`, terminal history with keys, and any personal files
  outside the screen capture. Open the final slides in presentation mode to
  check font size, contrast, figure cropping, and timing.

## Feedback-to-evidence map

| Feedback | What Video III demonstrates | Remaining honest limitation |
| --- | --- | --- |
| Professor: concrete vulnerable apps and exact AI role | Three controlled Express fixtures; model only proposes candidate source; independent validators and human boundary are in the chart | This is not a representative corpus of AI-generated applications |
| Professor: systematic choices and rigorous evaluation | Frozen 15-call schedule, same baseline per CWE, registered oracles and explicit denominators | One fixture per CWE and one fixed model/prompt condition limit generalization |
| Raymond: language and functional coverage | Python orchestrates; JavaScript/Express is the repair target; new parity test caught a missed behavior | Targeted checks do not cover production-scale behavior or performance |
| Kiang: repetition and measurement | Five attempts per CWE and separate SAST, security, parity, and robustness results | Repeated repairs of one fixture are not independent app diversity |
| Cheick: new flaws or behavior changes | Candidate rescan and `XSS-P01` failure after the original suites passed | No test suite proves absence of all new vulnerabilities |
| Aluor: deliverables, failure testing, before/after comparison | Working prototype, saved evidence, report/dashboard, baseline/candidate cases, and later human record | Broad API-stress and OWASP Top Ten expansion have not been completed |

The September 16 webinar link supplied by Raymond was not reviewed as research
evidence. Do not cite it as a study you evaluated. References and AI-use
disclosure in the report should be personally checked against the actual work.
