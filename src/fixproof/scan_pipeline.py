from __future__ import annotations

import argparse
from pathlib import Path

from fixproof.scanners.semgrep_runner import run_semgrep
from fixproof.scanners.semgrep_parser import parse_semgrep
from fixproof.findings.finding_correlator import correlate_findings
from fixproof.agent.context_builder import build_contexts


def run_scan_pipeline(
    target: Path,
    project_root: Path,
    scan_name: str,
) -> dict:
    """
    Execute the FixProof pre-remediation pipeline.

    Stages:
        1. Run Semgrep CE with FixProof controlled rules
        2. Normalize scanner findings
        3. Correlate/deduplicate findings
        4. Build remediation contexts
    """

    # -------------------------------------------------
    # Output paths
    # -------------------------------------------------

    raw_output = (
        project_root
        / "data"
        / "raw_scans"
        / f"{scan_name}.json"
    )

    normalized_output = (
        project_root
        / "data"
        / "normalized"
        / f"{scan_name}.json"
    )

    correlated_output = (
        project_root
        / "data"
        / "correlated"
        / f"{scan_name}.json"
    )

    context_output = (
        project_root
        / "data"
        / "contexts"
        / f"{scan_name}.json"
    )

    print("=" * 60)
    print("FixProof Scan Pipeline")
    print("=" * 60)
    print(f"Target: {target}")
    print()

    # -------------------------------------------------
    # Stage 1: Run Semgrep
    # -------------------------------------------------

    print("[1/4] Running Semgrep CE...")

    run_semgrep(
        target=target,
        output=raw_output,
        project_rule_dir=project_root / "rules",
    )

    print()

    # -------------------------------------------------
    # Stage 2: Normalize findings
    # -------------------------------------------------

    print("[2/4] Normalizing findings...")

    normalized = parse_semgrep(
        input_file=raw_output,
        output_file=normalized_output,
        source_root=project_root,
    )

    scanner_count = normalized[
        "scan"
    ]["finding_count"]

    print(
        f"Normalized {scanner_count} findings."
    )

    print()

    # -------------------------------------------------
    # Stage 3: Correlate findings
    # -------------------------------------------------

    print("[3/4] Correlating findings...")

    correlated = correlate_findings(
        input_file=normalized_output,
        output_file=correlated_output,
    )

    correlation_stats = correlated[
        "correlation"
    ]

    canonical_count = correlation_stats[
        "canonical_finding_count"
    ]

    duplicates_collapsed = correlation_stats[
        "duplicates_collapsed"
    ]

    print(
        f"Canonical findings: {canonical_count}"
    )

    print(
        f"Duplicates collapsed: {duplicates_collapsed}"
    )

    print()

    # -------------------------------------------------
    # Stage 4: Build remediation contexts
    # -------------------------------------------------

    print("[4/4] Building remediation contexts...")

    contexts = build_contexts(
        input_file=correlated_output,
        output_file=context_output,
        project_root=project_root,
    )

    contexts_created = contexts[
        "context_build"
    ]["contexts_created"]

    print(
        f"Contexts created: {contexts_created}"
    )

    # -------------------------------------------------
    # Final summary
    # -------------------------------------------------

    print()
    print("=" * 60)
    print("FixProof Preparation Complete")
    print("=" * 60)

    print(
        f"Scanner findings: {scanner_count}"
    )

    print(
        f"Canonical findings: {canonical_count}"
    )

    print(
        f"Duplicates collapsed: {duplicates_collapsed}"
    )

    print(
        f"Remediation contexts: {contexts_created}"
    )

    print()

    print(f"Raw results: {raw_output}")
    print(
        f"Normalized results: {normalized_output}"
    )
    print(
        f"Correlated results: {correlated_output}"
    )
    print(
        f"Context results: {context_output}"
    )

    print()

    if canonical_count:
        print("Canonical FixProof Findings:")

        for finding in correlated[
            "findings"
        ]:
            print(
                f"- {finding['canonical_id']} | "
                f"{finding.get('cwe') or 'No CWE'} | "
                f"{finding.get('vulnerability_class') or 'Unknown'} | "
                f"{finding['file']}:"
                f"{finding['start_line']} | "
                f"Scanner evidence: "
                f"{finding['scanner_finding_count']}"
            )

    return {
        "normalized": normalized,
        "correlated": correlated,
        "contexts": contexts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the FixProof SAST ingestion "
            "and remediation-context pipeline."
        )
    )

    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="Source file or application directory to scan.",
    )

    parser.add_argument(
        "--name",
        required=False,
        help="Name used for FixProof output files.",
    )

    parser.add_argument(
        "--project-root",
        default=Path("."),
        type=Path,
        help="FixProof project root.",
    )

    args = parser.parse_args()

    if not args.target.exists():
        raise FileNotFoundError(
            f"Scan target does not exist: {args.target}"
        )

    if args.name:
        scan_name = args.name

    elif args.target.is_file():
        scan_name = args.target.parent.name

    else:
        scan_name = args.target.name

    run_scan_pipeline(
        target=args.target,
        project_root=args.project_root.resolve(),
        scan_name=scan_name,
    )


if __name__ == "__main__":
    main()
