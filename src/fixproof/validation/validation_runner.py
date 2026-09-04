from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from fixproof.scanners.semgrep_runner import run_semgrep
from fixproof.scanners.semgrep_parser import parse_semgrep
from fixproof.findings.finding_correlator import correlate_findings
from fixproof.agent.context_builder import extract_express_route


EXPRESS_SIGNATURE_PATTERN = re.compile(
    r'\b(?:app|router)\.'
    r'(get|post|put|patch|delete|use|all)'
    r'\s*\(\s*["\']([^"\']+)["\']'
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def resolve_source_file(
    root: Path,
    file_path: str,
) -> Path:
    """
    Resolve a finding's source file.

    Supports:
    - project-relative paths
    - absolute paths
    - workspace copies where only the filename is stable
    """

    normalized = Path(
        file_path.replace("\\", "/")
    )

    candidates = []

    if normalized.is_absolute():
        candidates.append(normalized)
    else:
        candidates.append(root / normalized)
        candidates.append(normalized)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    # Workspace paths may differ from baseline paths.
    matches = list(
        root.rglob(normalized.name)
    )

    file_matches = [
        path
        for path in matches
        if path.is_file()
    ]

    if len(file_matches) == 1:
        return file_matches[0].resolve()

    raise FileNotFoundError(
        f"Could not uniquely resolve source file "
        f"'{file_path}' under '{root}'."
    )


def run_syntax_check(
    source_file: Path,
) -> dict[str, Any]:
    """
    Perform syntax validation.

    Current MVP:
    JavaScript -> node --check
    """

    suffix = source_file.suffix.lower()

    if suffix != ".js":
        return {
            "status": "not_implemented",
            "tool": None,
            "return_code": None,
            "stdout": "",
            "stderr": (
                f"Syntax validation is not implemented "
                f"for {suffix}"
            ),
        }

    result = subprocess.run(
        [
            "node",
            "--check",
            str(source_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    return {
        "status": (
            "pass"
            if result.returncode == 0
            else "fail"
        ),
        "tool": "node --check",
        "return_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def get_scope_signature(
    source_file: Path,
    finding: dict[str, Any],
) -> str:
    """
    Determine the semantic scope of a finding.

    For Express routes, this produces values such as:

        express:get:/hello
        express:get:/user

    Application-level findings fall back to:

        file
    """

    route_context = extract_express_route(
        source_file=source_file,
        start_line=finding["start_line"],
        end_line=finding["end_line"],
    )

    if route_context is not None:
        code = route_context.get(
            "code",
            "",
        )

        match = EXPRESS_SIGNATURE_PATTERN.search(
            code
        )

        if match:
            method = match.group(1)
            route = match.group(2)

            return (
                f"express:{method}:{route}"
            )

    return "file"


def make_semantic_key(
    finding: dict[str, Any],
    source_file: Path,
) -> str:
    """
    Create a comparison key that does not depend on
    unstable source line numbers.

    MVP key:

        filename + CWE + semantic scope
    """

    cwe = finding.get("cwe") or "NO-CWE"

    scope = get_scope_signature(
        source_file=source_file,
        finding=finding,
    )

    return (
        f"{source_file.name}"
        f"|{cwe}"
        f"|{scope}"
    )


def build_finding_map(
    findings: list[dict[str, Any]],
    source_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    """
    Group findings by semantic identity.
    """

    result: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    for finding in findings:
        source_file = resolve_source_file(
            root=source_root,
            file_path=finding["file"],
        )

        semantic_key = make_semantic_key(
            finding=finding,
            source_file=source_file,
        )

        record = {
            "semantic_key": semantic_key,
            "canonical_id": finding.get(
                "canonical_id"
            ),
            "cwe": finding.get("cwe"),
            "vulnerability_class": finding.get(
                "vulnerability_class"
            ),
            "file": finding.get("file"),
            "start_line": finding.get(
                "start_line"
            ),
            "end_line": finding.get(
                "end_line"
            ),
            "scope": get_scope_signature(
                source_file=source_file,
                finding=finding,
            ),
            "scanner_finding_count": finding.get(
                "scanner_finding_count",
                0,
            ),
        }

        result.setdefault(
            semantic_key,
            [],
        ).append(record)

    return result


def compare_findings(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    baseline_root: Path,
    candidate_root: Path,
    target_canonical_id: str,
) -> dict[str, Any]:
    """
    Compare baseline canonical findings to candidate
    canonical findings using semantic identities rather
    than line-based FixProof IDs.
    """

    baseline_findings = baseline.get(
        "findings",
        [],
    )

    candidate_findings = candidate.get(
        "findings",
        [],
    )

    target_finding = None

    for finding in baseline_findings:
        if (
            finding.get("canonical_id")
            == target_canonical_id
        ):
            target_finding = finding
            break

    if target_finding is None:
        raise ValueError(
            f"Baseline canonical finding not found: "
            f"{target_canonical_id}"
        )

    baseline_map = build_finding_map(
        findings=baseline_findings,
        source_root=baseline_root,
    )

    candidate_map = build_finding_map(
        findings=candidate_findings,
        source_root=candidate_root,
    )

    target_source = resolve_source_file(
        root=baseline_root,
        file_path=target_finding["file"],
    )

    target_key = make_semantic_key(
        finding=target_finding,
        source_file=target_source,
    )

    baseline_keys = set(
        baseline_map.keys()
    )

    candidate_keys = set(
        candidate_map.keys()
    )

    persistent_keys = (
        baseline_keys
        & candidate_keys
    )

    resolved_keys = (
        baseline_keys
        - candidate_keys
    )

    new_keys = (
        candidate_keys
        - baseline_keys
    )

    target_status = (
        "persistent"
        if target_key in candidate_keys
        else "resolved"
    )

    def flatten(
        finding_map: dict[
            str,
            list[dict[str, Any]]
        ],
        keys: set[str],
    ) -> list[dict[str, Any]]:

        records = []

        for key in sorted(keys):
            records.extend(
                finding_map.get(
                    key,
                    [],
                )
            )

        return records

    return {
        "target": {
            "canonical_id": (
                target_canonical_id
            ),
            "semantic_key": target_key,
            "status": target_status,
            "baseline": (
                baseline_map.get(
                    target_key,
                    [],
                )
            ),
            "candidate_matches": (
                candidate_map.get(
                    target_key,
                    [],
                )
            ),
        },

        "summary": {
            "baseline_canonical_findings": len(
                baseline_findings
            ),
            "candidate_canonical_findings": len(
                candidate_findings
            ),
            "persistent": len(
                persistent_keys
            ),
            "resolved": len(
                resolved_keys
            ),
            "new": len(
                new_keys
            ),
        },

        "persistent_findings": flatten(
            baseline_map,
            persistent_keys,
        ),

        "resolved_findings": flatten(
            baseline_map,
            resolved_keys,
        ),

        "new_findings": flatten(
            candidate_map,
            new_keys,
        ),
    }


def determine_stage_status(
    syntax_result: dict[str, Any],
    comparison: dict[str, Any],
) -> str:
    """
    This is NOT the final remediation decision.

    Passing this stage only means the candidate is ready
    for targeted security and functional testing.
    """

    if syntax_result["status"] == "fail":
        return "failed_syntax_validation"

    if syntax_result["status"] == "not_implemented":
        return "syntax_validation_not_implemented"

    target_status = comparison[
        "target"
    ]["status"]

    if target_status == "persistent":
        return "failed_target_sast_validation"

    new_findings = comparison[
        "summary"
    ]["new"]

    if new_findings > 0:
        return "failed_new_finding_validation"

    return (
        "ready_for_security_and_functional_tests"
    )


def run_validation(
    project_root: Path,
    baseline_correlated_file: Path,
    workspace_dir: Path,
    canonical_id: str,
    output_file: Path,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:

    print("=" * 60)
    print("FixProof Preliminary Validation")
    print("=" * 60)

    print(
        f"Canonical finding: {canonical_id}"
    )

    print(
        f"Workspace: {workspace_dir}"
    )

    print()

    # -------------------------------------------------
    # Load workspace metadata
    # -------------------------------------------------

    workspace_metadata_file = (
        workspace_dir
        / "workspace.json"
    )

    if not workspace_metadata_file.exists():
        raise FileNotFoundError(
            f"Workspace metadata not found: "
            f"{workspace_metadata_file}"
        )

    workspace_metadata = load_json(
        workspace_metadata_file
    )

    patch_workspace = workspace_metadata[
        "patch_workspace"
    ]

    workspace_source = Path(
        patch_workspace[
            "workspace_source"
        ]
    )

    if not workspace_source.exists():
        raise FileNotFoundError(
            f"Candidate source does not exist: "
            f"{workspace_source}"
        )

    workspace_app = workspace_source.parent

    # -------------------------------------------------
    # Stage 1: Syntax validation
    # -------------------------------------------------

    print("[1/3] Running syntax validation...")

    syntax_result = run_syntax_check(
        workspace_source
    )

    print(
        f"Syntax status: "
        f"{syntax_result['status']}"
    )

    # Stop security scanning only if syntax failed.
    if syntax_result["status"] == "fail":
        comparison = {
            "target": {
                "canonical_id": canonical_id,
                "status": "not_evaluated",
            },
            "summary": {
                "baseline_canonical_findings": 0,
                "candidate_canonical_findings": 0,
                "persistent": 0,
                "resolved": 0,
                "new": 0,
            },
            "persistent_findings": [],
            "resolved_findings": [],
            "new_findings": [],
        }

        stage_status = (
            "failed_syntax_validation"
        )

        result = {
            "schema_version": "0.1",
            "project": "FixProof",
            "validation": {
                "canonical_id": canonical_id,
                "stage": (
                    "preliminary_validation"
                ),
                "status": stage_status,
                "syntax": syntax_result,
                "sast": {
                    "status": "not_run"
                },
                "comparison": comparison,
            },
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

    print()

    # -------------------------------------------------
    # Candidate validation artifacts
    # -------------------------------------------------

    validation_workspace = (
        artifact_dir
        if artifact_dir is not None
        else workspace_dir / "validation"
    )

    validation_workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidate_raw = (
        validation_workspace
        / "candidate-semgrep-raw.json"
    )

    candidate_normalized = (
        validation_workspace
        / "candidate-normalized.json"
    )

    candidate_correlated = (
        validation_workspace
        / "candidate-correlated.json"
    )

    # -------------------------------------------------
    # Stage 2: SAST rescan candidate
    # -------------------------------------------------

    print("[2/3] Rescanning candidate with Semgrep...")

    run_semgrep(
        target=workspace_source,
        output=candidate_raw,
        project_rule_dir=project_root / "rules",
    )

    normalized = parse_semgrep(
        input_file=candidate_raw,
        output_file=candidate_normalized,
        source_root=project_root,
    )

    if not normalized[
        "scan"
    ]["files_scanned"]:
        raise RuntimeError(
            "Semgrep candidate scan did not report "
            "any scanned files."
        )

    candidate_correlated_data = (
        correlate_findings(
            input_file=candidate_normalized,
            output_file=candidate_correlated,
        )
    )

    candidate_scanner_count = (
        normalized[
            "scan"
        ]["finding_count"]
    )

    candidate_canonical_count = (
        candidate_correlated_data[
            "correlation"
        ]["canonical_finding_count"]
    )

    print(
        f"Candidate scanner findings: "
        f"{candidate_scanner_count}"
    )

    print(
        f"Candidate canonical findings: "
        f"{candidate_canonical_count}"
    )

    print()

    # -------------------------------------------------
    # Stage 3: Compare baseline vs candidate
    # -------------------------------------------------

    print(
        "[3/3] Comparing baseline and candidate..."
    )

    baseline = load_json(
        baseline_correlated_file
    )

    comparison = compare_findings(
        baseline=baseline,
        candidate=candidate_correlated_data,
        baseline_root=project_root,
        candidate_root=workspace_app,
        target_canonical_id=canonical_id,
    )

    target_status = comparison[
        "target"
    ]["status"]

    print(
        f"Target finding: {target_status}"
    )

    print(
        "Persistent findings: "
        f"{comparison['summary']['persistent']}"
    )

    print(
        "Resolved findings: "
        f"{comparison['summary']['resolved']}"
    )

    print(
        "New findings: "
        f"{comparison['summary']['new']}"
    )

    # -------------------------------------------------
    # Preliminary decision
    # -------------------------------------------------

    stage_status = determine_stage_status(
        syntax_result=syntax_result,
        comparison=comparison,
    )

    result = {
        "schema_version": "0.1",
        "project": "FixProof",

        "validation": {
            "canonical_id": canonical_id,

            "stage": (
                "preliminary_validation"
            ),

            "status": stage_status,

            "syntax": syntax_result,

            "sast": {
                "status": "completed",

                "candidate_scanner_findings": (
                    candidate_scanner_count
                ),

                "candidate_canonical_findings": (
                    candidate_canonical_count
                ),

                "raw_results": str(
                    candidate_raw
                ),

                "normalized_results": str(
                    candidate_normalized
                ),

                "correlated_results": str(
                    candidate_correlated
                ),
            },

            "comparison": comparison,

            "final_security_validation": (
                "not_run"
            ),

            "functional_validation": (
                "not_run"
            ),
        },
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

    print()
    print("=" * 60)
    print("FixProof Preliminary Validation Complete")
    print("=" * 60)

    print(
        f"Syntax: "
        f"{syntax_result['status']}"
    )

    print(
        f"Target SAST status: "
        f"{target_status}"
    )

    print(
        f"New findings: "
        f"{comparison['summary']['new']}"
    )

    print(
        f"Preliminary status: "
        f"{stage_status}"
    )

    print()
    print(
        f"Validation report: {output_file}"
    )

    if stage_status == (
        "ready_for_security_and_functional_tests"
    ):
        print()
        print(
            "Candidate is NOT approved yet."
        )
        print(
            "Next required stages: targeted security "
            "testing and functional regression testing."
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run FixProof preliminary validation "
            "for an isolated AI-generated patch."
        )
    )

    parser.add_argument(
        "--baseline",
        required=True,
        type=Path,
        help=(
            "Baseline correlated FixProof findings."
        ),
    )

    parser.add_argument(
        "--workspace",
        required=True,
        type=Path,
        help=(
            "Candidate FixProof workspace directory."
        ),
    )

    parser.add_argument(
        "--canonical-id",
        required=True,
        help=(
            "Canonical finding being remediated."
        ),
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help=(
            "Validation summary JSON output."
        ),
    )

    parser.add_argument(
        "--project-root",
        default=Path("."),
        type=Path,
    )

    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help=(
            "Directory for raw, normalized, and correlated candidate-SAST "
            "artifacts. Defaults to <workspace>/validation."
        ),
    )

    args = parser.parse_args()

    run_validation(
        project_root=(
            args.project_root.resolve()
        ),
        baseline_correlated_file=(
            args.baseline.resolve()
        ),
        workspace_dir=(
            args.workspace.resolve()
        ),
        canonical_id=args.canonical_id,
        output_file=args.output.resolve(),
        artifact_dir=(
            args.artifact_dir.resolve()
            if args.artifact_dir is not None
            else None
        ),
    )


if __name__ == "__main__":
    main()
