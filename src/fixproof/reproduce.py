from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fixproof.evaluation.dashboard import create_dashboard_server
from fixproof.evaluation.report_builder import ReportDataError, build_report


PRIMARY_METRIC_SCOPE = "primary_ai_attempt_metrics"
CONTROL_METRIC_SCOPE = "outcome_coverage_only"
REQUIRED_DECISIONS = {
    "REJECT",
    "READY_FOR_HUMAN_REVIEW",
    "NEEDS_HUMAN_ADJUDICATION",
}


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VerificationResult:
    report: dict[str, Any]
    checks: tuple[ReadinessCheck, ...]
    tests_passed: bool

    @property
    def ready(self) -> bool:
        return self.tests_passed and all(check.passed for check in self.checks)


def _artifact_records_are_complete(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False

    for row in rows:
        artifacts = row.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            return False
        for record in artifacts.values():
            if not isinstance(record, dict):
                return False
            path = record.get("path")
            digest = record.get("sha256")
            if not isinstance(path, str) or not path:
                return False
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                return False
    return True


def evaluate_readiness(report: dict[str, Any]) -> tuple[ReadinessCheck, ...]:
    """Evaluate the generated report against the final-experiment invariants."""

    attempts = report.get("experiment_matrix", [])
    controls = report.get("outcome_coverage_controls", [])
    attempts = attempts if isinstance(attempts, list) else []
    controls = controls if isinstance(controls, list) else []

    declared_attempts = report.get("attempt_count")
    declared_controls = report.get("control_count")
    declared_cases = report.get("case_count")
    experiment_shape_ok = (
        isinstance(declared_attempts, int)
        and declared_attempts > 0
        and declared_attempts == len(attempts)
        and isinstance(declared_controls, int)
        and declared_controls == len(controls)
        and isinstance(declared_cases, int)
        and declared_cases > 0
    )

    primary_scope_ok = bool(attempts) and all(
        isinstance(row, dict)
        and row.get("candidate_origin") == "ai_generated"
        and row.get("metric_scope") == PRIMARY_METRIC_SCOPE
        for row in attempts
    )
    control_scope_ok = bool(controls) and all(
        isinstance(row, dict)
        and row.get("candidate_origin") != "ai_generated"
        and row.get("metric_scope") == CONTROL_METRIC_SCOPE
        for row in controls
    )

    coverage = report.get("outcome_coverage", {})
    coverage_ok = (
        isinstance(coverage, dict)
        and coverage.get("all_required_outcomes_covered") is True
    )

    adjudication = report.get("adjudication_summary", {})
    adjudication_ok = (
        isinstance(adjudication, dict)
        and isinstance(adjudication.get("required"), int)
        and adjudication.get("missing_packet") == 0
        and adjudication.get("pending") == 0
        and adjudication.get("completed") == adjudication.get("required")
    )

    observed_decisions = {
        row.get("decision") for row in attempts if isinstance(row, dict)
    }
    decision_coverage_ok = REQUIRED_DECISIONS.issubset(observed_decisions)

    artifact_bindings_ok = _artifact_records_are_complete(attempts + controls)

    metrics = report.get("metrics", {})
    primary_rate_names = (
        "sast_remediation_success_rate",
        "targeted_security_validation_pass_rate",
        "functional_preservation_rate",
        "security_regression_new_finding_rate",
        "human_adjudication_rate",
    )
    metric_denominators_ok = isinstance(metrics, dict) and all(
        isinstance(metrics.get(name), dict)
        and metrics[name].get("denominator") == len(attempts)
        for name in primary_rate_names
    )

    return (
        ReadinessCheck(
            "experiment shape",
            experiment_shape_ok,
            f"{len(attempts)} primary attempts, {len(controls)} separated controls",
        ),
        ReadinessCheck(
            "primary AI metric scope",
            primary_scope_ok,
            "all selected attempts are AI-generated and in primary metrics",
        ),
        ReadinessCheck(
            "control metric separation",
            control_scope_ok,
            "all controls are non-AI and outcome-coverage-only",
        ),
        ReadinessCheck(
            "required policy outcomes",
            coverage_ok,
            "validated-candidate and SAST-false-success outcomes are covered",
        ),
        ReadinessCheck(
            "decision-state coverage",
            decision_coverage_ok,
            "REJECT, READY_FOR_HUMAN_REVIEW, and NEEDS_HUMAN_ADJUDICATION observed",
        ),
        ReadinessCheck(
            "human adjudication",
            adjudication_ok,
            (
                f"{adjudication.get('completed', 0)}/"
                f"{adjudication.get('required', 0)} required reviews completed"
            ),
        ),
        ReadinessCheck(
            "artifact bindings",
            artifact_bindings_ok,
            "selected artifacts have paths and SHA-256 bindings",
        ),
        ReadinessCheck(
            "primary metric denominators",
            metric_denominators_ok,
            "control rows are excluded from primary attempt denominators",
        ),
    )


def run_test_suite(project_root: Path) -> bool:
    environment = os.environ.copy()
    source_root = str(project_root / "src")
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_python_path
        else source_root + os.pathsep + existing_python_path
    )
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ]
    completed = subprocess.run(
        command,
        cwd=project_root,
        env=environment,
        check=False,
    )
    return completed.returncode == 0


def verify_project(
    project_root: Path,
    *,
    run_tests: bool = True,
) -> VerificationResult:
    """Regenerate authoritative reports and verify final-experiment readiness."""

    project_root = project_root.resolve()
    report = build_report(
        project_root=project_root,
        manifest_path=project_root
        / "data"
        / "evaluation"
        / "experiment-manifest.json",
        json_output=project_root
        / "data"
        / "evaluation"
        / "experiment-report.json",
        markdown_output=project_root / "docs" / "evaluation-report.md",
    )
    checks = evaluate_readiness(report)
    tests_passed = run_test_suite(project_root) if run_tests else True
    return VerificationResult(
        report=report,
        checks=checks,
        tests_passed=tests_passed,
    )


def _print_verification(result: VerificationResult, project_root: Path) -> None:
    print("=" * 60)
    print("FixProof Reproducibility Verification")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"Project: {project_root}")
    print(
        "Report: "
        f"{result.report['case_count']} cases, "
        f"{result.report['attempt_count']} AI attempts, "
        f"{result.report['control_count']} separated control"
    )
    print("Readiness checks:")
    for check in result.checks:
        label = "PASS" if check.passed else "FAIL"
        print(f"  [{label}] {check.name}: {check.detail}")
    print(f"  [{'PASS' if result.tests_passed else 'FAIL'}] full test suite")

    provenance = result.report.get("provenance_summary", {})
    unrecorded = provenance.get("attempts_with_unrecorded_rule_provenance", 0)
    if unrecorded:
        print(
            "Note: "
            f"{unrecorded} historical XSS attempt(s) retain explicitly "
            "unrecorded pre-provenance evidence."
        )

    print("READY" if result.ready else "NOT READY")


def _serve(project_root: Path, bind: str, port: int) -> None:
    server = create_dashboard_server(project_root, bind, port)
    host, selected_port = server.server_address[:2]
    print("=" * 60)
    print("FixProof Read-Only Evaluation Dashboard")
    print("=" * 60)
    print(f"URL: http://{host}:{selected_port}/ui/")
    print("Verification passed. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild and verify the evidence-bound FixProof final experiment, "
            "optionally serving its read-only dashboard."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--verify",
        action="store_true",
        help="regenerate reports, verify invariants, and run the full test suite",
    )
    mode.add_argument(
        "--serve",
        action="store_true",
        help="run verification, then serve the read-only dashboard",
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    try:
        result = verify_project(project_root)
    except (OSError, ReportDataError, ValueError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    _print_verification(result, project_root)
    if not result.ready:
        raise SystemExit(1)

    if args.serve:
        _serve(project_root, args.bind, args.port)


if __name__ == "__main__":
    main()
