from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable


PROTOCOL_ID = "supplemental-v1"
DEFAULT_LOCK = Path("data/supplemental/v1/protocol-lock.json")
DEFAULT_CASES = Path("tests/supplemental/v1/cases.json")

EXPECTED_CASE_IDS = {
    "xss": (
        "XSS-P01",
        "XSS-P02",
        "XSS-P03",
        "XSS-P04",
        "XSS-P05",
        "XSS-R01",
        "XSS-S01",
        "XSS-S02",
        "XSS-S03",
    ),
    "path-traversal": (
        "PATH-P01",
        "PATH-P02",
        "PATH-R01",
        "PATH-R02",
        "PATH-R03",
        "PATH-S01",
        "PATH-S02",
        "PATH-S03",
        "PATH-S04",
        "PATH-S05",
        "PATH-S06",
    ),
    "sqli": (
        "SQL-P01",
        "SQL-P02",
        "SQL-R01",
        "SQL-R02",
        "SQL-R03",
        "SQL-S01",
        "SQL-S02",
        "SQL-S03",
    ),
}

ALLOWED_CATEGORIES = {
    "security",
    "behavioral_parity",
    "robustness_contract",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_project_path(project_root: Path, relative_path: str) -> Path:
    root = project_root.resolve()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Supplemental path escapes the project root: {relative_path}"
        ) from exc
    return resolved


def verify_protocol_lock(
    project_root: Path,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    resolved_lock = (
        lock_path.resolve()
        if lock_path is not None
        else resolve_project_path(root, str(DEFAULT_LOCK))
    )
    lock = load_json(resolved_lock)

    if lock.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Protocol lock has the wrong protocol_id.")
    if lock.get("status") != "frozen":
        raise ValueError("Supplemental protocol is not frozen.")

    bindings = [
        lock.get("protocol", {}),
        lock.get("primary_evidence_reference", {}).get("manifest", {}),
        lock.get("primary_evidence_reference", {}).get(
            "verified_report", {}
        ),
    ]

    verified_bindings: list[dict[str, str]] = []
    for binding in bindings:
        relative = binding.get("path")
        expected = binding.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError("Protocol lock contains a missing path binding.")
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(
                f"Protocol lock contains an invalid hash for {relative}."
            )

        artifact = resolve_project_path(root, relative)
        if not artifact.is_file():
            raise FileNotFoundError(f"Locked artifact not found: {artifact}")

        actual = sha256_file(artifact)
        if actual != expected.lower():
            raise ValueError(
                f"Locked artifact hash mismatch for {relative}: "
                f"expected {expected.lower()}, got {actual}"
            )

        verified_bindings.append(
            {
                "path": relative,
                "sha256": actual,
            }
        )

    return {
        "protocol_id": PROTOCOL_ID,
        "status": "verified",
        "lock": str(resolved_lock.relative_to(root)).replace("\\", "/"),
        "bindings": verified_bindings,
    }


def validate_case_manifest(
    project_root: Path,
    cases_path: Path | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    resolved_cases = (
        cases_path.resolve()
        if cases_path is not None
        else resolve_project_path(root, str(DEFAULT_CASES))
    )
    manifest = load_json(resolved_cases)

    if manifest.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Case manifest has the wrong protocol_id.")

    cwes = manifest.get("cwes")
    if not isinstance(cwes, dict):
        raise ValueError("Case manifest must contain a cwes object.")
    if tuple(cwes) != tuple(EXPECTED_CASE_IDS):
        raise ValueError(
            "Case manifest CWE order or membership differs from the frozen "
            "protocol."
        )

    all_ids: list[str] = []
    case_counts: dict[str, int] = {}
    for case_name, expected_ids in EXPECTED_CASE_IDS.items():
        case = cwes[case_name]
        if not isinstance(case, dict):
            raise ValueError(f"CWE entry must be an object: {case_name}")

        baseline = case.get("baseline")
        if not isinstance(baseline, str):
            raise ValueError(f"Missing baseline path for {case_name}.")
        if not resolve_project_path(root, baseline).is_dir():
            raise FileNotFoundError(f"Baseline directory not found: {baseline}")

        candidates = case.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != 5:
            raise ValueError(
                f"{case_name} must identify exactly five saved candidates."
            )
        attempts = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ValueError(f"Invalid candidate entry for {case_name}.")
            attempts.append(candidate.get("attempt"))
            app_path = candidate.get("app")
            if not isinstance(app_path, str):
                raise ValueError(f"Missing candidate app path for {case_name}.")
            if not resolve_project_path(root, app_path).is_dir():
                raise FileNotFoundError(
                    f"Candidate app directory not found: {app_path}"
                )
        if attempts != [1, 2, 3, 4, 5]:
            raise ValueError(
                f"{case_name} candidate attempts must be ordered 1 through 5."
            )

        tests = case.get("tests")
        if not isinstance(tests, list):
            raise ValueError(f"Missing tests list for {case_name}.")
        ids = tuple(test.get("id") for test in tests if isinstance(test, dict))
        if ids != expected_ids:
            raise ValueError(
                f"{case_name} test IDs or order differ from the frozen protocol: "
                f"expected {expected_ids}, got {ids}"
            )

        for test in tests:
            if not isinstance(test, dict):
                raise ValueError(f"Invalid test entry for {case_name}.")
            if test.get("category") not in ALLOWED_CATEGORIES:
                raise ValueError(
                    f"Invalid category for {test.get('id')}: "
                    f"{test.get('category')}"
                )
            for field in (
                "input",
                "baseline_expectation",
                "candidate_expectation",
                "security_oracle",
                "functional_oracle",
            ):
                if not isinstance(test.get(field), str) or not test[field]:
                    raise ValueError(
                        f"Test {test.get('id')} has no nonempty {field}."
                    )

        all_ids.extend(ids)
        case_counts[case_name] = len(ids)

    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Supplemental test IDs must be globally unique.")

    return {
        "protocol_id": PROTOCOL_ID,
        "status": "verified",
        "definition_only": True,
        "does_not_execute_applications": True,
        "manifest": str(resolved_cases.relative_to(root)).replace("\\", "/"),
        "manifest_sha256": sha256_file(resolved_cases),
        "case_counts": case_counts,
        "test_count": len(all_ids),
    }


def detect_environment(
    project_root: Path,
    *,
    which: Callable[[str], str | None] = shutil.which,
    chromium_path: str | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    node = which("node")
    npm = which("npm")

    resolved_chromium = chromium_path
    if resolved_chromium is None:
        resolved_chromium = find_playwright_chromium()

    playwright_available = importlib.util.find_spec("playwright") is not None

    chromium_exists = bool(
        resolved_chromium and Path(resolved_chromium).is_file()
    )

    dependency_checks = {}
    for case_name in EXPECTED_CASE_IDS:
        app = resolve_project_path(
            root,
            f"benchmarks/primary/v1/{case_name}",
        )
        dependency_checks[case_name] = {
            "package_lock": (app / "package-lock.json").is_file(),
            "node_modules": (app / "node_modules").is_dir(),
        }

    blockers = []
    if node is None:
        blockers.append("node_not_on_path")
    if npm is None:
        blockers.append("npm_not_on_path")
    if not playwright_available:
        blockers.append("playwright_python_package_missing")
    if not chromium_exists:
        blockers.append("chromium_not_installed_for_playwright")
    for case_name, status in dependency_checks.items():
        if not status["node_modules"]:
            blockers.append(f"locked_dependencies_missing:{case_name}")

    return {
        "protocol_id": PROTOCOL_ID,
        "check_type": "environment_preflight_no_candidate_execution",
        "ready_for_live_supplemental_execution": not blockers,
        "node": node,
        "npm": npm,
        "chromium": {
            "path": resolved_chromium,
            "exists": chromium_exists,
            "playwright_python_package_available": playwright_available,
        },
        "baseline_dependencies": dependency_checks,
        "blockers": blockers,
    }


def find_playwright_chromium() -> str | None:
    configured = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    search_roots: list[Path] = []
    if configured and configured != "0":
        search_roots.append(Path(configured))
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            search_roots.append(Path(local_app_data) / "ms-playwright")
    elif sys.platform == "darwin":
        search_roots.append(Path.home() / "Library/Caches/ms-playwright")
    else:
        search_roots.append(Path.home() / ".cache/ms-playwright")

    executable_patterns = (
        "chromium-*/chrome-win64/chrome.exe",
        "chromium_headless_shell-*/chrome-headless-shell-win64/"
        "chrome-headless-shell.exe",
        "chromium-*/chrome-linux/chrome",
        "chromium_headless_shell-*/chrome-headless-shell-linux64/"
        "chrome-headless-shell",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        "chromium-*/chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium",
    )
    for root in search_roots:
        for pattern in executable_patterns:
            for candidate in sorted(root.glob(pattern)):
                if candidate.is_file():
                    return str(candidate.resolve())
    return None


def verify_definition(project_root: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_definition_verification",
        "protocol": verify_protocol_lock(project_root),
        "cases": validate_case_manifest(project_root),
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the frozen FixProof supplemental protocol or report "
            "environment readiness without executing candidate applications."
        )
    )
    parser.add_argument("command", choices=("verify", "preflight"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return exit code 2 when preflight blockers exist.",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    verification = verify_definition(root)
    if args.command == "verify":
        result = verification
    else:
        result = {
            **verification,
            "artifact_type": "supplemental_environment_preflight",
            "environment": detect_environment(root),
        }

    if args.output is not None:
        output = (
            args.output.resolve()
            if args.output.is_absolute()
            else (root / args.output).resolve()
        )
        try:
            output.relative_to(root)
        except ValueError as exc:
            raise ValueError("Output must remain inside the project root.") from exc
        write_json(output, result)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if (
        args.command == "preflight"
        and args.require_ready
        and not result["environment"]["ready_for_live_supplemental_execution"]
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
