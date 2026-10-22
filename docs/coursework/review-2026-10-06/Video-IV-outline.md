# FixProof Post Video IV outline

Prepared October 6, 2026. Target length: approximately 5-6 minutes. Confirm
the required video length and the October 20/October 25 dates in Canvas before
recording or posting.

## Purpose

Video IV should show how FixProof handled one known uncertainty after Video III:
the Windows-inconclusive `PATH-S06` symbolic-link case. The video should explain
the frozen extension, measured result, human decision, and evidence traceability.
It should not repeat the complete Video III architecture walkthrough or present
the extension as a revision of the frozen primary or supplemental studies.

## Core message

> FixProof did not treat an unavailable security test as a pass. I registered a
> separate Linux/WSL2 extension before execution, reused the saved traversal
> candidates without new model calls, and preserved the earlier records. The
> baseline and all five candidates disclosed the controlled outside-file marker,
> so I recorded five later rejection qualifications.

## Slide and narration outline

### Slide 1 - Progress since Video III (0:00-0:30)

**On screen**

- FixProof: closing a recorded evidence gap
- `PATH-S06` extension completed
- Student-facing case evidence prepared
- Report 4 evaluation and reproducibility work in progress

**Say**

"Since Video III, I focused on a specific unresolved result rather than adding
another broad feature. The supplemental path-traversal symlink test could not
run in the original Windows environment, so it was recorded as inconclusive,
not as a pass. I have now evaluated that case through a separate, frozen WSL2
extension and preserved the earlier evidence."

### Slide 2 - The uncertainty being tested (0:30-1:05)

**On screen**

- Direct traversal: `../../outside-zone/outside-secret.txt`
- Symlink traversal: `link/outside-secret.txt`
- A lexical `path.resolve` check may block `../` while still following an
  in-root link to an outside filesystem target

**Say**

"Traversal 02 illustrates the issue clearly. Its code rejected a direct parent-
directory traversal with HTTP 400, but that did not prove the final filesystem
target remained inside the allowed directory. An in-root symbolic link can
point outside that directory, and `fs.readFile` follows the link. The extension
tested that distinct condition."

Do not say that HTTP 400 is a security risk. In this comparison, the HTTP 400
response is the desired rejection of the direct traversal. The security failure
is the later HTTP 200 response that discloses the outside marker through the
symbolic link.

### Slide 3 - Frozen extension design (1:05-1:50)

**On screen**

| Design element | Registered choice |
| --- | --- |
| Case | One case: `PATH-S06` |
| Inputs | Vulnerable baseline plus five saved traversal candidates |
| Environment | WSL2 Ubuntu with a Linux-native symbolic-link fixture |
| Candidate pass | Marker absent and HTTP 400, 403, or 404 |
| Candidate fail | Controlled outside marker disclosed |
| Isolation | Disposable copies; protected studies fingerprinted |
| Exclusions | No new model calls and no SAST reruns |

**Say**

"I documented the environment, payload, pass/fail rules, and stopping rule
before execution. The vulnerable baseline was a gate: it first had to prove
that the fixture could expose the controlled marker. This design resolved an
environment limitation without changing primary-v1 or supplemental-v1."

Evidence to cite:

- `docs/path-s06-extension-v1-protocol.md`
- `data/extensions/path-s06-v1/protocol-lock.json`
- `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/environment.json`

### Slide 4 - Result and human conclusion (1:50-2:40)

**On screen**

| Target | HTTP status | Marker | Result |
| --- | ---: | --- | --- |
| Vulnerable baseline | 200 | Disclosed | Baseline gate passed |
| Traversal 01 | 200 | Disclosed | Fail |
| Traversal 02 | 200 | Disclosed | Fail |
| Traversal 03 | 200 | Disclosed | Fail |
| Traversal 04 | 200 | Disclosed | Fail |
| Traversal 05 | 200 | Disclosed | Fail |

**Say**

"The baseline behaved as required, and all five saved candidates returned HTTP
200 with the controlled outside-file marker. The registered result was zero
pass, five fail, and zero inconclusive. After reviewing the protocol, baseline,
five candidate records, and manually reproducing Traversal 02, I recorded
`FOLLOW_UP_REJECT_CANDIDATE` for all five. These are later qualifications. They
do not rewrite the original reviews or the five inconclusive supplemental-v1
records."

### Slide 5 - Focused backend evidence demonstration (2:40-4:00)

Use Traversal 02 as the single detailed example. Avoid opening all five records.

1. Open the saved candidate result:
   `data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-02/result.json`.
2. Point to the effective request:
   `/file?name=link%2Foutside-secret.txt`.
3. Point to HTTP `200` and the response marker
   `FIXPROOF_CONTROLLED_TRAVERSAL_SECRET`.
4. Open `docs/coursework/review-2026-09-30/PATH-S06-extension-human-review.md`
   and briefly show the manual WSL2 comparison:
   normal file `200`, direct `../../` request `400`, symlink request `200` with
   the marker.
5. Open `data/extensions/path-s06-v1/human-review-approval.json` and show that
   only Traversal 02 is labeled as manually reproduced.

**Demo explanation**

"The request uses a filename that appears to remain under the public directory,
but `link` resolves to an outside directory. The candidate checks the lexical
path rather than the filesystem object reached after link resolution. The
outside marker in the response is the recorded security failure."

If the public evidence update is live, finish with the test-evidence page and
filter for `PATH-S06`. If it is not live, use the locally validated workbook or
static page and describe deployment as pending. Do not imply that opening the
dashboard reruns a test.

### Slide 6 - Traceability and evaluation boundary (4:00-4:45)

**On screen**

- Primary-v1: 100 recorded runtime observations
- Supplemental-v1: 140 observations - 120 pass, 15 fail, 5 inconclusive
- PATH-S06 extension-v1: 5 separate security observations - all fail
- Human records: 10 original + 14 supplemental + 5 extension = 29
- Student report: 245 case rows with request, response, outcome, reason, and
  evidence path

**Say**

"The counts remain separated because they answer different questions. I do not
combine the 100 primary observations, 140 supplemental observations, and five
extension observations into a single security-success percentage. The workbook
and public table let a reviewer trace each summary count to a request, response,
decision rule, and evidence file."

Evidence to cite:

- `docs/coursework/review-2026-10-01/FixProof-15-candidate-test-evidence.xlsx`
- `docs/coursework/review-2026-10-01/FixProof-student-evidence-validation.json`
- `docs/path-s06-extension-v1-results.md`

### Slide 7 - What this establishes and what it does not (4:45-5:20)

**On screen**

**Established within the registered case**

- All five saved traversal candidates remain vulnerable to `PATH-S06`
- A direct `../` rejection does not establish symlink-target containment
- Later evidence can qualify a decision without rewriting the study history

**Not established**

- Application-wide path-traversal security
- A production repair-success rate
- Generalization beyond the three controlled Express fixtures

**Say**

"This result strengthens confidence in FixProof's evidence and review process,
but it does not broaden the benchmark. One registered symbolic-link case found
a real limitation in all five saved traversal candidates. That is a bounded
finding, not a claim about every path-traversal repair or production system."

### Slide 8 - Report 4 work and feedback request (5:20-5:55)

**On screen**

- Summarize Video III feedback with adopt/defer/decline dispositions
- Verify controls and failure handling
- Run the clean-package reproduction rehearsal
- Refresh active documentation and validate the public package
- Finalize Report 4 with actual hours, limitations, references, and AI-use
  disclosure

**Feedback question**

> For the final project, would it add more confidence to have another person
> reproduce the existing workflow, or to add one more controlled vulnerable
> application? What evidence would you expect to see?

**Say**

"My current priority is reproducibility and documentation rather than expanding
the experiment. I would value feedback on whether an independent reproduction
or one additional controlled fixture would provide the more useful final check."

Close with the planned milestone dates only after confirming them in Canvas.
The repository plan currently lists Report 4 on October 18, Video IV on
October 20, and Peer Feedback Report IV on October 25.

### Closing AI-use disclosure (about 10 seconds)

"ChatGPT and Codex assisted implementation, testing, evidence organization,
documentation, and presentation preparation. Separate saved OpenAI API calls
generated the experimental repair candidates. I reviewed the evidence, made
the recorded human decisions, and remain responsible for the claims."

## Recommended visuals

1. One cropped workflow image for a 15-second recap only.
2. A simple `PATH-S06` diagram: allowed directory -> in-root link -> outside
   controlled file.
3. The six-row baseline/candidate result table.
4. Traversal 02 JSON or terminal evidence.
5. The student evidence workbook or public filter view.

Do not show the full 15-candidate matrix on the main slides. Keep it in backup
material for questions.

## Backup slides or Q&A material

- Why HTTP 400 is correct for direct traversal but HTTP 200 plus the marker is
  a security failure.
- Difference between lexical containment and resolved filesystem containment.
- Why the extension did not rerun SAST or request new patches.
- Why supplemental-v1 retains its five inconclusive `PATH-S06` results.
- Difference between an automated outcome, an original human review, and a
  later qualification.
- Why 15 model calls represent repeated repairs of three fixtures rather than
  15 independent applications.

## Pre-recording checklist

- [ ] Confirm Video IV length, due date, and peer-feedback date in Canvas.
- [ ] Add actual Video III feedback; do not invent feedback that has not been received.
- [ ] Confirm whether the October 1 Netlify package is live.
- [ ] If demonstrating the public site, test the page and workbook download in
      a private browser window.
- [ ] Hide local usernames, transient ports, API identifiers, and credentials.
- [ ] Use one candidate for the backend walkthrough; keep the other four in the
      result table.
- [ ] Rehearse the distinction between direct traversal rejection and symbolic-
      link disclosure.
- [ ] Keep primary-v1, supplemental-v1, and extension counts separate.
- [ ] Save the posted-video receipt or screenshot.
