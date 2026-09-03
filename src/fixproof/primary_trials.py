from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fixproof.agent.context_builder import build_contexts
from fixproof.agent.prompt_builder import build_prompts
from fixproof.agent.remediation_agent import run_remediation
from fixproof.config import find_environment_file, load_environment_file
from fixproof.evaluation.benchmark_verifier import (
    load_json,
    resolve_project_path,
    sha256_file,
    verify_file_bindings,
)
from fixproof.findings.finding_correlator import correlate_findings
from fixproof.patches.patch_workspace import create_patch_workspace
from fixproof.scanners.semgrep_parser import parse_semgrep
from fixproof.validation.decision_engine import run_decision_engine
from fixproof.validation.functional_validator import run_functional_validation
from fixproof.validation.security_validator import run_security_validation
from fixproof.validation.validation_runner import run_validation


TRIAL_PLAN_PATH = Path("data/evaluation/trial-plan.json")
BENCHMARK_MANIFEST_PATH = Path(
    "data/evaluation/primary-benchmark-manifest.json"
)
DEFAULT_OUTPUT_ROOT = Path("data/primary_trials/v1")
PRIMARY_EXPERIMENT_MANIFEST = "primary-experiment-manifest.json"
COLLECTION_CONFIRMATION = "PRIMARY-V1-15"
TERMINAL_ATTEMPT_STATUSES = frozenset(
    {
        "completed",
        "model_generation_failed",
        "needs_additional_context",
        "candidate_application_failed",
    }
)
UNCERTAIN_ATTEMPT_STATUSES = frozenset({"api_request_started"})
COLLECTION_IMPLEMENTATION_PATHS = (
    "src/fixproof/primary_trials.py",
    "src/fixproof/agent/context_builder.py",
    "src/fixproof/agent/prompt_builder.py",
    "src/fixproof/agent/remediation_agent.py",
    "src/fixproof/findings/finding_correlator.py",
    "src/fixproof/patches/patch_workspace.py",
    "src/fixproof/scanners/semgrep_parser.py",
    "src/fixproof/scanners/semgrep_runner.py",
    "src/fixproof/validation/browser_xss.py",
    "src/fixproof/validation/decision_engine.py",
    "src/fixproof/validation/functional_validator.py",
    "src/fixproof/validation/security_validator.py",
    "src/fixproof/validation/validation_runner.py",
)


class PrimaryTrialError(RuntimeError):
    """Raised when a primary-study integrity rule would be violated."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def repository_relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def validate_frozen_inputs(
    project_root: Path,
    *,
    plan: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify every immutable input before a schedule or API call is used."""

    project_root = project_root.resolve()
    plan_path = project_root / TRIAL_PLAN_PATH
    manifest_path = project_root / BENCHMARK_MANIFEST_PATH
    plan = plan or load_json(plan_path)
    manifest = manifest or load_json(manifest_path)

    errors: list[str] = []
    if plan.get("protocol_frozen") is not True:
        errors.append("The primary trial plan is not frozen.")
    if plan.get("plan_status") != "frozen_ready_for_primary_collection":
        errors.append("The primary trial plan is not ready for collection.")
    if manifest.get("suite_frozen") is not True:
        errors.append("The primary benchmark manifest is not frozen.")
    if manifest.get("candidate_prompts_must_exclude_this_manifest") is not True:
        errors.append("The manifest does not require evaluator-input withholding.")

    freeze_evidence = plan.get("freeze_evidence", {})
    for name, binding in freeze_evidence.items():
        expected_hash = binding.get("sha256")
        if not expected_hash:
            continue
        try:
            bound_path = resolve_project_path(project_root, binding["path"])
        except (KeyError, ValueError) as exc:
            errors.append(f"Invalid freeze binding '{name}': {exc}")
            continue
        if not bound_path.is_file():
            errors.append(f"Frozen input is missing: {binding['path']}")
            continue
        actual_hash = sha256_file(bound_path)
        if actual_hash != expected_hash:
            errors.append(
                f"Frozen input changed: {binding['path']} "
                f"(expected {expected_hash}, found {actual_hash})."
            )

    manifest_binding = freeze_evidence.get("benchmark_manifest", {})
    manifest_hash = sha256_file(manifest_path)
    if manifest_binding.get("sha256") != manifest_hash:
        errors.append("The active benchmark manifest does not match its freeze hash.")

    verification_binding = freeze_evidence.get("baseline_verification", {})
    try:
        verification_path = resolve_project_path(
            project_root,
            verification_binding["path"],
        )
        verification = load_json(verification_path)
    except (KeyError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"Baseline verification evidence is unavailable: {exc}")
        verification = {}

    if verification.get("status") != "ready":
        errors.append("The latest primary baseline verification is not ready.")
    if verification.get("manifest", {}).get("sha256") != manifest_hash:
        errors.append("Baseline verification is not bound to the frozen manifest.")
    if verification_binding.get("manifest_sha256") != manifest_hash:
        errors.append("The trial plan's verification binding is stale.")

    plan_cases = {case["case_id"]: case for case in plan.get("benchmarks", [])}
    manifest_cases = manifest.get("cases", [])
    expected_cwes = {"CWE-22", "CWE-79", "CWE-89"}
    if len(manifest_cases) != 3:
        errors.append("The primary suite must contain exactly three cases.")
    if {case.get("cwe") for case in manifest_cases} != expected_cwes:
        errors.append("The primary suite CWE set changed.")

    for case in manifest_cases:
        case_id = case.get("case_id")
        plan_case = plan_cases.get(case_id)
        if plan_case is None:
            errors.append(f"Manifest case is absent from the trial plan: {case_id}")
            continue
        if plan_case.get("primary_application") != case.get("application"):
            errors.append(f"Application binding changed for case '{case_id}'.")
        if plan_case.get("cwe") != case.get("cwe"):
            errors.append(f"CWE binding changed for case '{case_id}'.")
        file_result = verify_file_bindings(project_root, case)
        if file_result["status"] != "pass":
            errors.append(f"Baseline files changed for case '{case_id}'.")

    treatment = plan.get("treatments", {})
    attempts_per_case = treatment.get("planned_attempts_per_case")
    planned_attempts = treatment.get("planned_primary_attempts")
    if attempts_per_case != 5 or planned_attempts != 15:
        errors.append("The frozen schedule must remain five attempts per case, 15 total.")

    if errors:
        raise PrimaryTrialError("\n".join(errors))

    return {
        "status": "pass",
        "manifest_sha256": manifest_hash,
        "suite_id": manifest["suite_id"],
        "model": treatment["candidate_generator"],
        "attempts_per_case": attempts_per_case,
        "planned_attempts": planned_attempts,
        "plan": plan,
        "manifest": manifest,
        "verification": verification,
    }


def build_schedule(frozen: dict[str, Any]) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    attempts_per_case = frozen["attempts_per_case"]

    for case in frozen["manifest"]["cases"]:
        for attempt_number in range(1, attempts_per_case + 1):
            attempts.append(
                {
                    "trial_id": (
                        f"{frozen['suite_id']}-{case['case_id']}-"
                        f"initial-{attempt_number:02d}"
                    ),
                    "case_id": case["case_id"],
                    "application": case["application"],
                    "cwe": case["cwe"],
                    "attempt": attempt_number,
                    "condition": "initial",
                    "metric_scope": "primary",
                    "status": "planned",
                }
            )

    if len(attempts) != frozen["planned_attempts"]:
        raise PrimaryTrialError("Generated schedule does not match the frozen total.")
    return attempts


def find_verification_case(
    verification: dict[str, Any],
    case_id: str,
) -> dict[str, Any]:
    matches = [
        case for case in verification.get("cases", [])
        if case.get("case_id") == case_id
    ]
    if len(matches) != 1:
        raise PrimaryTrialError(
            f"Expected one baseline verification case for '{case_id}'."
        )
    return matches[0]


def write_normalized_subset(
    normalized: dict[str, Any],
    findings: list[dict[str, Any]],
    output_file: Path,
) -> dict[str, Any]:
    subset = copy.deepcopy(normalized)
    subset["findings"] = findings
    subset["scan"]["finding_count"] = len(findings)
    subset["scan"]["finding_count_by_rule_origin"] = dict(
        sorted(Counter(finding["rule_origin"] for finding in findings).items())
    )
    write_json_atomic(output_file, subset)
    return subset


def audit_prompt_withholding(
    case: dict[str, Any],
    prompt_data: dict[str, Any],
) -> None:
    """Reject prompts containing evaluator-only names, payloads, or paths."""

    serialized = json.dumps(prompt_data, sort_keys=True)
    banned_values = [
        *case["tests"]["security"]["names"],
        *case["tests"]["functional"]["names"],
        "<script>alert(1)</script>",
        "' OR '1'='1",
        "../outside-secret.txt",
        "FIXPROOF_CONTROLLED_TRAVERSAL_SECRET",
        "primary-benchmark-manifest.json",
        "primary-baseline-verification.json",
        "security_validator.py",
        "functional_validator.py",
    ]
    leaked = [value for value in banned_values if value and value in serialized]
    if leaked:
        raise PrimaryTrialError(
            "Evaluator-only data leaked into the remediation prompt: "
            + ", ".join(leaked)
        )


def prepare_case(
    project_root: Path,
    frozen: dict[str, Any],
    case: dict[str, Any],
    output_directory: Path,
) -> dict[str, Any]:
    """Build one deterministic, target-only prompt from frozen scan evidence."""

    verification_case = find_verification_case(
        frozen["verification"],
        case["case_id"],
    )
    raw_relative = verification_case["scanner_evidence"]["configured"]["path"]
    raw_file = resolve_project_path(project_root, raw_relative)

    full_normalized_file = output_directory / "baseline-normalized.json"
    full_correlated_file = output_directory / "baseline-correlated.json"
    target_normalized_file = output_directory / "target-normalized.json"
    target_correlated_file = output_directory / "target-correlated.json"
    contexts_file = output_directory / "contexts.json"
    prompts_file = output_directory / "prompts.json"

    normalized = parse_semgrep(
        input_file=raw_file,
        output_file=full_normalized_file,
        source_root=project_root,
    )
    full_correlated = correlate_findings(
        input_file=full_normalized_file,
        output_file=full_correlated_file,
    )

    target_rule_ids = set(case["scanner_expectation"]["any_target_rule_id"])
    target_findings = [
        finding for finding in normalized.get("findings", [])
        if finding.get("cwe") == case["cwe"]
        and finding.get("rule_id") in target_rule_ids
    ]
    if not target_findings:
        raise PrimaryTrialError(
            f"Frozen target scanner evidence is missing for '{case['case_id']}'."
        )
    expected_origin = case["scanner_expectation"]["rule_origin"]
    if {finding.get("rule_origin") for finding in target_findings} != {
        expected_origin
    }:
        raise PrimaryTrialError(
            f"Scanner-rule provenance changed for '{case['case_id']}'."
        )

    write_normalized_subset(normalized, target_findings, target_normalized_file)
    target_correlated = correlate_findings(
        input_file=target_normalized_file,
        output_file=target_correlated_file,
    )
    targets = target_correlated.get("findings", [])
    if len(targets) != 1:
        raise PrimaryTrialError(
            f"Expected one canonical target for '{case['case_id']}', found "
            f"{len(targets)}."
        )
    canonical_id = targets[0]["canonical_id"]
    if canonical_id not in {
        finding["canonical_id"] for finding in full_correlated.get("findings", [])
    }:
        raise PrimaryTrialError("Target is absent from full baseline evidence.")

    contexts = build_contexts(
        input_file=target_correlated_file,
        output_file=contexts_file,
        project_root=project_root,
    )
    prompts = build_prompts(contexts_file, prompts_file)
    if contexts["context_build"]["contexts_created"] != 1:
        raise PrimaryTrialError("Target preparation did not create one context.")
    if prompts["prompt_build"]["prompts_created"] != 1:
        raise PrimaryTrialError("Target preparation did not create one prompt.")
    audit_prompt_withholding(case, prompts)

    return {
        "case_id": case["case_id"],
        "canonical_id": canonical_id,
        "baseline_raw": repository_relative(project_root, raw_file),
        "baseline_raw_sha256": sha256_file(raw_file),
        "baseline_correlated": repository_relative(
            project_root, full_correlated_file
        ) if full_correlated_file.is_relative_to(project_root) else str(
            full_correlated_file.resolve()
        ),
        "contexts": repository_relative(project_root, contexts_file)
        if contexts_file.is_relative_to(project_root)
        else str(contexts_file.resolve()),
        "prompts": repository_relative(project_root, prompts_file)
        if prompts_file.is_relative_to(project_root)
        else str(prompts_file.resolve()),
        "prompt_sha256": sha256_file(prompts_file),
        "prompt_withholding_audit": "pass",
        "target_rule_ids": sorted(
            {finding["rule_id"] for finding in target_findings}
        ),
        "target_rule_origin": expected_origin,
    }


def build_dry_run(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    frozen = validate_frozen_inputs(project_root)
    schedule = build_schedule(frozen)

    with tempfile.TemporaryDirectory(prefix="fixproof-primary-dry-run-") as temp:
        temporary_root = Path(temp)
        preparations = [
            prepare_case(
                project_root,
                frozen,
                case,
                temporary_root / case["case_id"],
            )
            for case in frozen["manifest"]["cases"]
        ]

    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "primary_trial_dry_run",
        "status": "ready",
        "writes_performed": False,
        "model_calls_performed": 0,
        "suite_id": frozen["suite_id"],
        "manifest_sha256": frozen["manifest_sha256"],
        "model": frozen["model"],
        "schedule": schedule,
        "preparations": preparations,
    }


def git_output(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise PrimaryTrialError(completed.stderr.strip() or "Git command failed.")
    return completed.stdout.strip()


def verify_collection_worktree(project_root: Path, output_root: Path) -> str:
    """Require committed implementation code while allowing trial artifacts."""

    project_root = project_root.resolve()
    output_relative = repository_relative(project_root, output_root)
    status_lines = git_output(
        project_root,
        "status",
        "--porcelain",
        "--untracked-files=all",
    ).splitlines()
    unexpected: list[str] = []
    for line in status_lines:
        path_text = line[3:].replace("\\", "/")
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        if not (
            path_text == output_relative
            or path_text.startswith(f"{output_relative}/")
        ):
            unexpected.append(line)
    if unexpected:
        raise PrimaryTrialError(
            "Commit implementation changes before primary collection. "
            "Unexpected working-tree changes:\n" + "\n".join(unexpected)
        )
    return git_output(project_root, "rev-parse", "HEAD")


def collection_implementation_bindings(
    project_root: Path,
) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for relative in COLLECTION_IMPLEMENTATION_PATHS:
        path = resolve_project_path(project_root, relative)
        if not path.is_file():
            raise PrimaryTrialError(f"Collection implementation is missing: {relative}")
        bindings[relative] = sha256_file(path)
    return bindings


def select_scheduled_attempts(
    schedule: list[dict[str, Any]],
    case_id: str | None,
    attempt: int | None,
) -> list[dict[str, Any]]:
    if attempt is not None and case_id is None:
        raise PrimaryTrialError("--attempt requires --case.")
    selected = [
        item for item in schedule
        if (case_id is None or item["case_id"] == case_id)
        and (attempt is None or item["attempt"] == attempt)
    ]
    if not selected:
        raise PrimaryTrialError("No scheduled primary attempts match the selection.")
    return selected


def transition_attempt(
    state_file: Path,
    record: dict[str, Any],
    status: str,
    **fields: Any,
) -> dict[str, Any]:
    record["status"] = status
    record.update(fields)
    record.setdefault("history", []).append(
        {"status": status, "recorded_at": utc_now()}
    )
    write_json_atomic(state_file, record)
    return record


def artifact_binding(project_root: Path, path: Path) -> dict[str, str]:
    return {
        "path": repository_relative(project_root, path),
        "sha256": sha256_file(path),
    }


def run_one_attempt(
    project_root: Path,
    frozen: dict[str, Any],
    case: dict[str, Any],
    scheduled: dict[str, Any],
    preparation: dict[str, Any],
    output_root: Path,
    *,
    remediation_runner: Callable[..., dict[str, Any]] = run_remediation,
) -> dict[str, Any]:
    attempt_directory = (
        output_root
        / "cases"
        / case["case_id"]
        / f"attempt-{scheduled['attempt']:02d}"
    )
    state_file = attempt_directory / "attempt.json"
    remediation_file = attempt_directory / "remediation.json"

    if state_file.is_file():
        record = load_json(state_file)
        if record.get("trial_id") != scheduled["trial_id"]:
            raise PrimaryTrialError(f"Attempt identity mismatch: {state_file}")
        if record.get("status") in TERMINAL_ATTEMPT_STATUSES:
            print(f"[SKIP] {scheduled['trial_id']}: {record['status']}")
            return record
        if record.get("status") in UNCERTAIN_ATTEMPT_STATUSES:
            if remediation_file.is_file():
                saved = load_json(remediation_file).get("remediation", {})
                if saved.get("canonical_id") == preparation.get("canonical_id"):
                    transition_attempt(
                        state_file,
                        record,
                        "model_response_saved",
                        remediation=artifact_binding(
                            project_root, remediation_file
                        ),
                        response_id=saved.get("response_id"),
                        error=None,
                    )
                else:
                    print(
                        f"[BLOCKED] {scheduled['trial_id']}: the saved response "
                        "does not match the scheduled canonical finding."
                    )
                    return record
            else:
                print(
                    f"[BLOCKED] {scheduled['trial_id']}: an API request may already "
                    "have occurred; no automatic replacement call was made."
                )
                return record
    else:
        record = {
            "schema_version": "0.1",
            "project": "FixProof",
            "artifact_type": "primary_trial_attempt",
            **scheduled,
            "model": frozen["model"],
            "canonical_id": preparation["canonical_id"],
            "manifest_sha256": frozen["manifest_sha256"],
            "prompt_sha256": preparation["prompt_sha256"],
            "history": [],
        }

    prompt_file = resolve_project_path(project_root, preparation["prompts"])
    context_file = resolve_project_path(project_root, preparation["contexts"])
    baseline_correlated = resolve_project_path(
        project_root,
        preparation["baseline_correlated"],
    )

    if not remediation_file.is_file():
        transition_attempt(state_file, record, "api_request_started")
        try:
            remediation = remediation_runner(
                prompt_file=prompt_file,
                output_file=remediation_file,
                canonical_id=preparation["canonical_id"],
                model=frozen["model"],
            )
        except Exception as exc:
            return transition_attempt(
                state_file,
                record,
                "model_generation_failed",
                terminal=True,
                error={"type": type(exc).__name__, "message": str(exc)},
                note=(
                    "No automatic replacement request is allowed for this "
                    "scheduled initial attempt."
                ),
            )
        transition_attempt(
            state_file,
            record,
            "model_response_saved",
            remediation=artifact_binding(project_root, remediation_file),
            response_id=remediation["remediation"].get("response_id"),
        )

    remediation = load_json(remediation_file)
    if remediation["remediation"].get("needs_additional_context"):
        return transition_attempt(
            state_file,
            record,
            "needs_additional_context",
            terminal=True,
            remediation=artifact_binding(project_root, remediation_file),
        )

    try:
        workspace_metadata = create_patch_workspace(
            project_root=project_root,
            context_file=context_file,
            remediation_file=remediation_file,
            workspace_root=attempt_directory / "workspace",
            attempt=scheduled["attempt"],
        )
    except Exception as exc:
        return transition_attempt(
            state_file,
            record,
            "candidate_application_failed",
            terminal=True,
            error={"type": type(exc).__name__, "message": str(exc)},
            remediation=artifact_binding(project_root, remediation_file),
        )

    workspace_directory = Path(
        workspace_metadata["patch_workspace"]["workspace_directory"]
    )
    transition_attempt(
        state_file,
        record,
        "candidate_applied",
        error=None,
        workspace_metadata=artifact_binding(
            project_root, workspace_directory / "workspace.json"
        ),
        candidate_patch=artifact_binding(
            project_root, workspace_directory / "candidate.patch"
        ),
    )

    preliminary_file = attempt_directory / "preliminary.json"
    security_file = attempt_directory / "security.json"
    functional_file = attempt_directory / "functional.json"
    decision_file = attempt_directory / "decision.json"
    try:
        preliminary = run_validation(
            project_root=project_root,
            baseline_correlated_file=baseline_correlated,
            workspace_dir=workspace_directory,
            canonical_id=preparation["canonical_id"],
            output_file=preliminary_file,
            artifact_dir=attempt_directory / "sast",
        )
        syntax_status = preliminary["validation"]["syntax"]["status"]
        if syntax_status != "pass":
            return transition_attempt(
                state_file,
                record,
                "completed",
                terminal=True,
                classification="syntax_failure",
                disposition="REJECT",
                evidence={
                    "syntax": syntax_status,
                    "target_sast": "not_evaluated",
                    "security_validation": "not_run",
                    "functional_validation": "not_run",
                },
                artifacts={
                    "remediation": artifact_binding(project_root, remediation_file),
                    "preliminary": artifact_binding(project_root, preliminary_file),
                },
            )

        security = run_security_validation(
            contexts_file=context_file,
            workspace_dir=workspace_directory,
            canonical_id=preparation["canonical_id"],
            output_file=security_file,
        )
        functional = run_functional_validation(
            contexts_file=context_file,
            workspace_dir=workspace_directory,
            canonical_id=preparation["canonical_id"],
            output_file=functional_file,
        )
        if security["security_validation"]["status"] == "inconclusive":
            return transition_attempt(
                state_file,
                record,
                "validation_infrastructure_failed",
                terminal=False,
                error={
                    "type": "InconclusiveSecurityValidation",
                    "message": "Security validation must be rerun with the saved candidate.",
                },
            )
        decision = run_decision_engine(
            preliminary_file=preliminary_file,
            security_file=security_file,
            functional_file=functional_file,
            output_file=decision_file,
        )
    except Exception as exc:
        message = str(exc)
        if "Candidate application failed to start" in message:
            status = "candidate_application_failed"
            terminal = True
        else:
            status = "validation_infrastructure_failed"
            terminal = False
        return transition_attempt(
            state_file,
            record,
            status,
            terminal=terminal,
            error={"type": type(exc).__name__, "message": message},
            note="Resume reuses the saved model response and makes no new API call.",
        )

    for manifest_case in frozen["manifest"]["cases"]:
        if verify_file_bindings(project_root, manifest_case)["status"] != "pass":
            raise PrimaryTrialError(
                "A frozen baseline changed during primary validation."
            )

    decision_record = decision["decision"]
    target_sast = decision_record["evidence"]["target_sast"]
    sast_only = frozen["plan"]["comparison"]["sast_only_mapping"].get(
        target_sast,
        "INCONCLUSIVE",
    )
    artifacts = {
        "remediation": artifact_binding(project_root, remediation_file),
        "workspace": artifact_binding(
            project_root, workspace_directory / "workspace.json"
        ),
        "patch": artifact_binding(
            project_root, workspace_directory / "candidate.patch"
        ),
        "preliminary": artifact_binding(project_root, preliminary_file),
        "security": artifact_binding(project_root, security_file),
        "functional": artifact_binding(project_root, functional_file),
        "decision": artifact_binding(project_root, decision_file),
    }
    return transition_attempt(
        state_file,
        record,
        "completed",
        terminal=True,
        classification=decision_record["classification"],
        disposition=decision_record["disposition"],
        sast_only_interpretation=sast_only,
        evidence=decision_record["evidence"],
        evaluation_labels=decision_record["evaluation_labels"],
        artifacts=artifacts,
    )


def build_collection_state(
    output_root: Path,
    schedule: list[dict[str, Any]],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for scheduled in schedule:
        state_file = (
            output_root
            / "cases"
            / scheduled["case_id"]
            / f"attempt-{scheduled['attempt']:02d}"
            / "attempt.json"
        )
        if state_file.is_file():
            records.append(load_json(state_file))

    status_counts = Counter(record.get("status", "unknown") for record in records)
    terminal_count = sum(
        record.get("status") in TERMINAL_ATTEMPT_STATUSES for record in records
    )
    denominator = len(schedule)

    def count_where(predicate: Callable[[dict[str, Any]], bool]) -> int:
        return sum(1 for record in records if predicate(record))

    valid_candidates = count_where(
        lambda record: record.get("status") == "completed"
    )
    sast_successes = count_where(
        lambda record: record.get("evidence", {}).get("target_sast") == "resolved"
    )
    security_passes = count_where(
        lambda record: record.get("evidence", {}).get("security_validation")
        == "pass"
    )
    functional_passes = count_where(
        lambda record: record.get("evidence", {}).get("functional_validation")
        == "pass"
    )
    new_findings = count_where(
        lambda record: record.get("evidence", {}).get("new_sast_findings", 0) > 0
    )
    sast_apparent_successes = count_where(
        lambda record: record.get("sast_only_interpretation") == "APPARENT_SUCCESS"
    )
    false_successes = count_where(
        lambda record: record.get("evaluation_labels", {}).get("false_success")
        is True
    )
    disagreements = count_where(
        lambda record: record.get("classification") == "sast_runtime_disagreement"
    )
    dispositions = Counter(
        record["disposition"] for record in records if record.get("disposition")
    )

    def metric(count: int) -> dict[str, Any]:
        return {
            "count": count,
            "denominator": denominator,
            "rate": count / denominator if denominator else None,
        }

    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "primary_trial_collection_state",
        "updated_at": utc_now(),
        "status": (
            "complete" if terminal_count == len(schedule) else "in_progress"
        ),
        "scheduled": len(schedule),
        "recorded": len(records),
        "terminal": terminal_count,
        "remaining": len(schedule) - terminal_count,
        "status_counts": dict(sorted(status_counts.items())),
        "primary_metrics": {
            "provisional": terminal_count != denominator,
            "denominator_policy": "all_15_scheduled_initial_attempts",
            "valid_candidate_generation_application": metric(valid_candidates),
            "sast_remediation_success": metric(sast_successes),
            "targeted_security_pass": metric(security_passes),
            "functional_preservation": metric(functional_passes),
            "new_finding": metric(new_findings),
            "sast_only_apparent_success": metric(sast_apparent_successes),
            "sast_false_success": metric(false_successes),
            "sast_runtime_disagreement": metric(disagreements),
            "fixproof_disposition_distribution": dict(sorted(dispositions.items())),
        },
    }


def execute_collection(
    project_root: Path,
    *,
    case_id: str | None = None,
    attempt: int | None = None,
    remediation_runner: Callable[..., dict[str, Any]] = run_remediation,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_root = (project_root / DEFAULT_OUTPUT_ROOT).resolve()
    implementation_commit = verify_collection_worktree(project_root, output_root)
    implementation_files = collection_implementation_bindings(project_root)
    frozen = validate_frozen_inputs(project_root)
    schedule = build_schedule(frozen)
    selected = select_scheduled_attempts(schedule, case_id, attempt)

    preparation_root = output_root / "preparation"
    preparations = {
        case["case_id"]: prepare_case(
            project_root,
            frozen,
            case,
            preparation_root / case["case_id"],
        )
        for case in frozen["manifest"]["cases"]
    }
    schedule_file = output_root / PRIMARY_EXPERIMENT_MANIFEST
    if schedule_file.is_file():
        recorded_schedule = load_json(schedule_file)
        if recorded_schedule.get("implementation_files") != implementation_files:
            raise PrimaryTrialError(
                "The collection implementation changed after collection started."
            )
        if recorded_schedule.get("attempts") != schedule:
            raise PrimaryTrialError("The recorded primary schedule changed.")
    else:
        write_json_atomic(
            schedule_file,
            {
                "schema_version": "0.1",
                "project": "FixProof",
                "artifact_type": "primary_experiment_manifest",
                "created_at": utc_now(),
                "suite_id": frozen["suite_id"],
                "manifest_sha256": frozen["manifest_sha256"],
                "implementation_commit": implementation_commit,
                "implementation_files": implementation_files,
                "model": frozen["model"],
                "attempts": schedule,
                "preparations": preparations,
            },
        )

    case_map = {
        case["case_id"]: case for case in frozen["manifest"]["cases"]
    }
    for scheduled in selected:
        print(f"\n=== {scheduled['trial_id']} ===")
        run_one_attempt(
            project_root,
            frozen,
            case_map[scheduled["case_id"]],
            scheduled,
            preparations[scheduled["case_id"]],
            output_root,
            remediation_runner=remediation_runner,
        )

    state = build_collection_state(output_root, schedule)
    write_json_atomic(output_root / "collection-state.json", state)
    return state


def print_dry_run(result: dict[str, Any]) -> None:
    counts = Counter(item["cwe"] for item in result["schedule"])
    print("=" * 60)
    print("FixProof Primary Trial Dry Run")
    print("=" * 60)
    print("Frozen inputs: PASS")
    print("Prompt withholding audit: PASS")
    for cwe in sorted(counts):
        print(f"{cwe}: {counts[cwe]} initial attempts")
    print(f"Total: {len(result['schedule'])} primary attempts")
    print(f"Model: {result['model']}")
    print("Model calls performed: 0")
    print("Repository writes performed: no")
    print("READY FOR COMMITTED IMPLEMENTATION REVIEW")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan or execute the frozen FixProof primary-v1 trials."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the frozen schedule and prompts without writes or API calls.",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Execute selected, scheduled primary attempts.",
    )
    parser.add_argument("--case", choices=("xss", "sqli", "path-traversal"))
    parser.add_argument("--attempt", type=int, choices=range(1, 6))
    parser.add_argument(
        "--confirm-collection",
        help=(
            "Required for --execute. The exact value is "
            f"{COLLECTION_CONFIRMATION}."
        ),
    )
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()

    if args.dry_run:
        if args.case is not None or args.attempt is not None:
            parser.error("--case and --attempt are execute-mode selectors.")
        result = build_dry_run(project_root)
        print_dry_run(result)
        return

    if args.confirm_collection != COLLECTION_CONFIRMATION:
        parser.error(
            "--execute requires --confirm-collection "
            f"{COLLECTION_CONFIRMATION}"
        )

    if args.env_file is not None:
        load_environment_file(args.env_file, required=True)
    else:
        environment_file = find_environment_file(project_root)
        if environment_file is not None:
            load_environment_file(environment_file)
    if not os.getenv("OPENAI_API_KEY"):
        parser.error(
            "No OpenAI API key configured. Set OPENAI_API_KEY or use the "
            "local ignored .env file."
        )

    state = execute_collection(
        project_root,
        case_id=args.case,
        attempt=args.attempt,
    )
    print("=" * 60)
    print("FixProof Primary Trial Collection")
    print("=" * 60)
    print(f"Status: {state['status']}")
    print(f"Terminal: {state['terminal']}/{state['scheduled']}")
    print(f"Remaining: {state['remaining']}")
    print(f"State: {project_root / DEFAULT_OUTPUT_ROOT / 'collection-state.json'}")


if __name__ == "__main__":
    try:
        main()
    except PrimaryTrialError as exc:
        raise SystemExit(f"FixProof primary trial error:\n{exc}") from exc
