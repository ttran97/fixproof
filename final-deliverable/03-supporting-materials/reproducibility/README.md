# Reproducibility staging record

## October 22 rehearsal

The full clean-package rehearsal passed. A disposable release-candidate
snapshot installed fresh Python, Playwright, and Node dependencies, verified
the recorded evidence, passed 131 tests twice, and reproduced all four
controlled candidate decisions plus the separated false-success control.

Detailed record:
**docs/coursework/review-2026-10-22/Clean-package-reproduction-validation.md**

## Planned contents

- Clean installation instructions
- Declared Python, Node.js, npm, Semgrep, and browser versions
- Frozen primary-v1 verification command
- Supplemental-v1 verification command
- Human-record binding checks
- PATH-S06 extension verification instructions
- Public-export build and validation instructions
- Expected test counts and stopping conditions
- Known platform limitations and environment differences

The final rehearsal should again begin from a clean package without **.venv/**,
caches, credentials, disposable logs, or open Office lock files. Commands that
would make model calls, rerun frozen experiments, or overwrite evidence must be
clearly separated from read-only verification commands.
