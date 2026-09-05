# FixProof Artifact and Experiment-Record Contract

## Purpose

This document defines the minimum evidence expected for an auditable FixProof
attempt. Existing JSON artifacts remain the machine-readable authority; this
contract prevents future repeated trials from silently changing their meaning.

## Attempt identity

An attempt is uniquely identified by:

- `case_id` and application name;
- CWE;
- canonical finding ID;
- attempt number;
- optional prior-attempt link;
- candidate origin and metric scope.

The primary aggregation unit is a remediation attempt. Non-AI policy controls
must be stored and reported separately from primary AI attempts.

## Required evidence chain

The paths below describe pilot artifacts. The equivalent primary chain is
inside `data/primary_trials/v1/cases/<case>/attempt-XX/`, with preparation
records selected by its frozen manifest. Primary human records live separately
under `data/primary_reviews/v1/`; the derived report is
`data/evaluation/primary-report.json`. Do not move bound primary artifacts
to match the pilot directory layout.

| Stage | Required record | Minimum meaning |
|---|---|---|
| Ground truth | `data/ground_truth/<application>.json` | Independent vulnerability definition, source, sink, route, and expected vulnerable behavior |
| Raw SAST | `data/raw_scans/*.json` | Scanner version, exact findings, configuration outcome, and scan target |
| Normalized/correlated | `data/normalized/` and `data/correlated/` | Stable project fields, canonical finding, evidence count, and rule provenance |
| Model input | `data/contexts/` and `data/prompts/` | Source context and exact structured remediation request |
| Model output | `data/remediations/<canonical-id>-attempt-XX.json` | Model, response ID, unchanged candidate, analysis, assumptions, and lineage |
| Isolated patch | `workspaces/**/workspace.json` and `candidate.patch` | Candidate source, patch, hashes, and proof the baseline was not modified |
| Preliminary validation | `data/validation/` | Syntax result, target SAST status, new findings, and comparison key |
| Runtime security | `data/security_validation/` | Test cases, observed responses, criteria, and aggregate status |
| Functional regression | `data/functional_validation/` | Expected and observed behavior per case and aggregate status |
| Policy | `data/decisions/` | Policy version, reason codes, classification, disposition, and retry state |
| Human boundary | `data/adjudications/` when required | Immutable packet plus separate human result |

## Path rules

- New artifacts should store repository-relative POSIX-style paths.
- Historical absolute paths may remain unchanged when they are already bound by
  hashes. The evidence loader relocates known repository paths under the active
  project root instead of following an old checkout.
- An artifact path must not escape the active project root.
- Selected workspace metadata, candidate source, and patch must be included in
  a reproducible submission even though disposable dependencies remain ignored.

## Integrity and mutability

- Raw scans, prompts, remediation responses, workspace records, validation
  results, decisions, and adjudication records are immutable experimental
  evidence.
- Generated evaluation reports are derived and may be rebuilt from the
  authoritative manifest.
- Corrections must create a new evidence revision; they must not overwrite or
  relabel historical evidence.
- JSON artifact bindings use byte-exact SHA-256. Candidate source and patch
  bindings use normalized UTF-8 text hashes where declared by the packet.

## Required trial metadata before primary repetitions

- frozen prompt/template version;
- exact model and model settings;
- scanner version and configuration provenance;
- controlled-rule revision, if any;
- planned attempts per case;
- retry and stopping rules;
- exclusion and failed-run handling;
- primary metrics and denominator;
- SAST-only comparison rule;
- timestamp and software/environment versions.

The frozen decisions and completed technical gates are recorded in
`data/evaluation/trial-plan.json`. The versioned benchmark contract and hashes
are in `data/evaluation/primary-benchmark-manifest.json`, and the executable
baseline evidence is in `data/evaluation/primary-baseline-verification.json`.
Their rationale is documented in `docs/study-protocol-v1.md`.
