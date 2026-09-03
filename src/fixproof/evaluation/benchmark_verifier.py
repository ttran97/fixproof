from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fixproof.scanners.semgrep_runner import run_semgrep
from fixproof.validation.functional_validator import (
    determine_functional_status,
    run_functional_tests,
    run_path_traversal_functional_tests,
    run_sqli_functional_tests,
)
from fixproof.validation.security_validator import (
    HOST,
    PORT,
    determine_security_status,
    port_is_open,
    run_path_traversal_security_tests,
    run_sqli_security_tests,
    run_xss_tests,
    stop_application,
    wait_for_application,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_project_path(project_root: Path, relative_path: str) -> Path:
    root = project_root.resolve()
    resolved = (root / Path(relative_path)).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Benchmark path escapes the project root: {relative_path}")
    return resolved


def verify_file_bindings(
    project_root: Path,
    case: dict[str, Any],
) -> dict[str, Any]:
    files = []
    all_match = True

    for binding in case["files"]:
        path = resolve_project_path(project_root, binding["path"])
        exists = path.is_file()
        actual = sha256_file(path) if exists else None
        matches = exists and actual == binding["sha256"]
        all_match = all_match and matches
        files.append(
            {
                "path": binding["path"],
                "expected_sha256": binding["sha256"],
                "actual_sha256": actual,
                "matches": matches,
            }
        )

    return {"status": "pass" if all_match else "fail", "files": files}


def verify_restore_copy(
    project_root: Path,
    case: dict[str, Any],
) -> dict[str, Any]:
    application_directory = resolve_project_path(
        project_root,
        case["application_directory"],
    )

    with tempfile.TemporaryDirectory(prefix="fixproof-primary-restore-") as temp:
        restored = Path(temp) / application_directory.name
        shutil.copytree(
            application_directory,
            restored,
            ignore=shutil.ignore_patterns("node_modules"),
        )

        mismatches = []
        for binding in case["files"]:
            original = resolve_project_path(project_root, binding["path"])
            relative_to_application = original.relative_to(application_directory)
            copied = restored / relative_to_application
            if not copied.is_file() or sha256_file(copied) != binding["sha256"]:
                mismatches.append(binding["path"])

    return {
        "status": "pass" if not mismatches else "fail",
        "mismatches": mismatches,
    }


def check_javascript_syntax(source_file: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["node", "--check", str(source_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "fail", "returncode": None, "error": str(exc)}

    return {
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def start_baseline_application(application_directory: Path) -> subprocess.Popen:
    if port_is_open(HOST, PORT):
        raise RuntimeError(f"Port {PORT} is already in use.")

    node_modules = application_directory / "node_modules"
    if not node_modules.is_dir():
        raise FileNotFoundError(
            f"Locked dependencies are not installed in {application_directory}. "
            "Run npm ci before baseline verification."
        )

    environment = os.environ.copy()
    environment["PORT"] = str(PORT)

    process = subprocess.Popen(
        ["node", "app.js"],
        cwd=str(application_directory),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if not wait_for_application(process, HOST, PORT, 10):
        stdout, stderr = (
            process.communicate(timeout=2)
            if process.poll() is not None
            else ("", "")
        )
        stop_application(process)
        raise RuntimeError(
            "Baseline application failed to start.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )

    return process


def run_baseline_tests(case: dict[str, Any]) -> dict[str, Any]:
    route = case["route"]
    parameter = case["input_parameter"]
    cwe = case["cwe"]

    if cwe == "CWE-79":
        security_tests = run_xss_tests(route, parameter)
        functional_tests = run_functional_tests(route, parameter)
    elif cwe == "CWE-89":
        security_tests = run_sqli_security_tests(route, parameter)
        functional_tests = run_sqli_functional_tests(route, parameter)
    elif cwe == "CWE-22":
        security_tests = run_path_traversal_security_tests(route, parameter)
        functional_tests = run_path_traversal_functional_tests(route, parameter)
    else:
        raise ValueError(f"Unsupported benchmark CWE: {cwe}")

    security_status = determine_security_status(security_tests)
    functional_status = determine_functional_status(functional_tests)
    expected_security = case["tests"]["security"]
    expected_functional = case["tests"]["functional"]

    observed_security_names = [test["test"] for test in security_tests]
    observed_functional_names = [test["test"] for test in functional_tests]

    browser_execution = None
    if expected_security.get("browser_execution_required"):
        browser_statuses = [
            test["evaluation"]["browser"]["status"]
            for test in security_tests
        ]
        execution_count = browser_statuses.count("executed")
        browser_execution = {
            "status": (
                "pass"
                if execution_count
                == expected_security["expected_browser_executions"]
                else "fail"
            ),
            "expected_executions": expected_security[
                "expected_browser_executions"
            ],
            "observed_executions": execution_count,
            "statuses": browser_statuses,
        }

    test_contract_matches = (
        len(security_tests) == expected_security["count"]
        and observed_security_names == expected_security["names"]
        and len(functional_tests) == expected_functional["count"]
        and observed_functional_names == expected_functional["names"]
    )

    baseline_behavior_passes = (
        security_status == expected_security["expected_baseline_status"]
        and functional_status == expected_functional["expected_baseline_status"]
        and test_contract_matches
        and (
            browser_execution is None
            or browser_execution["status"] == "pass"
        )
    )

    return {
        "status": "pass" if baseline_behavior_passes else "fail",
        "security": {
            "status": security_status,
            "expected_status": expected_security["expected_baseline_status"],
            "count": len(security_tests),
            "tests": security_tests,
        },
        "functional": {
            "status": functional_status,
            "expected_status": expected_functional["expected_baseline_status"],
            "count": len(functional_tests),
            "tests": functional_tests,
        },
        "browser_execution": browser_execution,
        "test_contract_matches": test_contract_matches,
    }


def semgrep_rule_ids(path: Path) -> tuple[str | None, list[str]]:
    raw = load_json(path)
    return raw.get("version"), sorted(
        {
            result.get("check_id")
            for result in raw.get("results", [])
            if result.get("check_id")
        }
    )


def verify_scanner_evidence(
    project_root: Path,
    case: dict[str, Any],
    evidence_directory: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    expectation = case["scanner_expectation"]
    target_rules = set(expectation["any_target_rule_id"])
    source_relative = Path(case["source_file"])
    default_output = evidence_directory / f"{case['case_id']}-default.json"

    run_semgrep(
        target=source_relative,
        output=default_output,
        project_rule_dir=project_root / "__no_controlled_rules__",
        timeout_seconds=timeout_seconds,
    )
    default_version, default_rules = semgrep_rule_ids(default_output)
    default_detected = bool(target_rules.intersection(default_rules))
    expected_default_detected = expectation["default_target_detected"]

    configured_output = default_output
    configured_version = default_version
    configured_rules = default_rules

    if expectation["rule_origin"] == "fixproof_controlled":
        configured_output = (
            evidence_directory / f"{case['case_id']}-configured.json"
        )
        run_semgrep(
            target=source_relative,
            output=configured_output,
            project_rule_dir=project_root / "rules",
            timeout_seconds=timeout_seconds,
        )
        configured_version, configured_rules = semgrep_rule_ids(configured_output)

    configured_detected = bool(target_rules.intersection(configured_rules))
    status = (
        "pass"
        if default_detected == expected_default_detected and configured_detected
        else "fail"
    )

    return {
        "status": status,
        "expected_default_target_detected": expected_default_detected,
        "default_target_detected": default_detected,
        "configured_target_detected": configured_detected,
        "target_rule_ids": sorted(target_rules),
        "default": {
            "path": default_output.relative_to(project_root).as_posix(),
            "semgrep_version": default_version,
            "observed_rule_ids": default_rules,
            "sha256": sha256_file(default_output),
        },
        "configured": {
            "path": configured_output.relative_to(project_root).as_posix(),
            "semgrep_version": configured_version,
            "observed_rule_ids": configured_rules,
            "sha256": sha256_file(configured_output),
        },
    }


def verify_case(
    project_root: Path,
    case: dict[str, Any],
    evidence_directory: Path,
    scanner_timeout_seconds: int,
) -> dict[str, Any]:
    application_directory = resolve_project_path(
        project_root,
        case["application_directory"],
    )
    source_file = resolve_project_path(project_root, case["source_file"])

    file_bindings = verify_file_bindings(project_root, case)
    restore_copy = verify_restore_copy(project_root, case)
    syntax = check_javascript_syntax(source_file)
    target_only = case["intentionally_seeded_vulnerabilities"] == [case["cwe"]]

    runtime: dict[str, Any]
    process = None
    try:
        process = start_baseline_application(application_directory)
        runtime = run_baseline_tests(case)
    except Exception as exc:
        runtime = {"status": "fail", "error": str(exc)}
    finally:
        if process is not None:
            stop_application(process)

    try:
        scanner = verify_scanner_evidence(
            project_root=project_root,
            case=case,
            evidence_directory=evidence_directory,
            timeout_seconds=scanner_timeout_seconds,
        )
    except Exception as exc:
        scanner = {"status": "fail", "error": str(exc)}

    checks = {
        "file_bindings": file_bindings["status"],
        "restore_copy": restore_copy["status"],
        "syntax": syntax["status"],
        "target_only_contract": "pass" if target_only else "fail",
        "runtime_ground_truth": runtime["status"],
        "scanner_evidence": scanner["status"],
    }
    status = "pass" if all(value == "pass" for value in checks.values()) else "fail"

    return {
        "case_id": case["case_id"],
        "application": case["application"],
        "cwe": case["cwe"],
        "status": status,
        "checks": checks,
        "file_bindings": file_bindings,
        "restore_copy": restore_copy,
        "syntax": syntax,
        "runtime_ground_truth": runtime,
        "scanner_evidence": scanner,
    }


def verify_primary_benchmarks(
    project_root: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    manifest_path = manifest_path.resolve()
    manifest = load_json(manifest_path)
    evidence_directory = project_root / "data" / "primary_baselines" / "raw_scans"
    evidence_directory.mkdir(parents=True, exist_ok=True)

    if manifest["project"] != "FixProof":
        raise ValueError("Primary benchmark manifest has an unexpected project.")
    if manifest.get("suite_frozen") is not True:
        raise ValueError(
            "Primary benchmark manifest must be frozen before final verification."
        )

    scanner_timeout_seconds = manifest["scanner"]["process_timeout_seconds"]
    cases = [
        verify_case(
            project_root=project_root,
            case=case,
            evidence_directory=evidence_directory,
            scanner_timeout_seconds=scanner_timeout_seconds,
        )
        for case in manifest["cases"]
    ]
    passed = sum(case["status"] == "pass" for case in cases)

    result = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "primary_baseline_verification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": {
            "path": manifest_path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(manifest_path),
            "suite_id": manifest["suite_id"],
        },
        "status": "ready" if passed == len(cases) else "not_ready",
        "summary": {
            "cases": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
        },
        "cases": cases,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the frozen ground truth for FixProof primary v1."
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/evaluation/primary-benchmark-manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/evaluation/primary-baseline-verification.json"),
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    manifest = (
        args.manifest
        if args.manifest.is_absolute()
        else project_root / args.manifest
    )
    output = args.output if args.output.is_absolute() else project_root / args.output

    result = verify_primary_benchmarks(project_root, manifest, output)
    print("=" * 60)
    print("FixProof Primary Benchmark Verification")
    print("=" * 60)
    for case in result["cases"]:
        print(f"[{case['status'].upper()}] {case['case_id']} ({case['cwe']})")
        for check, status in case["checks"].items():
            print(f"  {check}: {status}")
    print(
        f"Result: {result['status']} "
        f"({result['summary']['passed']}/{result['summary']['cases']} cases)"
    )
    print(f"Report: {output}")

    if result["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
