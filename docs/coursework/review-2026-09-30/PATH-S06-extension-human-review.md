# PATH-S06 extension human-review worksheet

Prepared September 30, 2026. Tony's confirmation and approved verdicts are
recorded below; machine-readable qualification records are stored separately
under `data/extensions/path-s06-v1/human-reviews/`.

## What to review

1. Read the [extension results](../../path-s06-extension-v1-results.md) and the
   [frozen protocol](../../path-s06-extension-v1-protocol.md).
2. Open the [run summary](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/summary.json).
3. Inspect at least one full candidate record, then confirm that the other four
   summary rows report the same decisive facts: HTTP 200 and
   `marker_disclosed: true`.
4. Compare the candidate patch with its saved source. Confirm that the code
   checks the lexical path but does not establish containment of the
   filesystem target after symbolic-link resolution.
5. Decide whether the conclusive security disclosure changes the prior later
   verdict. Do not edit the original primary review or the existing
   `supplemental-v1` follow-up record.

## Outcome matrix

| Candidate | Earlier supplemental-v1 follow-up | PATH-S06 extension | Recommended new qualification |
| --- | --- | --- | --- |
| Traversal 01 | `FOLLOW_UP_REJECT_CANDIDATE` | Fail: HTTP 200; marker disclosed | Reaffirm rejection with new supporting evidence |
| Traversal 02 | `FOLLOW_UP_REQUEST_MORE_TESTING` | Fail: HTTP 200; marker disclosed | `FOLLOW_UP_REJECT_CANDIDATE` |
| Traversal 03 | `FOLLOW_UP_REQUEST_MORE_TESTING` | Fail: HTTP 200; marker disclosed | `FOLLOW_UP_REJECT_CANDIDATE` |
| Traversal 04 | `FOLLOW_UP_REQUEST_MORE_TESTING` | Fail: HTTP 200; marker disclosed | `FOLLOW_UP_REJECT_CANDIDATE` |
| Traversal 05 | `FOLLOW_UP_REQUEST_MORE_TESTING` | Fail: HTTP 200; marker disclosed | `FOLLOW_UP_REJECT_CANDIDATE` |

## Evidence links

- [Traversal 01 extension result](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-01/result.json)
- [Traversal 02 extension result](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-02/result.json)
- [Traversal 03 extension result](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-03/result.json)
- [Traversal 04 extension result](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-04/result.json)
- [Traversal 05 extension result](../../../data/extensions/path-s06-v1/runs/20260930T180925912688Z-path-s06-v1/candidates/primary-v1-path-traversal-initial-05/result.json)

## Suggested rationale

Use this only after personally confirming the evidence:

> I reviewed the saved candidate, its original and supplemental-v1 decisions,
> and the separately frozen PATH-S06 extension result. In WSL2, the vulnerable
> baseline established the control by returning the outside-file marker
> through an in-root symbolic link. This candidate then returned HTTP 200 and
> disclosed the same marker. Its lexical `path.resolve` containment check did
> not verify the filesystem target followed by `fs.readFile`. I therefore
> reject the candidate for the bounded benchmark because the registered
> symbolic-link traversal remains exploitable. This is a later qualification;
> it does not overwrite primary-v1, supplemental-v1, or the earlier human
> record.

## Tony's confirmation

- [x] I inspected the protocol, summary, and candidate evidence.
- [x] I confirmed that the baseline gate passed.
- [x] I confirmed HTTP 200 and marker disclosure for all five candidates.
- [x] I understand that the five original supplemental-v1 inconclusive
  observations remain unchanged.
- [x] I approve the proposed later qualifications and rationale.

Approval statement:

> I reviewed the frozen PATH-S06 protocol, baseline gate, run summary, and all
> five recorded candidate results. I also manually reproduced Traversal 02 in
> WSL2. I approve `FOLLOW_UP_REJECT_CANDIDATE` as a separate PATH-S06 extension
> qualification for Traversal 01-05. Traversal 01's existing rejection is
> reaffirmed, while Traversal 02-05 change from request-more-testing to
> rejection based on the later extension evidence. The original primary-v1 and
> supplemental-v1 records remain unchanged.

## Manual verification transcript — unregistered spot-check

This transcript is Tony's personal reproduction of Traversal 02. It supports
his understanding of the registered result but is not added to the extension
counts or to supplemental-v1. The registered extension remains the
machine-readable evidence source.

```console
tony_tran@Tony-Tran-Gaming-PC:/tmp/fixproof-manual-path-s06-tony$ cp "$PROJECT/data/primary_trials/v1/cases/path-traversal/attempt-02/workspace/CF-17216aac7b7a/attempt-02/app/app.js" "$DEMO/app.js"
tony_tran@Tony-Tran-Gaming-PC:/tmp/fixproof-manual-path-s06-tony$ PORT=3106 node app.js
FixProof primary path-traversal benchmark running on port 3106

tony_tran@Tony-Tran-Gaming-PC:/mnt/c/Users/Tony Tran/Documents/fixproof$ curl -i 'http://127.0.0.1:3106/file?name=welcome.txt'
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/plain; charset=utf-8
Content-Length: 33
ETag: W/"21-/SK5INosJvb0DhKDQecgqrD0ba0"
Date: Wed, 30 Sep 2026 19:39:53 GMT
Connection: keep-alive
Keep-Alive: timeout=5

FixProof public fixture: welcome
tony_tran@Tony-Tran-Gaming-PC:/mnt/c/Users/Tony Tran/Documents/fixproof$ curl -iG \
  --data-urlencode 'name=../../outside-zone/outside-secret.txt' \
  'http://127.0.0.1:3106/file'
HTTP/1.1 400 Bad Request
X-Powered-By: Express
Content-Type: application/json; charset=utf-8
Content-Length: 29
ETag: W/"1d-tPwVUxxqMgqbBYRFqgt326smyIc"
Date: Wed, 30 Sep 2026 19:39:56 GMT
Connection: keep-alive
Keep-Alive: timeout=5

tony_tran@Tony-Tran-Gaming-PC:/mnt/c/Users/Tony Tran/Documents/fixproof$ curl -i 'http://127.0.0.1:3106/file?name=link%2Foutside-secret.txt'
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/plain; charset=utf-8
Content-Length: 37
ETag: W/"25-w+WIyS86DAzTfTBOMppDmCyts10"
Date: Wed, 30 Sep 2026 19:40:08 GMT
Connection: keep-alive
Keep-Alive: timeout=5

FIXPROOF_CONTROLLED_TRAVERSAL_SECRET
```

Human rationale for Traversal 02: I manually verified Traversal 02 in WSL2.
The candidate preserved normal access to `welcome.txt` and returned HTTP 400
for a direct `../../` traversal request. However, an in-root symbolic link
pointing outside the allowed directory bypassed the lexical `path.resolve`
check. The candidate returned HTTP 200 and disclosed the controlled
outside-file marker. I therefore reject the candidate for the bounded
benchmark because the registered PATH-S06 symbolic-link traversal remains
exploitable. This later qualification preserves the original primary and
supplemental-v1 records.

