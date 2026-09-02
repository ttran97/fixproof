from __future__ import annotations

import argparse
import json
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fixproof.evaluation.dashboard import create_dashboard_server
from fixproof.evaluation.report_builder import build_report_data
from fixproof.reproduce import evaluate_readiness
from fixproof.validation.decision_engine import run_decision_engine
from fixproof.validation.functional_validator import run_functional_validation
from fixproof.validation.security_validator import run_security_validation
from fixproof.validation.validation_runner import run_validation as run_preliminary_validation


SUPPORTED_CONTEXTS = {
    "xss": Path("data/contexts/vulnerable-js-app.json"),
    "sqli": Path("data/contexts/vulnerable-sqli-app-rule-v2.json"),
    "path-traversal": Path(
        "data/contexts/vulnerable-path-traversal-app.json"
    ),
}

VALIDATION_HOST = "127.0.0.1"
VALIDATION_PORT = 3000


class DemoError(ValueError):
    """Raised when a safe, reproducible demo cannot be selected or run."""


@dataclass(frozen=True)
class DemoSelection:
    project_root: Path
    case_id: str
    case_name: str
    application: str
    cwe: str
    canonical_id: str
    attempt: int
    contexts_file: Path
    baseline_correlated_file: Path
    baseline_source: Path
    remediation_file: Path
    preliminary_file: Path
    recorded_decision_file: Path
    workspace_metadata_file: Path
    workspace_dir: Path
    candidate_source: Path
    patch_file: Path
    model: str


@dataclass(frozen=True)
class DemoValidationResult:
    output_dir: Path
    preliminary_file: Path
    security_file: Path
    functional_file: Path
    decision_file: Path
    summary_file: Path
    decision: dict[str, Any]
    evidence_mode: dict[str, str]


Validator = Callable[[Path, Path, str, Path], dict[str, Any]]
DecisionRunner = Callable[[Path, Path, Path, Path], dict[str, Any]]
PreliminaryRunner = Callable[
    [Path, Path, Path, str, Path, Path | None],
    dict[str, Any],
]


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DemoError(f"Missing {label}: '{path}'.") from error
    except json.JSONDecodeError as error:
        raise DemoError(f"Invalid JSON in {label} '{path}': {error}.") from error

    if not isinstance(payload, dict):
        raise DemoError(f"Expected a JSON object in {label} '{path}'.")
    return payload


def _resolve_project_file(
    project_root: Path,
    configured_path: Any,
    label: str,
) -> Path:
    if not isinstance(configured_path, (str, Path)) or not str(configured_path):
        raise DemoError(f"Expected a file path for {label}.")

    raw_path = Path(configured_path)
    resolved = (
        raw_path.resolve()
        if raw_path.is_absolute()
        else (project_root / raw_path).resolve()
    )
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise DemoError(f"{label} escapes the project root: '{configured_path}'.") from error
    if not resolved.is_file():
        raise DemoError(f"Missing {label}: '{resolved}'.")
    return resolved


def select_demo_case(
    project_root: Path,
    case_id: str,
    attempt: int | None = None,
) -> DemoSelection:
    """Select one authoritative AI attempt without selecting a control."""

    project_root = project_root.resolve()
    if case_id not in SUPPORTED_CONTEXTS:
        supported = ", ".join(sorted(SUPPORTED_CONTEXTS))
        raise DemoError(
            f"Unsupported demo case '{case_id}'. Supported cases: {supported}."
        )

    manifest_path = (
        project_root / "data" / "evaluation" / "experiment-manifest.json"
    )
    manifest = _load_json(manifest_path, "experiment manifest")
    entries = manifest.get("attempts")
    if not isinstance(entries, list):
        raise DemoError("The experiment manifest does not contain an attempts list.")

    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("case_id") == case_id
        and (attempt is None or entry.get("attempt") == attempt)
    ]
    if not matches:
        attempt_label = "any selected attempt" if attempt is None else f"attempt {attempt}"
        raise DemoError(
            f"The manifest has no {case_id} entry for {attempt_label}."
        )

    entry = max(matches, key=lambda item: item.get("attempt", 0))
    selected_attempt = entry.get("attempt")
    if isinstance(selected_attempt, bool) or not isinstance(selected_attempt, int):
        raise DemoError("The selected manifest attempt is not a valid integer.")
    if entry.get("candidate_origin", "ai_generated") != "ai_generated":
        raise DemoError("The demo command accepts AI-generated attempts only.")

    artifacts = entry.get("artifacts")
    if not isinstance(artifacts, dict):
        raise DemoError("The selected manifest entry has no artifact mapping.")

    contexts_file = _resolve_project_file(
        project_root,
        SUPPORTED_CONTEXTS[case_id],
        "context artifact",
    )
    baseline_correlated_file = _resolve_project_file(
        project_root,
        artifacts.get("baseline_correlated"),
        "baseline correlated artifact",
    )
    remediation_file = _resolve_project_file(
        project_root,
        artifacts.get("remediation"),
        "remediation artifact",
    )
    preliminary_file = _resolve_project_file(
        project_root,
        artifacts.get("preliminary"),
        "preliminary-validation artifact",
    )
    recorded_decision_file = _resolve_project_file(
        project_root,
        artifacts.get("decision"),
        "recorded decision artifact",
    )
    workspace_metadata_file = _resolve_project_file(
        project_root,
        artifacts.get("workspace"),
        "workspace metadata",
    )

    workspace_payload = _load_json(workspace_metadata_file, "workspace metadata")
    workspace = workspace_payload.get("patch_workspace")
    if not isinstance(workspace, dict):
        raise DemoError("The selected workspace has no patch_workspace object.")

    canonical_id = entry.get("canonical_id")
    if not isinstance(canonical_id, str) or not canonical_id:
        raise DemoError("The selected manifest entry has no canonical ID.")
    if workspace.get("canonical_id") != canonical_id:
        raise DemoError("The selected workspace has a different canonical ID.")
    if workspace.get("attempt") not in (None, selected_attempt):
        raise DemoError("The selected workspace has a different attempt number.")
    if workspace.get("original_modified") is not False:
        raise DemoError("The selected workspace does not prove baseline preservation.")

    workspace_dir = workspace_metadata_file.parent
    candidate_source = workspace_dir / "app" / "app.js"
    patch_file = workspace_dir / "candidate.patch"
    if not candidate_source.is_file() or not patch_file.is_file():
        raise DemoError("The selected workspace is missing its candidate source or patch.")

    application = entry.get("application")
    if not isinstance(application, str) or not application:
        raise DemoError("The selected manifest entry has no application name.")
    baseline_source = _resolve_project_file(
        project_root,
        Path("sample_apps") / application / "app.js",
        "baseline source",
    )

    case_name = entry.get("case")
    cwe = entry.get("cwe")
    if not isinstance(case_name, str) or not isinstance(cwe, str):
        raise DemoError("The selected manifest entry has incomplete case metadata.")

    model = workspace.get("model")
    if not isinstance(model, str) or not model:
        model = "unrecorded"

    return DemoSelection(
        project_root=project_root,
        case_id=case_id,
        case_name=case_name,
        application=application,
        cwe=cwe,
        canonical_id=canonical_id,
        attempt=selected_attempt,
        contexts_file=contexts_file,
        baseline_correlated_file=baseline_correlated_file,
        baseline_source=baseline_source,
        remediation_file=remediation_file,
        preliminary_file=preliminary_file,
        recorded_decision_file=recorded_decision_file,
        workspace_metadata_file=workspace_metadata_file,
        workspace_dir=workspace_dir,
        candidate_source=candidate_source,
        patch_file=patch_file,
        model=model,
    )


def _ensure_validation_port_available() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((VALIDATION_HOST, VALIDATION_PORT))
    except OSError as error:
        raise DemoError(
            f"Port {VALIDATION_PORT} is already in use. Stop the baseline "
            "application or another validator before running the live demo."
        ) from error
    finally:
        probe.close()


def _new_output_directory(
    selection: DemoSelection,
    output_parent: Path | None,
) -> Path:
    if output_parent is None:
        output_parent = Path(tempfile.gettempdir())
    output_parent = output_parent.resolve()
    if output_parent.exists() and not output_parent.is_dir():
        raise DemoError(f"Demo output parent is not a directory: '{output_parent}'.")
    output_parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(
            prefix=f"fixproof-{selection.case_id}-attempt-{selection.attempt}-",
            dir=output_parent,
        )
    ).resolve()


def run_live_validation(
    selection: DemoSelection,
    output_parent: Path | None = None,
    *,
    fresh_sast: bool = False,
    preliminary_runner: PreliminaryRunner = run_preliminary_validation,
    security_runner: Validator = run_security_validation,
    functional_runner: Validator = run_functional_validation,
    decision_runner: DecisionRunner = run_decision_engine,
    check_port: bool = True,
) -> DemoValidationResult:
    """Rerun runtime validation into a unique, non-authoritative directory."""

    if check_port:
        _ensure_validation_port_available()

    output_dir = _new_output_directory(selection, output_parent)
    preliminary_file = selection.preliminary_file

    if fresh_sast:
        preliminary_file = output_dir / "preliminary.json"
        preliminary_runner(
            selection.project_root,
            selection.baseline_correlated_file,
            selection.workspace_dir,
            selection.canonical_id,
            preliminary_file,
            output_dir / "sast",
        )

    security_file = output_dir / "security.json"
    functional_file = output_dir / "functional.json"
    decision_file = output_dir / "decision.json"
    summary_file = output_dir / "summary.json"

    security = security_runner(
        selection.contexts_file,
        selection.workspace_dir,
        selection.canonical_id,
        security_file,
    )
    functional = functional_runner(
        selection.contexts_file,
        selection.workspace_dir,
        selection.canonical_id,
        functional_file,
    )
    decision = decision_runner(
        preliminary_file,
        security_file,
        functional_file,
        decision_file,
    )

    security_status = security.get("security_validation", {}).get("status")
    functional_status = functional.get("functional_validation", {}).get("status")
    live_decision = decision.get("decision")
    if not isinstance(live_decision, dict):
        raise DemoError("The live decision runner returned no decision object.")

    recorded = _load_json(selection.recorded_decision_file, "recorded decision")
    recorded_decision = recorded.get("decision")
    if not isinstance(recorded_decision, dict):
        raise DemoError("The recorded artifact contains no decision object.")

    comparison_fields = ("classification", "disposition")
    mismatches = {
        field: {
            "live": live_decision.get(field),
            "recorded": recorded_decision.get(field),
        }
        for field in comparison_fields
        if live_decision.get(field) != recorded_decision.get(field)
    }
    if mismatches:
        raise DemoError(
            "Live validation disagrees with the manifest-selected decision: "
            f"{mismatches}."
        )

    evidence_mode = {
        "ai_candidate": "recorded",
        "baseline_sast": "recorded",
        "candidate_sast": "live" if fresh_sast else "recorded",
        "runtime_security": "live",
        "functional_regression": "live",
        "decision": "live",
    }

    summary = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "disposable_demo_summary",
        "authoritative_experiment_artifact": False,
        "case": {
            "case_id": selection.case_id,
            "name": selection.case_name,
            "cwe": selection.cwe,
            "canonical_id": selection.canonical_id,
            "attempt": selection.attempt,
            "model": selection.model,
        },
        "live_results": {
            "security": security_status,
            "functional": functional_status,
            "classification": live_decision.get("classification"),
            "disposition": live_decision.get("disposition"),
        },
        "evidence_mode": evidence_mode,
        "recorded_decision_match": True,
        "outputs": {
            "preliminary": str(preliminary_file),
            "security": str(security_file),
            "functional": str(functional_file),
            "decision": str(decision_file),
        },
    }
    summary_file.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    return DemoValidationResult(
        output_dir=output_dir,
        preliminary_file=preliminary_file,
        security_file=security_file,
        functional_file=functional_file,
        decision_file=decision_file,
        summary_file=summary_file,
        decision=decision,
        evidence_mode=evidence_mode,
    )


def validate_dashboard_state(project_root: Path) -> dict[str, Any]:
    """Require the served report to match a fresh, read-only aggregation."""

    project_root = project_root.resolve()
    manifest_path = (
        project_root / "data" / "evaluation" / "experiment-manifest.json"
    )
    report_path = project_root / "data" / "evaluation" / "experiment-report.json"
    recomputed = build_report_data(project_root, manifest_path)
    selected = _load_json(report_path, "generated experiment report")
    if selected != recomputed:
        raise DemoError(
            "The dashboard report is stale. Run "
            "'.\\.venv\\Scripts\\python.exe -m fixproof.reproduce --verify' "
            "before serving the demo."
        )

    failures = [
        check.name for check in evaluate_readiness(recomputed) if not check.passed
    ]
    if failures:
        raise DemoError(
            "The experiment is not demo-ready; failed checks: "
            + ", ".join(failures)
            + "."
        )
    return recomputed


def _print_selection(selection: DemoSelection) -> None:
    print("=" * 60)
    print("FixProof Controlled Demonstration")
    print("=" * 60)
    print(f"Case: {selection.case_name} ({selection.cwe})")
    print(f"Attempt: {selection.attempt}")
    print(f"Canonical finding: {selection.canonical_id}")
    print(f"Recorded model: {selection.model}")
    print(f"Vulnerable source: {selection.baseline_source}")
    print(f"Candidate patch: {selection.patch_file}")
    print("Candidate origin: recorded AI-generated remediation")


def _print_evidence_plan(*, validate: bool, fresh_sast: bool, serve: bool) -> None:
    print()
    print("Evidence plan")
    print("- RECORDED: AI-generated candidate and baseline SAST evidence")

    if validate:
        candidate_sast = "LIVE (fresh Semgrep rescan)" if fresh_sast else "RECORDED"
        print(f"- {candidate_sast}: candidate SAST evidence")
        print("- LIVE: targeted runtime security tests")
        print("- LIVE: functional regression tests")
        print("- LIVE: deterministic decision recomputation")
        print("- DISPOSABLE: all newly generated demo outputs")
    else:
        print("- NOT RUN: candidate validation stages")

    if serve:
        print("- AUTHORITATIVE RECORDED DATA: read-only dashboard")


def _print_validation(result: DemoValidationResult) -> None:
    decision = result.decision["decision"]
    print()
    print("=" * 60)
    print("FixProof Live Demo Complete")
    print("=" * 60)
    print(f"Classification: {decision['classification']}")
    print(f"Decision: {decision['disposition']}")
    print(
        "Candidate SAST evidence: "
        f"{result.evidence_mode['candidate_sast']}"
    )
    print("Recorded decision match: yes")
    print(f"Preliminary evidence: {result.preliminary_file}")
    print(f"Disposable outputs: {result.output_dir}")
    print(f"Summary: {result.summary_file}")


def _serve_dashboard(project_root: Path, bind: str, port: int) -> None:
    report = validate_dashboard_state(project_root)
    server = create_dashboard_server(project_root, bind, port)
    host, selected_port = server.server_address[:2]
    print()
    print("=" * 60)
    print("FixProof Read-Only Evaluation Dashboard")
    print("=" * 60)
    print(
        f"Report: {report['case_count']} cases, "
        f"{report['attempt_count']} AI attempts"
    )
    print(f"URL: http://{host}:{selected_port}/ui/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Demonstrate one manifest-selected FixProof benchmark without "
            "calling the AI API or overwriting experiment artifacts."
        )
    )
    parser.add_argument(
        "--case",
        required=True,
        choices=sorted(SUPPORTED_CONTEXTS),
        dest="case_id",
    )
    parser.add_argument(
        "--attempt",
        type=int,
        help="selected attempt number; defaults to the latest selected attempt",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help=(
            "rerun targeted security, functional, and decision stages using "
            "the recorded candidate-SAST result"
        ),
    )
    parser.add_argument(
        "--fresh-sast",
        action="store_true",
        help=(
            "also rerun candidate syntax/Semgrep validation into the "
            "disposable output directory; implies --validate"
        ),
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve the current read-only authoritative dashboard",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="parent for a unique disposable output directory; defaults to TEMP",
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    try:
        selection = select_demo_case(
            project_root,
            args.case_id,
            args.attempt,
        )
        _print_selection(selection)

        validate = args.validate or args.fresh_sast
        _print_evidence_plan(
            validate=validate,
            fresh_sast=args.fresh_sast,
            serve=args.serve,
        )

        if not validate and not args.serve:
            print(
                "No live action selected. Add --validate, --fresh-sast, "
                "and/or --serve."
            )
            return

        if validate:
            result = run_live_validation(
                selection,
                args.output_dir,
                fresh_sast=args.fresh_sast,
            )
            _print_validation(result)

        if args.serve:
            _serve_dashboard(project_root, args.bind, args.port)
    except (DemoError, FileNotFoundError, NotImplementedError, OSError, RuntimeError) as error:
        parser.exit(1, f"FixProof demo failed: {error}\n")


if __name__ == "__main__":
    main()
