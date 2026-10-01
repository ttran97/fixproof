# FixProof PATH-S06 Extension v1 Protocol

**Protocol ID:** `path-s06-extension-v1`  
**Source case:** `supplemental-v1` / `PATH-S06`  
**Approved by:** Tony Tran  
**Freeze date:** September 30, 2026  
**Status:** Frozen before execution

## Purpose and boundary

This extension resolves the environment-caused uncertainty for the one
registered supplemental security case that could not execute on Windows. It
does not reopen or overwrite `primary-v1` or `supplemental-v1`, does not make a
new model call, and does not rerun SAST. The original five `PATH-S06`
observations remain inconclusive in `supplemental-v1`; results from this
extension are separately versioned later evidence.

The extension evaluates the frozen vulnerable path-traversal baseline and the
same five saved primary path-traversal candidates. It makes no claim about
other repositories, vulnerability classes, or production readiness.

## Registered case

- **Case ID:** `PATH-S06`
- **Category:** security
- **Environment:** a Linux filesystem capable of ordinary symbolic links
- **Fixture:** inside the allowed `public-files` directory, create `link` as a
  symbolic link to a disposable directory outside `public-files`. Place the
  controlled marker in `outside-secret.txt` in that outside directory.
- **Request:** `GET /file?name=link%2Foutside-secret.txt`
- **Marker:** `FIXPROOF_CONTROLLED_TRAVERSAL_SECRET`

## Frozen oracles

The vulnerable baseline is a gate. It must return HTTP 200 and disclose the
exact controlled marker through the link. If it does not, stop the run before
candidate execution and preserve that run as a baseline-gate failure.

For each candidate:

- **Pass:** the marker is absent and the response status is exactly HTTP 400,
  403, or 404.
- **Fail:** the marker is disclosed, or the response is any status outside 400,
  403, or 404. In particular, HTTP 200 without the marker is still a contract
  failure, although it is not marker disclosure.
- **Inconclusive:** the symlink fixture, application process, loopback request,
  or other required infrastructure cannot execute reliably and therefore no
  valid response can be judged.

Security disclosure and status-contract conformance are recorded separately so
that a failed status contract is not mislabeled as a successful traversal
attack.

## Inputs

The machine-readable definition at
`tests/extensions/path_s06/v1/case.json` binds:

1. the primary-v1 vulnerable path-traversal application;
2. the five saved primary traversal candidate `app.js` files;
3. the committed package manifest and lockfile; and
4. the exact case and oracle above.

The protocol lock at `data/extensions/path-s06-v1/protocol-lock.json` binds this
document, the machine-readable definition, and the focused runner
implementation by SHA-256. The runner must refuse execution if a binding has
changed.

## Execution rules

1. Execute on Linux using a native Linux Node.js runtime. Record the kernel,
   Python, Node.js, and npm versions.
2. Prepare all application workspaces in a disposable Linux-native temporary
   directory. Restore dependencies from the committed lockfile with `npm ci`.
3. Verify the protocol lock before creating an evidence run.
4. Run the vulnerable baseline first. Do not execute candidates unless the
   baseline gate passes.
5. Apply the same fixture, request, timeout, and oracle to attempts 01-05.
6. Store all responses, process output, evaluations, input hashes, and summary
   counts under `data/extensions/path-s06-v1/runs/<run-id>/`.
7. Preserve infrastructure failures and aborted runs. Do not silently rerun
   only an unfavorable candidate. A complete retry requires a new run ID and
   the earlier run remains recorded.
8. Do not edit any `data/supplemental/v1/` or `data/primary_trials/v1/`
   artifact.
9. Human interpretation is recorded later and separately; the runner does not
   approve a candidate.

## Stopping rule

One complete baseline-plus-five-candidate run is the planned extension. Stop
after that complete run. Additional execution requires a documented reason and
a new run ID. A protocol or oracle change requires a new protocol version.

## Reporting rule

Report the baseline gate, each of the five candidate outcomes, marker
disclosure separately from status conformance, the complete environment, and
any failure or inconclusive result. Describe this as a separately versioned
qualification of the original PATH-S06 uncertainty, not as a revision of the
140 supplemental-v1 observations.
