# FixProof clean-package reproduction validation

Completed October 22, 2026.

## Result

PASS. A disposable Git clone of the current repository was converted into a
clean release-candidate snapshot, dependencies were installed into a new
virtual environment, recorded evidence was verified, and the controlled demo
suite reproduced its authoritative decisions.

## Snapshot and isolation

- Source commit: `f68f75708422cd95aa406b1bc644b0951c2e7040`.
- Disposable rehearsal commit: `90493f92d4b9cd686753edaa7e710654c64ce065`.
- The rehearsal commit removed two tracked Microsoft Office lock files and
  added ignore rules for `~$*.docx`, `~$*.pptx`, and `~$*.xlsx`.
- The rehearsal used `scripts/verify-clean.ps1 -InstallDependencies
  -RunDemoSuite`.
- The script exported the temporary commit with `git archive`, expanded it to
  a second disposable directory, created a new Python environment, installed
  Python and Node dependencies, and removed the clean-extraction directory
  after completion.
- The outer rehearsal clone and its temporary environment link were also
  removed after the result was recorded.

## Environment observed

- Python used to create the disposable environment: 3.11.9.
- Node.js: 22.17.1.
- npm: 10.9.2.
- Project dependency pins included OpenAI 3.3.1, Playwright 1.62.0, Pydantic
  2.13.4, and Semgrep 1.136.0.

This reproduction environment is separate from the PATH-S06 WSL2 extension,
which recorded native Linux Node.js 24.19.0 and npm 11.17.0. The clean Windows
rehearsal verified the general evidence and demo package; it did not rerun or
replace the registered Linux extension.

## Verification outcomes

- All 131 automated tests passed during readiness verification.
- `fixproof.reproduce --verify` reported `EVIDENCE VERIFIED`.
- Primary evidence verified: 15/15 scheduled initial attempts.
- Original human conflict reviews verified: 10/10 complete.
- Pilot/control separation checks passed, including exclusion of the non-AI
  control from AI-attempt denominators.
- The guided demo suite reran the test suite and again reported 131/131 tests
  passing.
- Four controlled candidate demonstrations matched their recorded decisions:
  SQLi ready for human review, XSS rejection for functional regression, XSS
  human adjudication for evidence disagreement, and traversal human
  adjudication for evidence disagreement.
- The separate false-success control was also verified.
- The final command reported `Clean-extraction verification passed`.

## Dependency observation

All six `npm ci` steps completed from their committed lockfiles. npm also
reported existing dependency advisories in the fixture trees, including
moderate, high, and critical severity labels. The rehearsal did not run
`npm audit fix`, because changing lockfiles would modify the frozen benchmark
and would require a separately reviewed dependency-update plan. These audit
messages do not invalidate the recorded candidate outcomes, but they should be
disclosed as a dependency-maintenance limitation and triaged before presenting
the package as production-ready software.

## Interpretation boundary

The rehearsal demonstrates that the committed evidence verifier and controlled
demo operate from a clean exported snapshot with freshly installed
dependencies. It is not an independent replication by another person, does
not rerun the original model calls, and does not broaden the three-fixture
benchmark.
