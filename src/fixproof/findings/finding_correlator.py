from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def make_canonical_id(
    file_path: str,
    cwe: str | None,
    start_line: int,
) -> str:
    """
    Generate a stable FixProof canonical finding ID.

    For the MVP, findings with the same file, CWE, and source
    location are considered the same underlying vulnerability.
    """
    raw = f"{file_path}|{cwe}|{start_line}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    return f"CF-{digest}"


def correlation_key(finding: dict[str, Any]) -> tuple:
    """
    Define when multiple scanner findings represent the same
    underlying source-code vulnerability.

    MVP rule:
        same file
        + same CWE
        + same start line
    """
    return (
        finding.get("file"),
        finding.get("cwe"),
        finding.get("start_line"),
    )


def correlate_findings(
    input_file: Path,
    output_file: Path,
) -> dict[str, Any]:

    normalized = json.loads(
        input_file.read_text(encoding="utf-8")
    )

    groups: dict[tuple, list[dict[str, Any]]] = {}

    for finding in normalized.get("findings", []):
        key = correlation_key(finding)

        if key not in groups:
            groups[key] = []

        groups[key].append(finding)

    canonical_findings = []

    for _, findings in groups.items():

        primary = findings[0]

        canonical_id = make_canonical_id(
            file_path=primary["file"],
            cwe=primary.get("cwe"),
            start_line=primary["start_line"],
        )

        scanner_evidence = []

        for finding in findings:
            scanner_evidence.append(
                {
                    "finding_id": finding["finding_id"],
                    "rule_id": finding["rule_id"],
                    "rule_origin": finding.get(
                        "rule_origin",
                        "unknown",
                    ),
                    "severity": finding.get("severity"),
                    "confidence": finding.get("confidence"),
                    "message": finding.get("message"),
                }
            )

        canonical = {
            "canonical_id": canonical_id,

            "cwe": primary.get("cwe"),
            "cwe_name": primary.get("cwe_name"),
            "vulnerability_class": primary.get(
                "vulnerability_class"
            ),

            "file": primary["file"],
            "start_line": primary["start_line"],
            "end_line": primary["end_line"],

            "source_context": primary.get(
                "source_context"
            ),

            "status": primary.get(
                "status",
                "new"
            ),

            "scanner_finding_count": len(findings),

            "rule_origins": sorted(
                {
                    finding.get(
                        "rule_origin",
                        "unknown",
                    )
                    for finding in findings
                }
            ),

            "scanner_evidence": scanner_evidence,
        }

        canonical_findings.append(canonical)

    correlated = {
        "schema_version": "0.2",
        "project": "FixProof",

        "correlation": {
            "input_finding_count": len(
                normalized.get("findings", [])
            ),

            "canonical_finding_count": len(
                canonical_findings
            ),

            "duplicates_collapsed": (
                len(normalized.get("findings", []))
                - len(canonical_findings)
            ),
        },

        "findings": canonical_findings,
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file.write_text(
        json.dumps(
            correlated,
            indent=2
        ),
        encoding="utf-8",
    )

    return correlated


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Correlate and deduplicate normalized "
            "FixProof findings."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    result = correlate_findings(
        input_file=args.input,
        output_file=args.output,
    )

    stats = result["correlation"]

    print("FixProof Finding Correlation")
    print(
        f"Input findings: "
        f"{stats['input_finding_count']}"
    )
    print(
        f"Canonical findings: "
        f"{stats['canonical_finding_count']}"
    )
    print(
        f"Duplicates collapsed: "
        f"{stats['duplicates_collapsed']}"
    )


if __name__ == "__main__":
    main()
