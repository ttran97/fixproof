from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LANGUAGE_MAP = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".py": "python",
    ".java": "java",
    ".jsp": "jsp",
}


EXPRESS_ROUTE_PATTERN = re.compile(
    r"\b(?:app|router)\."
    r"(?:get|post|put|patch|delete|use|all)\s*\("
)


def detect_language(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()

    return LANGUAGE_MAP.get(
        suffix,
        "unknown",
    )


def resolve_source_file(
    project_root: Path,
    file_path: str,
) -> Path:
    normalized_path = Path(
        file_path.replace("\\", "/")
    )

    source_file = project_root / normalized_path

    if not source_file.exists():
        raise FileNotFoundError(
            f"Could not resolve source file: {source_file}"
        )

    return source_file


def format_source_context(
    lines: list[str],
    context_start: int,
    context_end: int,
    affected_start: int,
    affected_end: int,
    context_type: str,
) -> dict[str, Any]:
    snippet_lines = []

    for line_number in range(
        context_start,
        context_end + 1,
    ):
        marker = (
            ">>"
            if affected_start <= line_number <= affected_end
            else "  "
        )

        snippet_lines.append(
            f"{marker} {line_number}: "
            f"{lines[line_number - 1]}"
        )

    return {
        "context_type": context_type,
        "start_line": context_start,
        "end_line": context_end,
        "affected_start_line": affected_start,
        "affected_end_line": affected_end,
        "code": "\n".join(snippet_lines),
    }


def extract_source_window(
    source_file: Path,
    start_line: int,
    end_line: int,
    context_lines: int = 8,
) -> dict[str, Any]:
    """
    Fallback context extraction.

    Used when a more precise function/route boundary
    cannot be identified.
    """

    lines = source_file.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()

    window_start = max(
        1,
        start_line - context_lines,
    )

    window_end = min(
        len(lines),
        end_line + context_lines,
    )

    return format_source_context(
        lines=lines,
        context_start=window_start,
        context_end=window_end,
        affected_start=start_line,
        affected_end=end_line,
        context_type="line_window",
    )


def extract_express_route(
    source_file: Path,
    start_line: int,
    end_line: int,
) -> dict[str, Any] | None:
    """
    Attempt to locate the enclosing Express route.

    Searches upward from the finding for constructs such as:

        app.get(...)
        app.post(...)
        router.get(...)

    Once found, brace counting is used to locate
    the end of the route callback.
    """

    lines = source_file.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()

    finding_index = start_line - 1

    route_start_index = None

    # Search upward for the nearest Express route.
    for index in range(
        finding_index,
        -1,
        -1,
    ):
        if EXPRESS_ROUTE_PATTERN.search(lines[index]):
            route_start_index = index
            break

    if route_start_index is None:
        return None

    brace_depth = 0
    opening_brace_found = False
    route_end_index = None

    for index in range(
        route_start_index,
        len(lines),
    ):
        line = lines[index]

        open_count = line.count("{")
        close_count = line.count("}")

        if open_count:
            opening_brace_found = True

        brace_depth += open_count
        brace_depth -= close_count

        if (
            opening_brace_found
            and brace_depth == 0
        ):
            route_end_index = index
            break

    if route_end_index is None:
        return None

    # Ensure the finding is actually inside this route.
    if not (
        route_start_index
        <= finding_index
        <= route_end_index
    ):
        return None

    return format_source_context(
        lines=lines,
        context_start=route_start_index + 1,
        context_end=route_end_index + 1,
        affected_start=start_line,
        affected_end=end_line,
        context_type="express_route",
    )


def extract_best_context(
    source_file: Path,
    language: str,
    start_line: int,
    end_line: int,
) -> dict[str, Any]:
    """
    Prefer semantically meaningful context when possible.

    JavaScript/TypeScript Express findings:
        enclosing route

    Otherwise:
        fixed line window
    """

    if language in {
        "javascript",
        "typescript",
    }:
        route_context = extract_express_route(
            source_file=source_file,
            start_line=start_line,
            end_line=end_line,
        )

        if route_context is not None:
            return route_context

    return extract_source_window(
        source_file=source_file,
        start_line=start_line,
        end_line=end_line,
    )


def build_finding_context(
    finding: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    file_path = finding["file"]

    source_file = resolve_source_file(
        project_root=project_root,
        file_path=file_path,
    )

    language = detect_language(
        file_path
    )

    source_context = extract_best_context(
        source_file=source_file,
        language=language,
        start_line=finding["start_line"],
        end_line=finding["end_line"],
    )

    scanner_messages = []
    scanner_rules = []
    rule_origins = set()

    for evidence in finding.get(
        "scanner_evidence",
        [],
    ):
        message = evidence.get("message")

        if message:
            scanner_messages.append(
                message
            )

        scanner_rules.append(
            {
                "finding_id": evidence.get(
                    "finding_id"
                ),
                "rule_id": evidence.get(
                    "rule_id"
                ),
                "rule_origin": evidence.get(
                    "rule_origin",
                    "unknown",
                ),
                "severity": evidence.get(
                    "severity"
                ),
                "confidence": evidence.get(
                    "confidence"
                ),
            }
        )

        rule_origins.add(
            evidence.get(
                "rule_origin",
                "unknown",
            )
        )

    return {
        "context_id": (
            f"CTX-{finding['canonical_id']}"
        ),

        "canonical_id": finding[
            "canonical_id"
        ],

        "finding": {
            "cwe": finding.get("cwe"),
            "cwe_name": finding.get(
                "cwe_name"
            ),
            "vulnerability_class": finding.get(
                "vulnerability_class"
            ),
            "status": finding.get(
                "status"
            ),
        },

        "location": {
            "file": file_path,
            "language": language,
            "start_line": finding[
                "start_line"
            ],
            "end_line": finding[
                "end_line"
            ],
        },

        "scanner_evidence": {
            "finding_count": finding.get(
                "scanner_finding_count",
                0,
            ),
            "rule_origins": sorted(
                rule_origins
            ),
            "rules": scanner_rules,
            "messages": scanner_messages,
        },

        "source_context": source_context,
    }


def build_contexts(
    input_file: Path,
    output_file: Path,
    project_root: Path,
) -> dict[str, Any]:

    correlated = json.loads(
        input_file.read_text(
            encoding="utf-8"
        )
    )

    contexts = []

    for finding in correlated.get(
        "findings",
        [],
    ):
        context = build_finding_context(
            finding=finding,
            project_root=project_root,
        )

        contexts.append(context)

    result = {
        "schema_version": "0.2",
        "project": "FixProof",

        "context_build": {
            "canonical_finding_count": len(
                correlated.get(
                    "findings",
                    [],
                )
            ),
            "contexts_created": len(
                contexts
            ),
        },

        "contexts": contexts,
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build AI remediation contexts "
            "from canonical FixProof findings."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Correlated FixProof findings JSON.",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Context output JSON.",
    )

    parser.add_argument(
        "--project-root",
        default=Path("."),
        type=Path,
        help="FixProof project root.",
    )

    args = parser.parse_args()

    result = build_contexts(
        input_file=args.input,
        output_file=args.output,
        project_root=args.project_root.resolve(),
    )

    print("FixProof Context Builder")

    print(
        "Canonical findings: "
        f"{result['context_build']['canonical_finding_count']}"
    )

    print(
        "Contexts created: "
        f"{result['context_build']['contexts_created']}"
    )

    print(
        f"Output: {args.output}"
    )


if __name__ == "__main__":
    main()
