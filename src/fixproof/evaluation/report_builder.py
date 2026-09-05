from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fixproof.evaluation.adjudication import (
    ALLOWED_VERDICTS,
    REQUIRED_REVIEW_CHECKS,
    AdjudicationDataError,
    evaluate_adjudication,
    validate_packet_bindings,
)


REPORT_SCHEMA_VERSION = "0.1"

REQUIRED_ARTIFACTS = (
    "baseline_correlated",
    "remediation",
    "preliminary",
    "security",
    "functional",
    "decision",
    "workspace",
)

OPTIONAL_ARTIFACTS = (
    "adjudication_packet",
    "adjudication_result",
)

METRIC_DEFINITIONS = {
    "sast_remediation_success_rate": (
        "Attempts whose target SAST finding was resolved, divided by all "
        "attempts."
    ),
    "targeted_security_validation_pass_rate": (
        "Attempts whose targeted runtime security validation passed, divided "
        "by all attempts."
    ),
    "functional_preservation_rate": (
        "Attempts whose functional/regression validation passed, divided by "
        "all attempts."
    ),
    "security_regression_new_finding_rate": (
        "Attempts that introduced one or more new SAST findings, divided by "
        "all attempts."
    ),
    "sast_false_success_count": (
        "Count of attempts where the target SAST finding resolved but "
        "security validation failed or was inconclusive, functional validation "
        "failed, or new SAST findings appeared."
    ),
    "sast_runtime_disagreement_count": (
        "Count of attempts where the target SAST finding remained persistent "
        "while targeted security and functional validation passed with no new "
        "SAST findings."
    ),
    "retry_improvement_rate": (
        "Retries that were no worse on syntax, target SAST, security, "
        "functional, and new-finding evidence and improved at least one of "
        "those dimensions, divided by all retries."
    ),
    "human_adjudication_rate": (
        "Attempts dispositioned NEEDS_HUMAN_ADJUDICATION, divided by all "
        "attempts."
    ),
    "human_adjudication_completion_rate": (
        "Completed evidence-bound human adjudications, divided by attempts "
        "that require human adjudication."
    ),
}


class ReportDataError(ValueError):
    """Raised when selected experiment artifacts are missing or inconsistent."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReportDataError(f"Invalid JSON in '{path}': {error}") from error

    if not isinstance(value, dict):
        raise ReportDataError(f"Expected a JSON object in '{path}'.")

    return value


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReportDataError(f"Expected an object at {label}.")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReportDataError(f"Expected a non-empty string at {label}.")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportDataError(f"Expected an integer at {label}.")
    return value


def _resolve_artifact(project_root: Path, configured_path: Any) -> Path:
    raw_path = Path(_string(configured_path, "manifest artifact path"))
    candidate = raw_path if raw_path.is_absolute() else project_root / raw_path
    resolved = candidate.resolve()

    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise ReportDataError(
            f"Artifact path escapes the project root: '{configured_path}'."
        ) from error

    if not resolved.is_file():
        raise ReportDataError(f"Artifact file does not exist: '{resolved}'.")

    return resolved


def _relative_path(project_root: Path, path: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_record(project_root: Path, path: Path) -> dict[str, str]:
    return {
        "path": _relative_path(project_root, path),
        "sha256": _sha256(path),
    }


def _historical_adjudication(
    project_root: Path,
    result_path: Path,
    case_id: str,
    canonical_id: str,
    attempt: int,
) -> tuple[dict[str, Any], dict[str, str]]:
    payload = load_json(result_path)
    if payload.get("artifact_type") != "adjudication_result":
        raise ReportDataError(
            f"Historical artifact '{result_path}' is not an adjudication result."
        )
    result = _mapping(
        payload.get("adjudication_result"),
        f"{result_path}.adjudication_result",
    )
    expected_identity = {
        "case_id": case_id,
        "canonical_id": canonical_id,
        "attempt": attempt,
    }
    mismatches = {
        name: {"result": result.get(name), "expected": value}
        for name, value in expected_identity.items()
        if result.get(name) != value
    }
    if mismatches:
        raise ReportDataError(
            f"Historical adjudication '{result_path}' identifies the wrong "
            f"attempt: {mismatches}."
        )
    if result.get("status") != "completed":
        raise ReportDataError(
            f"Historical adjudication '{result_path}' is not completed."
        )
    verdict = result.get("verdict")
    if verdict not in ALLOWED_VERDICTS:
        raise ReportDataError(
            f"Historical adjudication '{result_path}' has an invalid verdict."
        )
    reviewer = _string(result.get("reviewer"), f"{result_path}.reviewer")
    reviewed_at = _string(
        result.get("reviewed_at"), f"{result_path}.reviewed_at"
    )
    _string(result.get("rationale"), f"{result_path}.rationale")
    checks = _mapping(
        result.get("completed_checks"), f"{result_path}.completed_checks"
    )
    if any(checks.get(name) is not True for name in REQUIRED_REVIEW_CHECKS):
        raise ReportDataError(
            f"Historical adjudication '{result_path}' has incomplete checks."
        )
    if result.get("automated_decision_unchanged") is not True:
        raise ReportDataError(
            f"Historical adjudication '{result_path}' changed the automated "
            "decision."
        )

    packet_binding = _mapping(
        result.get("packet_binding"), f"{result_path}.packet_binding"
    )
    packet_path = _resolve_artifact(project_root, packet_binding.get("path"))
    if packet_binding.get("sha256") != _sha256(packet_path):
        raise ReportDataError(
            f"Historical adjudication '{result_path}' has a stale packet binding."
        )
    packet_payload = load_json(packet_path)
    try:
        validate_packet_bindings(project_root, packet_path, packet_payload)
    except AdjudicationDataError as error:
        raise ReportDataError(str(error)) from error

    return (
        {
            "status": "completed",
            "verdict": verdict,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
        },
        _artifact_record(project_root, packet_path),
    )


def _find_baseline_finding(
    baseline: dict[str, Any],
    canonical_id: str,
    source: Path,
) -> dict[str, Any]:
    findings = baseline.get("findings")
    if not isinstance(findings, list):
        raise ReportDataError(f"Expected a findings list in '{source}'.")

    matches = [
        finding
        for finding in findings
        if isinstance(finding, dict)
        and finding.get("canonical_id") == canonical_id
    ]
    if len(matches) != 1:
        raise ReportDataError(
            f"Expected exactly one baseline finding for {canonical_id} in "
            f"'{source}', found {len(matches)}."
        )
    return matches[0]


def _rule_provenance(finding: dict[str, Any]) -> tuple[list[str], bool]:
    origins = {
        origin
        for origin in finding.get("rule_origins", [])
        if isinstance(origin, str) and origin
    }

    evidence = finding.get("scanner_evidence", [])
    if isinstance(evidence, list):
        origins.update(
            item["rule_origin"]
            for item in evidence
            if isinstance(item, dict)
            and isinstance(item.get("rule_origin"), str)
            and item["rule_origin"]
        )

    if not origins:
        return ["unrecorded"], False
    return sorted(origins), True


def _test_counts(
    validation: dict[str, Any],
    source_label: str,
) -> dict[str, int]:
    tests = validation.get("tests")
    if not isinstance(tests, list):
        raise ReportDataError(f"Expected a tests list in {source_label}.")

    statuses = []
    for index, test in enumerate(tests):
        test_mapping = _mapping(test, f"{source_label}.tests[{index}]")
        evaluation = _mapping(
            test_mapping.get("evaluation"),
            f"{source_label}.tests[{index}].evaluation",
        )
        statuses.append(
            _string(
                evaluation.get("status"),
                f"{source_label}.tests[{index}].evaluation.status",
            )
        )

    return {
        "total": len(statuses),
        "passed": statuses.count("pass"),
        "failed": statuses.count("fail"),
        "inconclusive": statuses.count("inconclusive"),
    }


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    if denominator == 0:
        return {
            "numerator": numerator,
            "denominator": denominator,
            "rate": None,
            "percentage": None,
        }

    rate = numerator / denominator
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": round(rate, 6),
        "percentage": round(rate * 100, 2),
    }


def _validate_overall_test_status(
    status: str,
    counts: dict[str, int],
    source_label: str,
) -> None:
    if counts["total"] == 0:
        expected = "inconclusive"
    elif counts["failed"] > 0:
        expected = "fail"
    elif counts["inconclusive"] > 0:
        expected = "inconclusive"
    elif counts["passed"] == counts["total"]:
        expected = "pass"
    else:
        raise ReportDataError(
            f"Tests in {source_label} contain unsupported status values."
        )

    if status != expected:
        raise ReportDataError(
            f"Overall status '{status}' in {source_label} does not match the "
            f"recomputed test status '{expected}'."
        )


def _validate_decision_evidence(
    decision: dict[str, Any],
    actual: dict[str, Any],
    decision_path: Path,
) -> None:
    evidence = _mapping(
        decision.get("evidence"),
        f"{decision_path}.decision.evidence",
    )
    expected = {
        "syntax": actual["syntax"],
        "target_sast": actual["target_sast"],
        "new_sast_findings": actual["new_sast_findings"],
        "security_validation": actual["security"]["status"],
        "functional_validation": actual["functional"]["status"],
    }
    mismatches = {
        name: {"decision": evidence.get(name), "artifact": value}
        for name, value in expected.items()
        if evidence.get(name) != value
    }
    if mismatches:
        raise ReportDataError(
            f"Decision evidence in '{decision_path}' disagrees with its "
            f"selected validation artifacts: {mismatches}."
        )

    functional_tests = evidence.get("functional_tests")
    if functional_tests is not None:
        functional_tests = _mapping(
            functional_tests,
            f"{decision_path}.decision.evidence.functional_tests",
        )
        expected_functional_tests = {
            "passed": actual["functional"]["passed"],
            "failed": actual["functional"]["failed"],
        }
        if any(
            functional_tests.get(name) != value
            for name, value in expected_functional_tests.items()
        ):
            raise ReportDataError(
                f"Functional test counts in '{decision_path}' disagree with "
                "the selected functional-validation artifact."
            )

    labels = decision.get("evaluation_labels")
    if labels is None:
        return
    labels = _mapping(labels, f"{decision_path}.decision.evaluation_labels")
    expected_labels = {
        "sast_remediation_success": actual["sast_remediation_success"],
        "security_validation_pass": actual["security"]["status"] == "pass",
        "functional_preservation": actual["functional"]["status"] == "pass",
        "security_regression": actual["security_regression"],
        "false_success": actual["false_success"],
    }
    label_mismatches = {
        name: {"decision": labels.get(name), "recomputed": value}
        for name, value in expected_labels.items()
        if labels.get(name) != value
    }
    if label_mismatches:
        raise ReportDataError(
            f"Evaluation labels in '{decision_path}' are stale or "
            f"inconsistent: {label_mismatches}."
        )


def _build_attempt_row(
    project_root: Path,
    entry: dict[str, Any],
    entry_index: int,
    entry_collection: str = "attempts",
) -> dict[str, Any]:
    label = f"manifest.{entry_collection}[{entry_index}]"
    case_id = _string(entry.get("case_id"), f"{label}.case_id")
    case_name = _string(entry.get("case"), f"{label}.case")
    application = _string(entry.get("application"), f"{label}.application")
    cwe = _string(entry.get("cwe"), f"{label}.cwe")
    canonical_id = _string(
        entry.get("canonical_id"), f"{label}.canonical_id"
    )
    attempt = _integer(entry.get("attempt"), f"{label}.attempt")
    if attempt < 1:
        raise ReportDataError(f"{label}.attempt must be at least 1.")

    retry_of_attempt = entry.get("retry_of_attempt")
    if retry_of_attempt is not None:
        retry_of_attempt = _integer(
            retry_of_attempt, f"{label}.retry_of_attempt"
        )
        if retry_of_attempt < 1 or retry_of_attempt == attempt:
            raise ReportDataError(
                f"{label}.retry_of_attempt must identify a different positive "
                "attempt."
            )

    configured_artifacts = _mapping(
        entry.get("artifacts"), f"{label}.artifacts"
    )
    missing = [
        name for name in REQUIRED_ARTIFACTS if name not in configured_artifacts
    ]
    if missing:
        raise ReportDataError(f"{label} is missing artifacts: {missing}.")

    selected_artifacts = list(REQUIRED_ARTIFACTS) + [
        name for name in OPTIONAL_ARTIFACTS if name in configured_artifacts
    ]
    paths = {
        name: _resolve_artifact(project_root, configured_artifacts[name])
        for name in selected_artifacts
    }
    payloads = {name: load_json(path) for name, path in paths.items()}

    remediation = _mapping(
        payloads["remediation"].get("remediation"),
        f"{paths['remediation']}.remediation",
    )
    preliminary = _mapping(
        payloads["preliminary"].get("validation"),
        f"{paths['preliminary']}.validation",
    )
    security = _mapping(
        payloads["security"].get("security_validation"),
        f"{paths['security']}.security_validation",
    )
    functional = _mapping(
        payloads["functional"].get("functional_validation"),
        f"{paths['functional']}.functional_validation",
    )
    decision = _mapping(
        payloads["decision"].get("decision"),
        f"{paths['decision']}.decision",
    )
    workspace = _mapping(
        payloads["workspace"].get("patch_workspace"),
        f"{paths['workspace']}.patch_workspace",
    )

    canonical_sources = {
        "remediation": remediation.get("canonical_id"),
        "preliminary": preliminary.get("canonical_id"),
        "security": security.get("canonical_id"),
        "functional": functional.get("canonical_id"),
        "decision": decision.get("canonical_id"),
        "workspace": workspace.get("canonical_id"),
    }
    mismatched_ids = {
        name: value
        for name, value in canonical_sources.items()
        if value != canonical_id
    }
    if mismatched_ids:
        raise ReportDataError(
            f"Artifacts for {case_id} attempt {attempt} do not all match "
            f"canonical ID {canonical_id}: {mismatched_ids}."
        )

    workspace_attempt = workspace.get("attempt")
    if workspace_attempt is not None and workspace_attempt != attempt:
        raise ReportDataError(
            f"Workspace attempt {workspace_attempt} does not match manifest "
            f"attempt {attempt} for {case_id}."
        )

    baseline_finding = _find_baseline_finding(
        payloads["baseline_correlated"],
        canonical_id,
        paths["baseline_correlated"],
    )
    if baseline_finding.get("cwe") != cwe:
        raise ReportDataError(
            f"Manifest CWE {cwe} does not match baseline CWE "
            f"{baseline_finding.get('cwe')} for {canonical_id}."
        )

    comparison = _mapping(
        preliminary.get("comparison"),
        f"{paths['preliminary']}.validation.comparison",
    )
    target = _mapping(
        comparison.get("target"),
        f"{paths['preliminary']}.validation.comparison.target",
    )
    summary = _mapping(
        comparison.get("summary"),
        f"{paths['preliminary']}.validation.comparison.summary",
    )
    syntax = _mapping(
        preliminary.get("syntax"),
        f"{paths['preliminary']}.validation.syntax",
    )

    syntax_status = _string(
        syntax.get("status"), f"{paths['preliminary']}.validation.syntax.status"
    )
    target_sast = _string(
        target.get("status"),
        f"{paths['preliminary']}.validation.comparison.target.status",
    )
    new_findings = _integer(
        summary.get("new"),
        f"{paths['preliminary']}.validation.comparison.summary.new",
    )
    security_status = _string(
        security.get("status"), f"{paths['security']}.security_validation.status"
    )
    functional_status = _string(
        functional.get("status"),
        f"{paths['functional']}.functional_validation.status",
    )

    security_counts = _test_counts(
        security, f"{paths['security']}.security_validation"
    )
    declared_security_count = security.get("test_count")
    if (
        declared_security_count is not None
        and declared_security_count != security_counts["total"]
    ):
        raise ReportDataError(
            f"Security test count in '{paths['security']}' does not match its "
            "test list."
        )
    _validate_overall_test_status(
        security_status,
        security_counts,
        f"'{paths['security']}'",
    )

    functional_counts = _test_counts(
        functional, f"{paths['functional']}.functional_validation"
    )
    functional_summary = functional.get("summary")
    if isinstance(functional_summary, dict):
        declared_functional_counts = {
            "total": functional_summary.get("tests"),
            "passed": functional_summary.get("passed"),
            "failed": functional_summary.get("failed"),
        }
        actual_functional_counts = {
            name: functional_counts[name] for name in declared_functional_counts
        }
        if declared_functional_counts != actual_functional_counts:
            raise ReportDataError(
                f"Functional summary in '{paths['functional']}' does not "
                "match its test list."
            )
    _validate_overall_test_status(
        functional_status,
        functional_counts,
        f"'{paths['functional']}'",
    )

    sast_success = target_sast == "resolved"
    security_regression = new_findings > 0
    false_success = sast_success and (
        security_status != "pass"
        or functional_status != "pass"
        or security_regression
    )
    disagreement = (
        target_sast == "persistent"
        and security_status == "pass"
        and functional_status == "pass"
        and new_findings == 0
    )

    evidence = {
        "syntax": syntax_status,
        "target_sast": target_sast,
        "sast_remediation_success": sast_success,
        "security": {"status": security_status, **security_counts},
        "functional": {"status": functional_status, **functional_counts},
        "new_sast_findings": new_findings,
        "security_regression": security_regression,
        "false_success": false_success,
        "sast_runtime_disagreement": disagreement,
    }
    _validate_decision_evidence(decision, evidence, paths["decision"])

    classification = _string(
        decision.get("classification"), f"{paths['decision']}.classification"
    )
    if disagreement != (classification == "sast_runtime_disagreement"):
        raise ReportDataError(
            f"Classification in '{paths['decision']}' disagrees with the "
            "recomputed SAST/runtime evidence-conflict state."
        )

    origins, provenance_complete = _rule_provenance(baseline_finding)
    scanner_count = _integer(
        baseline_finding.get("scanner_finding_count"),
        f"{paths['baseline_correlated']}.scanner_finding_count",
    )

    model = _string(remediation.get("model"), f"{paths['remediation']}.model")
    workspace_model = workspace.get("model")
    if workspace_model is not None and workspace_model != model:
        raise ReportDataError(
            f"Workspace and remediation models disagree for {case_id} "
            f"attempt {attempt}."
        )

    reason_codes = decision.get("reason_codes", [])
    if not isinstance(reason_codes, list) or not all(
        isinstance(reason, str) and reason for reason in reason_codes
    ):
        raise ReportDataError(
            f"Expected a reason-code list in '{paths['decision']}'."
        )

    candidate_origin = entry.get("candidate_origin", "ai_generated")
    candidate_origin = _string(candidate_origin, f"{label}.candidate_origin")
    metric_scope = entry.get("metric_scope", "primary_ai_attempt_metrics")
    metric_scope = _string(metric_scope, f"{label}.metric_scope")

    evidence_revision = entry.get("evidence_revision")
    if evidence_revision is not None:
        evidence_revision = _mapping(
            evidence_revision, f"{label}.evidence_revision"
        )
        revision_record: dict[str, Any] = {
            "revision": _string(
                evidence_revision.get("revision"),
                f"{label}.evidence_revision.revision",
            ),
            "reason": _string(
                evidence_revision.get("reason"),
                f"{label}.evidence_revision.reason",
            ),
        }
        historical_artifacts = {}
        for name in (
            "historical_decision",
            "historical_adjudication_result",
        ):
            configured_history = evidence_revision.get(name)
            if configured_history is None:
                continue
            history_path = _resolve_artifact(project_root, configured_history)
            historical_artifacts[name] = _artifact_record(
                project_root, history_path
            )
            if name == "historical_adjudication_result":
                historical_review, historical_packet = (
                    _historical_adjudication(
                        project_root=project_root,
                        result_path=history_path,
                        case_id=case_id,
                        canonical_id=canonical_id,
                        attempt=attempt,
                    )
                )
                revision_record["historical_adjudication"] = historical_review
                historical_artifacts["historical_adjudication_packet"] = (
                    historical_packet
                )
        revision_record["historical_artifacts"] = historical_artifacts
        evidence_revision = revision_record

    row = {
        "case_id": case_id,
        "case": case_name,
        "application": application,
        "cwe": cwe,
        "canonical_id": canonical_id,
        "attempt": attempt,
        "retry_of_attempt": retry_of_attempt,
        "candidate_origin": candidate_origin,
        "metric_scope": metric_scope,
        "evidence_revision": evidence_revision,
        "model": model,
        "response_id": remediation.get("response_id"),
        "policy_version": decision.get("policy_version"),
        "classification": classification,
        "reason_codes": reason_codes,
        "decision": _string(
            decision.get("disposition"), f"{paths['decision']}.disposition"
        ),
        "retry_allowed": decision.get("retry_allowed"),
        "human_review_status": _mapping(
            decision.get("human_review"), f"{paths['decision']}.human_review"
        ).get("status"),
        "evidence": evidence,
        "scanner_evidence": {
            "finding_count": scanner_count,
            "rule_origins": origins,
            "rule_provenance_complete": provenance_complete,
        },
        "artifacts": {
            name: _artifact_record(project_root, path)
            for name, path in paths.items()
        },
    }
    try:
        row["adjudication"] = evaluate_adjudication(
            project_root=project_root,
            row=row,
            packet_path=paths.get("adjudication_packet"),
            result_path=paths.get("adjudication_result"),
        )
    except AdjudicationDataError as error:
        raise ReportDataError(str(error)) from error
    return row


def collect_attempts(
    project_root: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    attempts = manifest.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ReportDataError("The manifest must contain a non-empty attempts list.")

    rows = []
    keys: set[tuple[str, int]] = set()
    canonical_attempts: set[tuple[str, int]] = set()

    for index, raw_entry in enumerate(attempts):
        entry = _mapping(raw_entry, f"manifest.attempts[{index}]")
        row = _build_attempt_row(project_root, entry, index)
        if row["candidate_origin"] != "ai_generated":
            raise ReportDataError(
                f"Primary attempt {row['case_id']} attempt {row['attempt']} "
                "must be labeled ai_generated."
            )
        if row["metric_scope"] != "primary_ai_attempt_metrics":
            raise ReportDataError(
                f"Primary attempt {row['case_id']} attempt {row['attempt']} "
                "has an invalid metric scope."
            )
        key = (row["case_id"], row["attempt"])
        canonical_key = (row["canonical_id"], row["attempt"])
        if key in keys or canonical_key in canonical_attempts:
            raise ReportDataError(
                f"Duplicate selected attempt: {row['case_id']} attempt "
                f"{row['attempt']}."
            )
        keys.add(key)
        canonical_attempts.add(canonical_key)
        rows.append(row)

    selected = {(row["case_id"], row["attempt"]) for row in rows}
    for row in rows:
        prior = row["retry_of_attempt"]
        if prior is not None and (row["case_id"], prior) not in selected:
            raise ReportDataError(
                f"Retry {row['case_id']} attempt {row['attempt']} references "
                f"unselected attempt {prior}."
            )

    return rows


def collect_controls(
    project_root: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_controls = manifest.get("controls", [])
    if not isinstance(raw_controls, list):
        raise ReportDataError("The manifest controls field must be a list.")

    controls = []
    keys: set[tuple[str, int]] = set()
    for index, raw_entry in enumerate(raw_controls):
        entry = _mapping(raw_entry, f"manifest.controls[{index}]")
        row = _build_attempt_row(
            project_root,
            entry,
            index,
            entry_collection="controls",
        )
        key = (row["case_id"], row["attempt"])
        if key in keys:
            raise ReportDataError(
                f"Duplicate outcome-coverage control: {row['case_id']} "
                f"attempt {row['attempt']}."
            )
        keys.add(key)

        if row["candidate_origin"] == "ai_generated":
            raise ReportDataError(
                f"Control {row['case_id']} must not be labeled ai_generated."
            )
        if row["metric_scope"] != "outcome_coverage_only":
            raise ReportDataError(
                f"Control {row['case_id']} must use outcome_coverage_only."
            )
        expected = _string(
            entry.get("expected_classification"),
            f"manifest.controls[{index}].expected_classification",
        )
        if row["classification"] != expected:
            raise ReportDataError(
                f"Control {row['case_id']} produced classification "
                f"{row['classification']}, expected {expected}."
            )
        row["expected_classification"] = expected
        controls.append(row)
    return controls


def calculate_outcome_coverage(
    rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> dict[str, Any]:
    required = (
        "validated_candidate",
        "sast_false_success",
    )
    primary_classifications = Counter(row["classification"] for row in rows)
    control_classifications = Counter(
        row["classification"] for row in controls
    )
    outcomes = {}
    for classification in required:
        primary_count = primary_classifications.get(classification, 0)
        control_count = control_classifications.get(classification, 0)
        outcomes[classification] = {
            "observed_in_primary_ai_attempts": primary_count > 0,
            "primary_ai_attempt_count": primary_count,
            "demonstrated_by_non_ai_control": control_count > 0,
            "control_count": control_count,
            "covered": primary_count > 0 or control_count > 0,
        }
    return {
        "required_outcomes": outcomes,
        "all_required_outcomes_covered": all(
            outcome["covered"] for outcome in outcomes.values()
        ),
        "primary_ai_classifications": dict(
            sorted(primary_classifications.items())
        ),
        "control_classifications": dict(
            sorted(control_classifications.items())
        ),
        "metric_separation": (
            "Outcome-coverage controls are excluded from all primary "
            "AI-attempt metrics."
        ),
    }


def calculate_retry_analysis(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_attempt = {(row["case_id"], row["attempt"]): row for row in rows}
    analyses = []
    status_rank = {"fail": 0, "inconclusive": 1, "pass": 2}
    syntax_rank = {"fail": 0, "not_implemented": 0, "pass": 1}
    sast_rank = {"not_evaluated": -1, "persistent": 0, "resolved": 1}

    for current in rows:
        prior_attempt = current["retry_of_attempt"]
        if prior_attempt is None:
            continue
        prior = by_attempt[(current["case_id"], prior_attempt)]
        old = prior["evidence"]
        new = current["evidence"]
        comparisons = {
            "syntax": (
                syntax_rank.get(new["syntax"], -1),
                syntax_rank.get(old["syntax"], -1),
            ),
            "target_sast": (
                sast_rank.get(new["target_sast"], -2),
                sast_rank.get(old["target_sast"], -2),
            ),
            "security_validation": (
                status_rank.get(new["security"]["status"], -1),
                status_rank.get(old["security"]["status"], -1),
            ),
            "functional_validation": (
                status_rank.get(new["functional"]["status"], -1),
                status_rank.get(old["functional"]["status"], -1),
            ),
            "new_sast_findings": (
                -new["new_sast_findings"],
                -old["new_sast_findings"],
            ),
        }
        improved_dimensions = [
            name for name, (new_value, old_value) in comparisons.items()
            if new_value > old_value
        ]
        worsened_dimensions = [
            name for name, (new_value, old_value) in comparisons.items()
            if new_value < old_value
        ]
        analyses.append(
            {
                "case_id": current["case_id"],
                "case": current["case"],
                "from_attempt": prior_attempt,
                "to_attempt": current["attempt"],
                "improved": bool(improved_dimensions) and not worsened_dimensions,
                "improved_dimensions": improved_dimensions,
                "worsened_dimensions": worsened_dimensions,
            }
        )

    return analyses


def calculate_metrics(
    rows: list[dict[str, Any]],
    retry_analysis: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(rows)
    sast_successes = sum(
        row["evidence"]["sast_remediation_success"] for row in rows
    )
    security_passes = sum(
        row["evidence"]["security"]["status"] == "pass" for row in rows
    )
    functional_passes = sum(
        row["evidence"]["functional"]["status"] == "pass" for row in rows
    )
    regressions = sum(row["evidence"]["security_regression"] for row in rows)
    false_successes = sum(row["evidence"]["false_success"] for row in rows)
    disagreements = sum(
        row["evidence"]["sast_runtime_disagreement"] for row in rows
    )
    improved_retries = sum(item["improved"] for item in retry_analysis)
    adjudications = sum(
        row["decision"] == "NEEDS_HUMAN_ADJUDICATION" for row in rows
    )
    completed_adjudications = sum(
        row["adjudication"]["status"] == "completed" for row in rows
    )

    decision_distribution = Counter(row["decision"] for row in rows)
    known_decisions = (
        "REJECT",
        "READY_FOR_HUMAN_REVIEW",
        "NEEDS_HUMAN_ADJUDICATION",
    )
    distribution = {
        name: decision_distribution.get(name, 0) for name in known_decisions
    }
    distribution.update(
        {
            name: count
            for name, count in sorted(decision_distribution.items())
            if name not in distribution
        }
    )
    return {
        "sast_remediation_success_rate": _rate(sast_successes, total),
        "targeted_security_validation_pass_rate": _rate(
            security_passes, total
        ),
        "functional_preservation_rate": _rate(functional_passes, total),
        "security_regression_new_finding_rate": _rate(regressions, total),
        "sast_false_success_count": false_successes,
        "sast_runtime_disagreement_count": disagreements,
        "retry_improvement_rate": _rate(improved_retries, len(retry_analysis)),
        "human_adjudication_rate": _rate(adjudications, total),
        "human_adjudication_completion_rate": _rate(
            completed_adjudications, adjudications
        ),
        "decision_distribution": distribution,
    }


def _provenance_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [
        row for row in rows
        if row["scanner_evidence"]["rule_provenance_complete"]
    ]
    unrecorded = [
        {
            "case_id": row["case_id"],
            "attempt": row["attempt"],
            "baseline": row["artifacts"]["baseline_correlated"]["path"],
        }
        for row in rows
        if not row["scanner_evidence"]["rule_provenance_complete"]
    ]
    origins = sorted(
        {
            origin
            for row in complete
            for origin in row["scanner_evidence"]["rule_origins"]
        }
    )
    return {
        "attempts_with_complete_rule_provenance": len(complete),
        "attempts_with_unrecorded_rule_provenance": len(unrecorded),
        "recorded_rule_origins": origins,
        "unrecorded_attempts": unrecorded,
    }


def _adjudication_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = [row["adjudication"] for row in rows if row["adjudication"]["required"]]
    statuses = Counter(item["status"] for item in required)
    verdicts = Counter(
        item["verdict"] for item in required if item.get("verdict") is not None
    )
    return {
        "required": len(required),
        "missing_packet": statuses.get("missing_packet", 0),
        "pending": statuses.get("pending", 0),
        "completed": statuses.get("completed", 0),
        "verdict_distribution": dict(sorted(verdicts.items())),
    }


def build_report_data(
    project_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    manifest_path = manifest_path.resolve()
    manifest = load_json(manifest_path)
    rows = collect_attempts(project_root, manifest)
    controls = collect_controls(project_root, manifest)
    retry_analysis = calculate_retry_analysis(rows)
    metrics = calculate_metrics(rows, retry_analysis)

    manifest_record: dict[str, str] = {"sha256": _sha256(manifest_path)}
    try:
        manifest_record["path"] = _relative_path(project_root, manifest_path)
    except ValueError:
        manifest_record["path"] = str(manifest_path)

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "project": "FixProof",
        "study_id": manifest.get("study_id", "fixproof-evaluation"),
        "aggregation_unit": "remediation_attempt",
        "case_count": len({row["case_id"] for row in rows}),
        "attempt_count": len(rows),
        "control_count": len(controls),
        "manifest": manifest_record,
        "experiment_matrix": rows,
        "outcome_coverage_controls": controls,
        "outcome_coverage": calculate_outcome_coverage(rows, controls),
        "metrics": metrics,
        "metric_definitions": METRIC_DEFINITIONS,
        "retry_analysis": retry_analysis,
        "adjudication_summary": _adjudication_summary(rows),
        "provenance_summary": _provenance_summary(rows),
    }


def _markdown_status(status: str) -> str:
    return status.replace("_", " ").title()


def _markdown_decision(decision: str) -> str:
    labels = {
        "REJECT": "Reject",
        "READY_FOR_HUMAN_REVIEW": "Ready for human review",
        "NEEDS_HUMAN_ADJUDICATION": "Human adjudication",
    }
    return labels.get(decision, _markdown_status(decision))


def _format_rate(metric: dict[str, Any]) -> str:
    if metric["percentage"] is None:
        return f"{metric['numerator']}/{metric['denominator']} (N/A)"
    return (
        f"{metric['numerator']}/{metric['denominator']} "
        f"({metric['percentage']:.1f}%)"
    )


def render_markdown(report: dict[str, Any]) -> str:
    rows = report["experiment_matrix"]
    metrics = report["metrics"]
    lines = [
        "# FixProof Pilot Evaluation Report",
        "",
        (
            "This report is generated deterministically from the authoritative "
            f"attempt manifest `{report['manifest']['path']}`. Rates use the "
            "remediation attempt as the aggregation unit. This is the four-attempt "
            "pilot, separate from primary-v1. Legacy JSON fields named primary "
            "refer to AI attempts within this pilot."
        ),
        "",
        "## Experiment matrix",
        "",
        "| Case | CWE | Attempt | SAST | Security | Functional | New findings | Decision |",
        "|---|---:|---:|---|---|---|---:|---|",
    ]

    for row in rows:
        evidence = row["evidence"]
        security = evidence["security"]
        functional = evidence["functional"]
        lines.append(
            "| "
            f"{row['case']} | {row['cwe'].removeprefix('CWE-')} | "
            f"{row['attempt']} | {_markdown_status(evidence['target_sast'])} | "
            f"{_markdown_status(security['status'])} "
            f"({security['passed']}/{security['total']}) | "
            f"{_markdown_status(functional['status'])} "
            f"({functional['passed']}/{functional['total']}) | "
            f"{evidence['new_sast_findings']} | "
            f"{_markdown_decision(row['decision'])} |"
        )

    controls = report["outcome_coverage_controls"]
    lines.extend(
        [
            "",
            "## Outcome-coverage controls",
            "",
            (
                "These deterministic non-AI controls exercise missing policy "
                "outcomes and are excluded from every pilot AI-attempt metric."
            ),
            "",
            "| Control | Origin | SAST | Security | Functional | Classification | Decision |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in controls:
        evidence = row["evidence"]
        lines.append(
            f"| {row['case']} | {row['candidate_origin']} | "
            f"{_markdown_status(evidence['target_sast'])} | "
            f"{_markdown_status(evidence['security']['status'])} | "
            f"{_markdown_status(evidence['functional']['status'])} | "
            f"`{row['classification']}` | {_markdown_decision(row['decision'])} |"
        )

    coverage = report["outcome_coverage"]
    lines.extend(
        [
            "",
            "| Required outcome | Pilot AI attempt | Non-AI control | Covered |",
            "|---|---|---|---|",
        ]
    )
    for name, outcome in coverage["required_outcomes"].items():
        lines.append(
            f"| `{name}` | "
            f"{'Yes' if outcome['observed_in_primary_ai_attempts'] else 'No'} | "
            f"{'Yes' if outcome['demonstrated_by_non_ai_control'] else 'No'} | "
            f"{'Yes' if outcome['covered'] else 'No'} |"
        )

    metric_labels = {
        "sast_remediation_success_rate": "SAST remediation success rate",
        "targeted_security_validation_pass_rate": (
            "Targeted security validation pass rate"
        ),
        "functional_preservation_rate": "Functional preservation rate",
        "security_regression_new_finding_rate": (
            "Security regression/new finding rate"
        ),
        "retry_improvement_rate": "Retry improvement rate",
        "human_adjudication_rate": "Human adjudication rate",
        "human_adjudication_completion_rate": (
            "Human adjudication completion rate"
        ),
    }
    lines.extend(
        [
            "",
            "## Aggregate metrics",
            "",
            "| Metric | Result |",
            "|---|---:|",
        ]
    )
    for name in metric_labels:
        lines.append(f"| {metric_labels[name]} | {_format_rate(metrics[name])} |")
    lines.extend(
        [
            f"| SAST false-success count | {metrics['sast_false_success_count']} |",
            (
                "| SAST/runtime disagreement count | "
                f"{metrics['sast_runtime_disagreement_count']} |"
            ),
            "",
            (
                "A false success requires the target SAST finding to be "
                "resolved while at least one downstream validation condition "
                "fails. A persistent target is therefore not counted as a "
                "false success."
            ),
            "",
            "## Retry analysis",
            "",
        ]
    )

    if report["retry_analysis"]:
        lines.extend(
            [
                "| Case | From | To | Improved | Improved dimensions | Worsened dimensions |",
                "|---|---:|---:|---|---|---|",
            ]
        )
        for retry in report["retry_analysis"]:
            improved = ", ".join(retry["improved_dimensions"]) or "None"
            worsened = ", ".join(retry["worsened_dimensions"]) or "None"
            lines.append(
                f"| {retry['case']} | {retry['from_attempt']} | "
                f"{retry['to_attempt']} | {'Yes' if retry['improved'] else 'No'} | "
                f"{improved} | {worsened} |"
            )
    else:
        lines.append("No retry attempts were selected by the manifest.")

    adjudication_rows = [row for row in rows if row["adjudication"]["required"]]
    lines.extend(
        [
            "",
            "## Human adjudication",
            "",
            "Human adjudication records a separate human conclusion and does not replace the automated decision.",
            "",
            "| Case | Attempt | Status | Verdict | Packet |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in adjudication_rows:
        adjudication = row["adjudication"]
        packet = adjudication.get("packet", {}).get("path", "Not selected")
        verdict = adjudication.get("verdict") or "Pending"
        lines.append(
            f"| {row['case']} | {row['attempt']} | "
            f"{_markdown_status(adjudication['status'])} | {verdict} | "
            f"`{packet}` |"
        )

    evidence_revisions = [
        row for row in rows if row["evidence_revision"] is not None
    ]
    if evidence_revisions:
        lines.extend(
            [
                "",
                "## Evidence revisions",
                "",
                "| Case | Attempt | Revision | Historical adjudication | Reason |",
                "|---|---:|---|---|---|",
            ]
        )
        for row in evidence_revisions:
            revision = row["evidence_revision"]
            historical_review = revision.get("historical_adjudication")
            historical_label = (
                f"{historical_review['verdict']} by "
                f"{historical_review['reviewer']}"
                if historical_review
                else "None"
            )
            lines.append(
                f"| {row['case']} | {row['attempt']} | "
                f"`{revision['revision']}` | {historical_label} | "
                f"{revision['reason']} |"
            )
        lines.extend(
            [
                "",
                (
                    "Historical decisions and adjudications remain preserved "
                    "with SHA-256 digests in the machine-readable report."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Evidence provenance",
            "",
            "| Case | Attempt | Rule origin | Policy | Decision artifact |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in rows:
        origins = ", ".join(row["scanner_evidence"]["rule_origins"])
        decision_path = row["artifacts"]["decision"]["path"]
        lines.append(
            f"| {row['case']} | {row['attempt']} | {origins} | "
            f"{row['policy_version']} | `{decision_path}` |"
        )

    provenance = report["provenance_summary"]
    lines.extend(
        [
            "",
            (
                f"Rule provenance is recorded for "
                f"{provenance['attempts_with_complete_rule_provenance']}/"
                f"{report['attempt_count']} selected attempts. The historical "
                "XSS baseline uses the pre-provenance schema, so its rule origin "
                "is reported as `unrecorded` rather than inferred."
            ),
            "",
            "The machine-readable report records every selected artifact path "
            "and SHA-256 digest so the matrix can be audited against its inputs.",
            "",
            "## Interpretation limits",
            "",
            "- These rates describe a small, controlled benchmark and should not be generalized to production remediation performance.",
            "- Targeted runtime tests establish behavior for the tested endpoint and payloads, not application-wide security.",
            "- A SAST/runtime disagreement is escalated for human adjudication; it is not an automatic approval.",
            "",
        ]
    )
    return "\n".join(lines)


def build_report(
    project_root: Path,
    manifest_path: Path,
    json_output: Path,
    markdown_output: Path,
) -> dict[str, Any]:
    report = build_report_data(project_root, manifest_path)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_output.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate authoritative FixProof attempt artifacts into the "
            "experiment matrix and evaluation metrics."
        )
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/evaluation/experiment-manifest.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("data/evaluation/experiment-report.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("docs/evaluation-report.md"),
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    def from_root(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (project_root / path).resolve()

    report = build_report(
        project_root=project_root,
        manifest_path=from_root(args.manifest),
        json_output=from_root(args.json_output),
        markdown_output=from_root(args.markdown_output),
    )
    print("=" * 60)
    print("FixProof Experiment Evaluation Report")
    print("=" * 60)
    print(f"Cases: {report['case_count']}")
    print(f"Attempts: {report['attempt_count']}")
    print(f"JSON: {from_root(args.json_output)}")
    print(f"Markdown: {from_root(args.markdown_output)}")


if __name__ == "__main__":
    main()
