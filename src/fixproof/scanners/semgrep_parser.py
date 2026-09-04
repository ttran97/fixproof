from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def first_item(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return None


def normalize_cwe(value: Any) -> tuple[str | None, str | None]:
    raw = first_item(value)
    if not raw:
        return None, None

    if ":" in raw:
        cwe_id, cwe_name = raw.split(":", 1)
        return cwe_id.strip(), cwe_name.strip()

    return raw.strip(), None


def is_truthy_metadata(value: Any) -> bool:
    """Interpret boolean-like scanner metadata conservatively."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
        }

    return False


def determine_rule_origin(metadata: dict[str, Any]) -> str:
    """Classify scanner evidence without conflating local and OSS rules."""
    if is_truthy_metadata(
        metadata.get("fixproof_controlled_rule")
    ):
        return "fixproof_controlled"

    return "semgrep_oss"


def resolve_source_file(source_root: Path, semgrep_path: str) -> Path | None:
    # Semgrep on Windows may emit backslashes.
    normalized = Path(semgrep_path.replace("\\", "/"))

    candidates = [
        source_root / normalized,
        source_root / normalized.name,
        Path(semgrep_path),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def extract_source_context(
    source_root: Path,
    semgrep_path: str,
    start_line: int,
    end_line: int,
    context_lines: int = 2,
) -> dict[str, Any]:
    source_file = resolve_source_file(source_root, semgrep_path)

    if source_file is None:
        return {
            "snippet": None,
            "context_start_line": None,
            "context_end_line": None,
            "source_file_resolved": False,
        }

    lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()

    context_start = max(1, start_line - context_lines)
    context_end = min(len(lines), end_line + context_lines)

    snippet = "\n".join(
        f"{line_number}: {lines[line_number - 1]}"
        for line_number in range(context_start, context_end + 1)
    )

    return {
        "snippet": snippet,
        "context_start_line": context_start,
        "context_end_line": context_end,
        "source_file_resolved": True,
        "resolved_path": str(source_file),
    }


def make_finding_id(rule_id: str, path: str, start_line: int, end_line: int) -> str:
    raw = f"{rule_id}|{path}|{start_line}|{end_line}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"FP-{digest}"


def normalize_result(result: dict[str, Any], source_root: Path) -> dict[str, Any]:
    extra = result.get("extra", {})
    metadata = extra.get("metadata", {})

    start = result.get("start", {})
    end = result.get("end", {})

    start_line = int(start.get("line", 0))
    end_line = int(end.get("line", start_line))

    cwe_id, cwe_name = normalize_cwe(metadata.get("cwe"))
    vulnerability_class = first_item(metadata.get("vulnerability_class"))
    rule_origin = determine_rule_origin(metadata)

    rule_id = result.get("check_id", "")
    path = result.get("path", "")

    source_context = extract_source_context(
        source_root=source_root,
        semgrep_path=path,
        start_line=start_line,
        end_line=end_line,
    )

    return {
        "finding_id": make_finding_id(rule_id, path, start_line, end_line),
        "scanner": "semgrep",
        "engine": extra.get("engine_kind"),
        "rule_id": rule_id,
        "rule_origin": rule_origin,
        "cwe": cwe_id,
        "cwe_name": cwe_name,
        "vulnerability_class": vulnerability_class,
        "severity": extra.get("severity"),
        "confidence": metadata.get("confidence"),
        "likelihood": metadata.get("likelihood"),
        "impact": metadata.get("impact"),
        "message": extra.get("message"),
        "file": path,
        "start_line": start_line,
        "end_line": end_line,
        "source_context": source_context,
        "status": "new",
        "validation_state": extra.get("validation_state"),
    }


def parse_semgrep(input_file: Path, output_file: Path, source_root: Path) -> dict[str, Any]:
    raw = json.loads(input_file.read_text(encoding="utf-8"))

    findings = [
        normalize_result(result, source_root)
        for result in raw.get("results", [])
    ]

    origin_counts = Counter(
        finding["rule_origin"]
        for finding in findings
    )

    normalized = {
        "schema_version": "0.2",
        "project": "FixProof",
        "scanner": {
            "name": "Semgrep",
            "version": raw.get("version"),
            "engine_requested": raw.get("engine_requested"),
        },
        "scan": {
            "files_scanned": raw.get("paths", {}).get("scanned", []),
            "finding_count": len(findings),
            "error_count": len(raw.get("errors", [])),
            "finding_count_by_rule_origin": dict(
                sorted(origin_counts.items())
            ),
        },
        "findings": findings,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize Semgrep JSON into the FixProof finding schema."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--source-root",
        default=Path("."),
        type=Path,
        help="Project root used to resolve source files from Semgrep paths.",
    )
    args = parser.parse_args()

    normalized = parse_semgrep(args.input, args.output, args.source_root)
    print(
        f"Normalized {normalized['scan']['finding_count']} findings "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
