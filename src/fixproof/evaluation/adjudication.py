from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ADJUDICATION_SCHEMA_VERSION = "0.1"

ALLOWED_VERDICTS = (
    "ACCEPT_CANDIDATE",
    "REJECT_CANDIDATE",
    "REQUEST_ADDITIONAL_TESTING",
)

REQUIRED_REVIEW_CHECKS = (
    "candidate_patch_reviewed",
    "sast_finding_and_rule_provenance_reviewed",
    "targeted_security_evidence_reviewed",
    "functional_evidence_reviewed",
)

BOUND_ARTIFACTS = (
    "baseline_correlated",
    "remediation",
    "preliminary",
    "security",
    "functional",
    "decision",
    "workspace",
)


class AdjudicationDataError(ValueError):
    """Raised when an adjudication artifact is invalid or stale."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdjudicationDataError(f"Expected an object at {label}.")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdjudicationDataError(f"Expected a non-empty string at {label}.")
    return value.strip()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AdjudicationDataError(
            f"Invalid JSON in adjudication artifact '{path}': {error}"
        ) from error
    return _mapping(value, str(path))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_normalized_text(path: Path) -> str:
    """Match patch_workspace.py hashes across LF/CRLF platforms."""
    normalized_text = path.read_text(encoding="utf-8")
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def _relative_path(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as error:
        raise AdjudicationDataError(
            f"Adjudication artifact must remain under '{project_root}': '{path}'."
        ) from error


def _artifact_record(project_root: Path, path: Path) -> dict[str, str]:
    return {
        "path": _relative_path(project_root, path),
        "sha256": _sha256(path),
    }


def _resolve_project_file(
    project_root: Path,
    configured_path: Any,
    label: str,
) -> Path:
    configured = _string(configured_path, label)
    raw_path = Path(configured)
    normalized = configured.replace("\\", "/")
    windows_absolute = (
        len(normalized) >= 3
        and normalized[0].isalpha()
        and normalized[1:3] == ":/"
    )

    if not raw_path.is_absolute() and not windows_absolute:
        resolved = (project_root / raw_path).resolve()
        _relative_path(project_root, resolved)
        if not resolved.is_file():
            raise AdjudicationDataError(
                f"Bound file does not exist: '{resolved}'."
            )
        return resolved

    # Historical workspace records contain development-machine absolute paths.
    # Never follow one outside the active project root: a clean-extraction check
    # on the same machine could otherwise validate against the original checkout.
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
        try:
            _relative_path(project_root, resolved)
        except AdjudicationDataError:
            pass
        else:
            if resolved.is_file():
                return resolved

    repository_roots = {
        "data",
        "docs",
        "rules",
        "sample_apps",
        "src",
        "tests",
        "ui",
        "workspaces",
    }
    path_parts = [part for part in normalized.split("/") if part]
    for index, part in enumerate(path_parts):
        if part.lower() not in repository_roots:
            continue
        portable = (project_root.joinpath(*path_parts[index:])).resolve()
        _relative_path(project_root, portable)
        if portable.is_file():
            return portable

    raise AdjudicationDataError(
        f"Bound file does not exist under the active project root: '{configured}'."
    )


def _workspace_hashes(project_root: Path, row: dict[str, Any]) -> dict[str, str]:
    workspace_record = row["artifacts"]["workspace"]
    workspace_path = project_root / workspace_record["path"]
    workspace_payload = _load_json(workspace_path)
    workspace = _mapping(
        workspace_payload.get("patch_workspace"),
        f"{workspace_path}.patch_workspace",
    )
    hashes = _mapping(
        workspace.get("hashes"),
        f"{workspace_path}.patch_workspace.hashes",
    )
    selected_hashes = {
        "candidate_source_sha256": _string(
            hashes.get("candidate_source_sha256"),
            f"{workspace_path}.hashes.candidate_source_sha256",
        ),
        "patch_sha256": _string(
            hashes.get("patch_sha256"),
            f"{workspace_path}.hashes.patch_sha256",
        ),
    }
    content_bindings = (
        (
            "workspace_source",
            "candidate_source_sha256",
        ),
        (
            "patch_file",
            "patch_sha256",
        ),
    )
    for path_field, hash_field in content_bindings:
        content_path = _resolve_project_file(
            project_root,
            workspace.get(path_field),
            f"{workspace_path}.patch_workspace.{path_field}",
        )
        if _sha256_normalized_text(content_path) != selected_hashes[hash_field]:
            raise AdjudicationDataError(
                f"Workspace {path_field} content does not match {hash_field} "
                f"in '{workspace_path}'."
            )
    return selected_hashes


def build_pending_packet(
    project_root: Path,
    row: dict[str, Any],
) -> dict[str, Any]:
    if row["decision"] != "NEEDS_HUMAN_ADJUDICATION":
        raise AdjudicationDataError(
            f"{row['case']} attempt {row['attempt']} does not require "
            "human adjudication."
        )

    bound_artifacts = {
        name: row["artifacts"][name] for name in BOUND_ARTIFACTS
    }
    workspace_hashes = _workspace_hashes(project_root, row)
    evidence = row["evidence"]

    return {
        "schema_version": ADJUDICATION_SCHEMA_VERSION,
        "project": "FixProof",
        "artifact_type": "adjudication_packet",
        "adjudication_packet": {
            "case_id": row["case_id"],
            "case": row["case"],
            "canonical_id": row["canonical_id"],
            "attempt": row["attempt"],
            "trigger": {
                "classification": row["classification"],
                "automated_disposition": row["decision"],
                "reason_codes": row["reason_codes"],
            },
            "evidence_summary": {
                "syntax": evidence["syntax"],
                "target_sast": evidence["target_sast"],
                "new_sast_findings": evidence["new_sast_findings"],
                "security_validation": evidence["security"]["status"],
                "security_tests": {
                    "passed": evidence["security"]["passed"],
                    "total": evidence["security"]["total"],
                },
                "functional_validation": evidence["functional"]["status"],
                "functional_tests": {
                    "passed": evidence["functional"]["passed"],
                    "total": evidence["functional"]["total"],
                },
            },
            "evidence_binding": {
                "workspace_content_hash_mode": "utf8_normalized_text_sha256",
                **workspace_hashes,
                "artifacts": bound_artifacts,
            },
            "review_protocol": {
                "allowed_verdicts": list(ALLOWED_VERDICTS),
                "required_checks": list(REQUIRED_REVIEW_CHECKS),
                "instructions": (
                    "A human reviewer must inspect the candidate and all bound "
                    "evidence. The automated NEEDS_HUMAN_ADJUDICATION decision "
                    "must remain unchanged; record the human conclusion in a "
                    "separate adjudication_result artifact."
                ),
            },
        },
    }


def validate_packet_bindings(
    project_root: Path,
    packet_path: Path,
    packet_payload: dict[str, Any],
) -> None:
    if packet_payload.get("schema_version") != ADJUDICATION_SCHEMA_VERSION:
        raise AdjudicationDataError(
            f"Unsupported adjudication packet schema in '{packet_path}'."
        )
    if packet_payload.get("artifact_type") != "adjudication_packet":
        raise AdjudicationDataError(
            f"Expected an adjudication_packet in '{packet_path}'."
        )
    packet = _mapping(
        packet_payload.get("adjudication_packet"),
        f"{packet_path}.adjudication_packet",
    )
    binding = _mapping(
        packet.get("evidence_binding"),
        f"{packet_path}.adjudication_packet.evidence_binding",
    )
    if binding.get("workspace_content_hash_mode") != (
        "utf8_normalized_text_sha256"
    ):
        raise AdjudicationDataError(
            f"Adjudication packet '{packet_path}' has an unsupported "
            "workspace content hash mode."
        )
    artifacts = _mapping(
        binding.get("artifacts"),
        f"{packet_path}.adjudication_packet.evidence_binding.artifacts",
    )
    if set(artifacts) != set(BOUND_ARTIFACTS):
        raise AdjudicationDataError(
            f"Adjudication packet '{packet_path}' does not bind the required "
            "artifact set."
        )

    resolved_artifacts = {}
    for name in BOUND_ARTIFACTS:
        record = _mapping(artifacts[name], f"{packet_path}.artifacts.{name}")
        artifact_path = _resolve_project_file(
            project_root,
            record.get("path"),
            f"{packet_path}.artifacts.{name}.path",
        )
        expected_digest = _string(
            record.get("sha256"), f"{packet_path}.artifacts.{name}.sha256"
        )
        if _sha256(artifact_path) != expected_digest:
            raise AdjudicationDataError(
                f"Bound artifact '{artifact_path}' changed after packet "
                "creation. Regenerate the packet before review."
            )
        resolved_artifacts[name] = artifact_path

    workspace_payload = _load_json(resolved_artifacts["workspace"])
    workspace = _mapping(
        workspace_payload.get("patch_workspace"),
        f"{resolved_artifacts['workspace']}.patch_workspace",
    )
    hashes = _mapping(
        workspace.get("hashes"),
        f"{resolved_artifacts['workspace']}.patch_workspace.hashes",
    )
    for name in ("candidate_source_sha256", "patch_sha256"):
        if binding.get(name) != hashes.get(name):
            raise AdjudicationDataError(
                f"Candidate binding '{name}' in '{packet_path}' is stale."
            )
    content_bindings = (
        ("workspace_source", "candidate_source_sha256"),
        ("patch_file", "patch_sha256"),
    )
    for path_field, hash_field in content_bindings:
        content_path = _resolve_project_file(
            project_root,
            workspace.get(path_field),
            f"{resolved_artifacts['workspace']}.patch_workspace.{path_field}",
        )
        if _sha256_normalized_text(content_path) != binding.get(hash_field):
            raise AdjudicationDataError(
                f"Bound {path_field} content changed after packet creation."
            )

    protocol = _mapping(
        packet.get("review_protocol"),
        f"{packet_path}.adjudication_packet.review_protocol",
    )
    if protocol.get("allowed_verdicts") != list(ALLOWED_VERDICTS):
        raise AdjudicationDataError(
            f"Adjudication packet '{packet_path}' has an invalid verdict set."
        )
    if protocol.get("required_checks") != list(REQUIRED_REVIEW_CHECKS):
        raise AdjudicationDataError(
            f"Adjudication packet '{packet_path}' has an invalid checklist."
        )


def validate_packet(
    project_root: Path,
    row: dict[str, Any],
    packet_path: Path,
    packet_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = packet_payload or _load_json(packet_path)
    if payload.get("schema_version") != ADJUDICATION_SCHEMA_VERSION:
        raise AdjudicationDataError(
            f"Unsupported adjudication packet schema in '{packet_path}'."
        )
    if payload.get("artifact_type") != "adjudication_packet":
        raise AdjudicationDataError(
            f"Expected an adjudication_packet in '{packet_path}'."
        )

    validate_packet_bindings(project_root, packet_path, payload)

    expected = build_pending_packet(project_root, row)
    if payload != expected:
        raise AdjudicationDataError(
            f"Adjudication packet '{packet_path}' is stale or does not match "
            "the selected attempt evidence. Regenerate the packet."
        )
    return payload


def _validate_reviewed_at(value: Any, label: str) -> str:
    reviewed_at = _string(value, label)
    normalized = reviewed_at.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise AdjudicationDataError(
            f"Expected an ISO-8601 timestamp at {label}."
        ) from error
    if parsed.tzinfo is None:
        raise AdjudicationDataError(
            f"Timestamp at {label} must include a UTC offset."
        )
    return reviewed_at


def build_completed_result(
    project_root: Path,
    packet_path: Path,
    packet_payload: dict[str, Any],
    reviewer: str,
    verdict: str,
    rationale: str,
    reviewed_at: str,
    confirmed_checks: dict[str, bool],
) -> dict[str, Any]:
    packet = _mapping(
        packet_payload.get("adjudication_packet"),
        f"{packet_path}.adjudication_packet",
    )
    reviewer = _string(reviewer, "reviewer")
    rationale = _string(rationale, "rationale")
    if len(rationale) < 20:
        raise AdjudicationDataError(
            "Adjudication rationale must contain at least 20 characters."
        )
    if verdict not in ALLOWED_VERDICTS:
        raise AdjudicationDataError(
            f"Unsupported adjudication verdict '{verdict}'."
        )
    reviewed_at = _validate_reviewed_at(reviewed_at, "reviewed_at")

    checks = {
        name: confirmed_checks.get(name) is True for name in REQUIRED_REVIEW_CHECKS
    }
    missing_checks = [name for name, complete in checks.items() if not complete]
    if missing_checks:
        raise AdjudicationDataError(
            f"Human review checks are incomplete: {missing_checks}."
        )

    return {
        "schema_version": ADJUDICATION_SCHEMA_VERSION,
        "project": "FixProof",
        "artifact_type": "adjudication_result",
        "adjudication_result": {
            "case_id": packet["case_id"],
            "case": packet["case"],
            "canonical_id": packet["canonical_id"],
            "attempt": packet["attempt"],
            "status": "completed",
            "verdict": verdict,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "rationale": rationale,
            "completed_checks": checks,
            "packet_binding": _artifact_record(project_root, packet_path),
            "automated_decision_unchanged": True,
        },
    }


def validate_result(
    project_root: Path,
    row: dict[str, Any],
    packet_path: Path,
    packet_payload: dict[str, Any],
    result_path: Path,
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = result_payload or _load_json(result_path)
    if payload.get("schema_version") != ADJUDICATION_SCHEMA_VERSION:
        raise AdjudicationDataError(
            f"Unsupported adjudication result schema in '{result_path}'."
        )
    if payload.get("artifact_type") != "adjudication_result":
        raise AdjudicationDataError(
            f"Expected an adjudication_result in '{result_path}'."
        )
    result = _mapping(
        payload.get("adjudication_result"),
        f"{result_path}.adjudication_result",
    )

    identity = {
        "case_id": row["case_id"],
        "case": row["case"],
        "canonical_id": row["canonical_id"],
        "attempt": row["attempt"],
    }
    mismatches = {
        name: {"result": result.get(name), "selected_attempt": value}
        for name, value in identity.items()
        if result.get(name) != value
    }
    if mismatches:
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' identifies the wrong "
            f"attempt: {mismatches}."
        )
    if result.get("status") != "completed":
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' is not completed."
        )
    if result.get("verdict") not in ALLOWED_VERDICTS:
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' has an invalid verdict."
        )
    _string(result.get("reviewer"), f"{result_path}.reviewer")
    rationale = _string(result.get("rationale"), f"{result_path}.rationale")
    if len(rationale) < 20:
        raise AdjudicationDataError(
            f"Adjudication rationale in '{result_path}' is too short."
        )
    _validate_reviewed_at(result.get("reviewed_at"), f"{result_path}.reviewed_at")

    checks = _mapping(
        result.get("completed_checks"), f"{result_path}.completed_checks"
    )
    incomplete = [
        name for name in REQUIRED_REVIEW_CHECKS if checks.get(name) is not True
    ]
    if incomplete:
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' has incomplete checks: "
            f"{incomplete}."
        )
    expected_binding = _artifact_record(project_root, packet_path)
    if result.get("packet_binding") != expected_binding:
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' is not bound to the selected "
            "packet."
        )
    if result.get("automated_decision_unchanged") is not True:
        raise AdjudicationDataError(
            f"Adjudication result '{result_path}' must preserve the automated "
            "decision."
        )

    validate_packet(project_root, row, packet_path, packet_payload)
    return payload


def evaluate_adjudication(
    project_root: Path,
    row: dict[str, Any],
    packet_path: Path | None,
    result_path: Path | None,
) -> dict[str, Any]:
    required = row["decision"] == "NEEDS_HUMAN_ADJUDICATION"
    if not required:
        if packet_path is not None or result_path is not None:
            raise AdjudicationDataError(
                f"Adjudication artifacts were selected for {row['case']} "
                f"attempt {row['attempt']}, but its automated decision is "
                f"{row['decision']}."
            )
        return {
            "required": False,
            "status": "not_required",
            "verdict": None,
        }

    if packet_path is None:
        if result_path is not None:
            raise AdjudicationDataError(
                "An adjudication result cannot be selected without its packet."
            )
        return {
            "required": True,
            "status": "missing_packet",
            "verdict": None,
        }

    packet_payload = validate_packet(project_root, row, packet_path)
    if result_path is None:
        return {
            "required": True,
            "status": "pending",
            "verdict": None,
            "packet": row["artifacts"]["adjudication_packet"],
        }

    result_payload = validate_result(
        project_root,
        row,
        packet_path,
        packet_payload,
        result_path,
    )
    result = result_payload["adjudication_result"]
    return {
        "required": True,
        "status": "completed",
        "verdict": result["verdict"],
        "reviewer": result["reviewer"],
        "reviewed_at": result["reviewed_at"],
        "rationale": result["rationale"],
        "packet": row["artifacts"]["adjudication_packet"],
        "result": row["artifacts"]["adjudication_result"],
    }


def initialize_pending_packets(
    project_root: Path,
    manifest_path: Path,
    output_directory: Path,
) -> list[Path]:
    # Local import avoids a module cycle: report_builder uses the validation
    # helpers above when packets are selected by a manifest.
    from fixproof.evaluation.report_builder import build_report_data

    project_root = project_root.resolve()
    output_directory = output_directory.resolve()
    _relative_path(project_root, output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    report = build_report_data(project_root, manifest_path.resolve())
    outputs = []
    for row in report["experiment_matrix"]:
        if row["decision"] != "NEEDS_HUMAN_ADJUDICATION":
            continue
        output = output_directory / (
            f"{row['canonical_id']}-attempt-{row['attempt']:02d}-packet.json"
        )
        packet = build_pending_packet(project_root, row)
        serialized = json.dumps(packet, indent=2) + "\n"
        if output.exists():
            existing = _load_json(output)
            if existing != packet:
                raise AdjudicationDataError(
                    f"Refusing to overwrite stale adjudication packet "
                    f"'{output}'. Remove it only after preserving its audit "
                    "history."
                )
        else:
            output.write_text(serialized, encoding="utf-8")
        outputs.append(output)
    return outputs


def record_completed_result(
    project_root: Path,
    packet_path: Path,
    output_path: Path,
    reviewer: str,
    verdict: str,
    rationale: str,
    reviewed_at: str | None,
    confirm_all_required_checks: bool,
) -> Path:
    project_root = project_root.resolve()
    packet_path = packet_path.resolve()
    output_path = output_path.resolve()
    _relative_path(project_root, packet_path)
    _relative_path(project_root, output_path)
    if output_path == packet_path:
        raise AdjudicationDataError(
            "The result must be a separate artifact; it cannot overwrite the "
            "adjudication packet."
        )
    if output_path.exists():
        raise AdjudicationDataError(
            f"Refusing to overwrite existing adjudication result '{output_path}'."
        )

    packet_payload = _load_json(packet_path)
    validate_packet_bindings(project_root, packet_path, packet_payload)
    checks = {
        name: confirm_all_required_checks for name in REQUIRED_REVIEW_CHECKS
    }
    timestamp = reviewed_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    result = build_completed_result(
        project_root=project_root,
        packet_path=packet_path,
        packet_payload=packet_payload,
        reviewer=reviewer,
        verdict=verdict,
        rationale=rationale,
        reviewed_at=timestamp,
        confirmed_checks=checks,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create and complete evidence-bound FixProof adjudications."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser(
        "init", description="Create pending packets for selected disagreements."
    )
    initialize.add_argument("--project-root", type=Path, default=Path("."))
    initialize.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/evaluation/experiment-manifest.json"),
    )
    initialize.add_argument(
        "--output-dir", type=Path, default=Path("data/adjudications")
    )

    record = subparsers.add_parser(
        "record", description="Record a separate completed human result."
    )
    record.add_argument("--project-root", type=Path, default=Path("."))
    record.add_argument("--packet", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True)
    record.add_argument("--reviewer", required=True)
    record.add_argument("--verdict", choices=ALLOWED_VERDICTS, required=True)
    record.add_argument("--rationale", required=True)
    record.add_argument("--reviewed-at")
    record.add_argument("--confirm-all-required-checks", action="store_true")

    args = parser.parse_args()
    project_root = args.project_root.resolve()

    def from_root(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (project_root / path).resolve()

    if args.command == "init":
        outputs = initialize_pending_packets(
            project_root,
            from_root(args.manifest),
            from_root(args.output_dir),
        )
        print("=" * 60)
        print("FixProof Human Adjudication Packets")
        print("=" * 60)
        for output in outputs:
            print(_relative_path(project_root, output))
        print(f"Pending packets: {len(outputs)}")
        return

    output = record_completed_result(
        project_root=project_root,
        packet_path=from_root(args.packet),
        output_path=from_root(args.output),
        reviewer=args.reviewer,
        verdict=args.verdict,
        rationale=args.rationale,
        reviewed_at=args.reviewed_at,
        confirm_all_required_checks=args.confirm_all_required_checks,
    )
    print(f"Adjudication result: {_relative_path(project_root, output)}")


if __name__ == "__main__":
    main()
