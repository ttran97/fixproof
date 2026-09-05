# FixProof documentation and repository guide

Updated September 5, 2026. Start with [prototype status](prototype-status.md)
for current capabilities and remaining work. Use
[the submission guide](cs6727-submission-guide.md) to understand the source
tree, explain the project, and prepare the paper and presentation.

## Active references

| Document | Purpose |
|---|---|
| [Prototype status](prototype-status.md) | Current implementation, limits, and next milestone |
| [Primary results](primary-results.md) | Generated 15-attempt results; regenerate rather than manually edit |
| [Primary review guide](primary-review-guide.md) | Personally inspect and record the ten conflict reviews |
| [Submission guide](cs6727-submission-guide.md) | File structure, professor-facing explanation, paper/video outline |
| [Architecture](architecture.md) | Current components and trust boundaries |
| [Reproducibility](reproducibility.md) | Installation, evidence checks, live demos, packaging |
| [Pilot evidence map](evidence-map.md) | Selected pilot artifacts and separate non-AI control |
| [Pilot evaluation report](evaluation-report.md) | Generated four-attempt pilot metrics |
| [Demo guide](demo-guide.md) | Rehearsing the recorded pilot candidates with live runtime checks |
| [Methodology](methodology.md), [threat model](threat-model.md), [artifact schema](artifact-schema.md) | Design background; consult the frozen protocol for primary-v1 conditions |
| [Related work](related-work.md) | Literature/contribution background to personally verify and develop for the final paper |

## Preserve frozen and historical material

- [Study protocol v1](study-protocol-v1.md), `benchmarks/primary/v1/`, the
  primary manifests/trial plan, selected baseline evidence, and
  `data/primary_trials/v1/` define the completed study. Do not change them to
  make later code or results appear part of the original experiment.
- The primary manifest also binds 13 implementation files. The report
  verifier checks those hashes. Supplemental work belongs outside that
  frozen implementation boundary.
- [Initial course alignment review](cs6727-alignment-review.md) records the
  September 4 audit. Its original missing-feature list and work estimate are
  historical; use the current status page for remaining work.
- [Historical implementation notes](../IMPLEMENTATION_GUIDE.md) preserve the
  development sequence. Their old next-step instructions are not the active
  backlog.
- `sample_apps/python-smoke-test/` is an early scanner exercise. It does not
  demonstrate Python remediation support. Keep it as labeled history.
- Older pilot scans, decisions, and adjudications can coexist with selected
  evidence. The pilot manifest determines what counts. Retain these records
  unless a later, separately reviewed cleanup proves that no evidence or
  document links depend on them.

## What to keep or exclude

| Paths | Treatment |
|---|---|
| `src/`, `tests/`, `ui/`, `rules/`, `scripts/`, package manifests and lockfiles | Keep: implementation and reproducibility inputs |
| `benchmarks/`, `data/`, tracked `workspaces/`, `sample_apps/` | Keep: curated experiment inputs and evidence; do not bulk-delete or relocate |
| `docs/`, root README | Keep: active references, frozen protocol, labeled history |
| `.env` | Keep local if needed; never include in submission |
| `.venv/`, `node_modules/`, `__pycache__/`, package build metadata | Rebuildable local dependencies/cache; excluded from submission |
| `dist/` | Generated archives, screenshots, verification copies/logs; retain useful logs locally and exclude from source archive |

No experimental artifacts need removal to complete the prototype. The useful
cleanup is clearer navigation and current terminology. A tracked-file archive
already avoids shipping installed dependencies and local configuration.
Keep the verification copy until its logs and any needed outputs have been
reviewed; deleting it is optional disk-space housekeeping.

## Next work, in order

1. Review the ten primary conflict packets and record actual conclusions.
   Investigate any requested additional tests as separate supplemental evidence.
2. Explain the refined scope in the next course report: three deliberately
   vulnerable Express fixtures, AI-generated repairs, a controlled 15-attempt
   study, and a separate lifecycle replay. Do not claim a representative
   AI-generated application corpus.
3. Prepare the paper and presentation using measured results, limitations,
   literature comparisons, and actual AI-use records. Confirm Canvas deadlines,
   format, and required progress/peer submissions.
4. Review and commit the intended snapshot, run the clean-archive checks,
   then build and inspect the final submission archive.
