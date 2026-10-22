# FixProof Video IV recording script

**Target:** about 2 minutes 40 seconds; remain under 3 minutes.  
**Main recording route:** slides 1-7.  
**Screenshot slides 8-12:** validated backup evidence for Traversal 01-05; do
not narrate all five in the main recording.

The registered result remains the frozen PATH-S06 extension. Manual terminal
captures are later spot-checks for explanation and do not add observations to
the registered denominator.

## Slide 1 - Title (0:00-0:18)

Hi everyone. Since Video III, I addressed one unresolved FixProof result.
PATH-S06 could not create a symbolic link on Windows, so it remained
inconclusive. I then evaluated the same case in a separately versioned WSL2
extension.

## Slide 2 - Why the original result was unclear (0:18-0:43)

The fixes blocked direct `../` traversal with HTTP 400, which is the desired
result. But they validated only the path text. `link/outside-secret.txt`
contains no `..`, while the link can point outside `public-files`. Because
Windows could not create that link, the original case was neither a pass nor a
fail.

## Slide 3 - Frozen extension design (0:43-1:10)

Before running it, I froze the payload, Linux environment, and decision rule.
The vulnerable baseline first had to reveal the controlled marker. A candidate
passed only if the marker was absent and the response was HTTP 400, 403, or
404. I reused the five saved AI-generated fixes in disposable copies, with no
new model calls or SAST reruns.

## Slide 4 - Measured result (1:10-1:35)

The original vulnerable app was a positive control. Its HTTP 200 response and
outside-file marker confirmed that the Linux symlink setup worked; this was not
a security pass, and the control is not part of the five-candidate count. All
five saved fixes also returned HTTP 200 and the marker, so the registered result
is zero pass, five fail, and zero inconclusive.

## Slide 5 - Traversal 02 example (1:35-2:02)

Traversal 02 makes the failure concrete. Normal access returned HTTP 200, and
the direct `../` request returned HTTP 400. But the symlink request returned
HTTP 200 with `FIXPROOF_CONTROLLED_TRAVERSAL_SECRET`. The lexical check accepted
the path, and `fs.readFile` followed the link outside the allowed folder. My
manual WSL2 example supports that interpretation but does not change the
registered count.

## Slide 6 - Preserved evidence history (2:02-2:23)

The later evidence qualifies the conclusion without rewriting the study.
Primary-v1 keeps its 15 attempts. Supplemental-v1 keeps its 140 observations,
including five inconclusive PATH-S06 outcomes. The separate extension records
five failures and five later human rejection qualifications.

## Slide 7 - Meaning and next steps (2:23-2:55)

The bounded conclusion is that all five saved fixes fail this one registered
symbolic-link case. It is not an application-wide claim or a production
repair-success rate.

Next, I will reconcile peer feedback, complete the clean-package reproduction
and failure-handling audit, refresh the documentation and public evidence, and
carry the separated results and limitations into the final report and
presentation. I would value feedback on whether independent reproduction or
one additional controlled fixture would add more confidence.

ChatGPT and Codex assisted development, testing, documentation, and
presentation preparation. I reviewed the evidence, made the human decisions,
and remain responsible for the claims.

## Optional screenshot statement

Use this only if briefly showing a correct terminal capture:

> This manual WSL2 spot-check verifies the frozen source hash, normal access,
> direct traversal rejection, and symlink disclosure. It supports my review but
> is not another registered experimental observation.

## Pre-recording checks

- The five backup captures were checked against their intended target numbers,
  saved-source paths, SHA-256 values, and ports.
- Stop the main recording after slide 7. Use slides 8-12 only if a reviewer asks
  to see the terminal-level evidence.
- Keep usernames and machine names cropped if the deck will be distributed.
- Do not describe HTTP 400 as the security failure. The failure is HTTP 200
  plus disclosure of the controlled marker through the link.
- Keep primary-v1, supplemental-v1, and PATH-S06 extension counts separate.
- Verify the final video and peer-feedback deadlines in Canvas before posting.
