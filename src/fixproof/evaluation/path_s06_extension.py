from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_ID = "path-s06-extension-v1"
CASE_ID = "PATH-S06"
DEFAULT_DEFINITION = Path("tests/extensions/path_s06/v1/case.json")
DEFAULT_PROTOCOL = Path("docs/path-s06-extension-v1-protocol.md")
DEFAULT_LOCK = Path("data/extensions/path-s06-v1/protocol-lock.json")
DEFAULT_RUNS = Path("data/extensions/path-s06-v1/runs")
PROTECTED_DATA_ROOTS = (
    Path("data/primary_trials/v1"),
    Path("data/supplemental/v1"),
)
STARTUP_TIMEOUT_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 5


class PathS06ExtensionError(RuntimeError):
    """Raised when the frozen PATH-S06 extension cannot execute safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_fingerprint(path: Path) -> dict[str, Any]:
    """Return a deterministic digest without writing inside the source tree."""
    if not path.is_dir():
        raise PathS06ExtensionError(f"Protected data directory is missing: {path}")
    digest = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    for item in sorted(
        (candidate for candidate in path.rglob("*") if candidate.is_file()),
        key=lambda candidate: candidate.relative_to(path).as_posix(),
    ):
        relative = item.relative_to(path).as_posix()
        item_hash = sha256_file(item)
        size = item.stat().st_size
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item_hash.encode("ascii"))
        digest.update(b"\0")
        file_count += 1
        total_bytes += size
    return {
        "file_count": file_count,
        "total_bytes": total_bytes,
        "tree_sha256": digest.hexdigest(),
    }


def protected_data_snapshot(project_root: Path) -> dict[str, dict[str, Any]]:
    return {
        relative.as_posix(): tree_fingerprint(resolve_inside(project_root, relative))
        for relative in PROTECTED_DATA_ROOTS
    }


def record_protected_data_integrity(
    run_directory: Path,
    project_root: Path,
    before: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    after = protected_data_snapshot(project_root)
    record = {
        "schema_version": "0.1",
        "project": "FixProof",
        "protocol_id": PROTOCOL_ID,
        "recorded_at": utc_now(),
        "before": before,
        "after": after,
        "unchanged": before == after,
    }
    write_json(run_directory / "protected-data-integrity.json", record)
    return record


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PathS06ExtensionError(f"Invalid JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PathS06ExtensionError(f"Expected a JSON object at {path}.")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def project_root_from_module() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_inside(project_root: Path, relative: str | Path) -> Path:
    root = project_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PathS06ExtensionError(
            f"Path escapes the project root: {relative}"
        ) from exc
    return path


def validate_definition(definition: dict[str, Any]) -> None:
    if definition.get("protocol_id") != PROTOCOL_ID:
        raise PathS06ExtensionError("Unexpected extension protocol ID.")
    if definition.get("status") != "frozen":
        raise PathS06ExtensionError("The extension definition is not frozen.")
    activity = definition.get("activity") or {}
    if activity.get("model_calls") != 0 or activity.get("sast_runs") != 0:
        raise PathS06ExtensionError("Model calls and SAST runs must remain zero.")
    case = definition.get("case") or {}
    if case.get("id") != CASE_ID or case.get("category") != "security":
        raise PathS06ExtensionError("Only the registered PATH-S06 case is allowed.")
    baseline = case.get("baseline_oracle") or {}
    if baseline != {"status_code": 200, "marker_disclosed": True}:
        raise PathS06ExtensionError("The baseline oracle changed.")
    candidate = case.get("candidate_oracle") or {}
    if candidate.get("allowed_status_codes") != [400, 403, 404]:
        raise PathS06ExtensionError("The candidate status oracle changed.")
    if candidate.get("marker_disclosed") is not False:
        raise PathS06ExtensionError("The candidate marker oracle changed.")
    targets = definition.get("targets") or []
    baseline_targets = [row for row in targets if row.get("type") == "baseline"]
    candidate_targets = [row for row in targets if row.get("type") == "candidate"]
    if len(baseline_targets) != 1 or len(candidate_targets) != 5:
        raise PathS06ExtensionError(
            "Expected one baseline and five saved traversal candidates."
        )


def verify_protocol(project_root: Path) -> dict[str, Any]:
    lock_path = resolve_inside(project_root, DEFAULT_LOCK)
    definition_path = resolve_inside(project_root, DEFAULT_DEFINITION)
    protocol_path = resolve_inside(project_root, DEFAULT_PROTOCOL)
    lock = read_json(lock_path)
    if lock.get("protocol_id") != PROTOCOL_ID or lock.get("status") != "frozen":
        raise PathS06ExtensionError("The PATH-S06 protocol lock is not frozen.")
    bindings = lock.get("bindings") or []
    required = {
        DEFAULT_PROTOCOL.as_posix(),
        DEFAULT_DEFINITION.as_posix(),
        "src/fixproof/evaluation/path_s06_extension.py",
    }
    bound = {row.get("path") for row in bindings}
    if bound != required:
        raise PathS06ExtensionError("Protocol-lock bindings are incomplete.")
    for binding in bindings:
        path = resolve_inside(project_root, binding["path"])
        if not path.is_file() or sha256_file(path) != binding.get("sha256"):
            raise PathS06ExtensionError(
                f"Frozen protocol binding changed: {binding['path']}"
            )
    definition = read_json(definition_path)
    validate_definition(definition)
    for target in definition["targets"]:
        source = resolve_inside(project_root, target["source"])
        if not source.is_file() or sha256_file(source) != target["sha256"]:
            raise PathS06ExtensionError(
                f"Frozen target source changed: {target['source']}"
            )
    for package_key in ("manifest", "lockfile"):
        binding = definition["package"][package_key]
        path = resolve_inside(project_root, binding["path"])
        if not path.is_file() or sha256_file(path) != binding["sha256"]:
            raise PathS06ExtensionError(
                f"Frozen package binding changed: {binding['path']}"
            )
    return definition


def response_record(
    status_code: int | None,
    body: str,
    *,
    content_type: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "body": body,
        "content_type": content_type,
        "error": error,
    }


def evaluate_baseline_response(
    response: dict[str, Any], marker: str
) -> dict[str, Any]:
    status = response.get("status_code")
    body = response.get("body") or ""
    disclosed = marker in body
    if status is None:
        return {
            "status": "inconclusive",
            "reason": "No valid baseline HTTP response was observed.",
            "marker_disclosed": disclosed,
            "status_allowed": False,
        }
    passed = status == 200 and disclosed
    return {
        "status": "pass" if passed else "fail",
        "reason": (
            "Baseline disclosed the controlled outside marker through the link."
            if passed
            else "Expected HTTP 200 with the controlled outside marker."
        ),
        "marker_disclosed": disclosed,
        "status_allowed": status == 200,
    }


def evaluate_candidate_response(
    response: dict[str, Any], marker: str
) -> dict[str, Any]:
    status = response.get("status_code")
    body = response.get("body") or ""
    disclosed = marker in body
    allowed = status in {400, 403, 404}
    if status is None:
        return {
            "status": "inconclusive",
            "reason": "No valid candidate HTTP response was observed.",
            "marker_disclosed": disclosed,
            "status_allowed": False,
        }
    passed = allowed and not disclosed
    if disclosed:
        reason = "The candidate disclosed the controlled outside marker."
    elif not allowed:
        reason = "The candidate did not return the registered HTTP 400/403/404 response."
    else:
        reason = "The candidate denied the linked outside file without disclosure."
    return {
        "status": "pass" if passed else "fail",
        "reason": reason,
        "marker_disclosed": disclosed,
        "status_allowed": allowed,
    }


def find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def wait_for_application(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise PathS06ExtensionError("The application exited during startup.")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)
    raise PathS06ExtensionError(
        f"The application did not bind within {STARTUP_TIMEOUT_SECONDS} seconds."
    )


def send_request(port: int, value: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"name": value})
    url = f"http://127.0.0.1:{port}/file?{query}"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response_record(
                int(response.status),
                body,
                content_type=response.headers.get("Content-Type"),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return response_record(
            int(exc.code),
            body,
            content_type=exc.headers.get("Content-Type"),
            error=str(exc),
        )
    except (OSError, urllib.error.URLError) as exc:
        return response_record(None, "", error=str(exc))


def command_version(command: str, argument: str = "--version") -> str:
    completed = subprocess.run(
        [command, argument],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0 or not output:
        raise PathS06ExtensionError(
            f"Could not determine version for {command}: {output}"
        )
    return output.splitlines()[0]


def build_dependencies(
    definition: dict[str, Any],
    project_root: Path,
    temporary_root: Path,
    npm_binary: str,
) -> tuple[Path, dict[str, Any]]:
    dependency_root = temporary_root / "dependency-template"
    dependency_root.mkdir()
    for key in ("manifest", "lockfile"):
        source = resolve_inside(project_root, definition["package"][key]["path"])
        shutil.copy2(source, dependency_root / source.name)
    command = [npm_binary, "ci", "--no-audit", "--no-fund"]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=dependency_root,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    record = {
        "command": [Path(npm_binary).name, "ci", "--no-audit", "--no-fund"],
        "return_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0 or not (dependency_root / "node_modules").is_dir():
        raise PathS06ExtensionError("npm ci failed for the frozen lockfile.")
    return dependency_root / "node_modules", record


def prepare_workspace(
    target: dict[str, Any],
    definition: dict[str, Any],
    project_root: Path,
    workspaces_root: Path,
    node_modules: Path,
) -> tuple[Path, dict[str, Any]]:
    workspace = workspaces_root / target["id"] / "app"
    workspace.mkdir(parents=True)
    baseline_root = resolve_inside(
        project_root, "benchmarks/primary/v1/path-traversal"
    )
    shutil.copy2(resolve_inside(project_root, target["source"]), workspace / "app.js")
    shutil.copy2(baseline_root / "package.json", workspace / "package.json")
    shutil.copy2(baseline_root / "package-lock.json", workspace / "package-lock.json")
    shutil.copytree(baseline_root / "public-files", workspace / "public-files")
    shutil.copytree(node_modules, workspace / "node_modules", symlinks=True)

    outside = workspace / "outside-zone"
    outside.mkdir()
    marker = definition["case"]["marker"]
    (outside / "outside-secret.txt").write_text(marker + "\n", encoding="utf-8")
    link = workspace / "public-files" / "link"
    fixture: dict[str, Any] = {
        "link": "public-files/link",
        "target": "../outside-zone",
        "symlink_created": False,
        "resolved_outside_allowed_root": None,
        "error": None,
    }
    try:
        link.symlink_to(Path("..") / "outside-zone", target_is_directory=True)
        fixture["symlink_created"] = link.is_symlink()
        allowed = (workspace / "public-files").resolve()
        resolved_target = (link / "outside-secret.txt").resolve()
        try:
            resolved_target.relative_to(allowed)
            fixture["resolved_outside_allowed_root"] = False
        except ValueError:
            fixture["resolved_outside_allowed_root"] = True
    except OSError as exc:
        fixture["error"] = str(exc)
    return workspace, fixture


def run_target(
    target: dict[str, Any],
    definition: dict[str, Any],
    project_root: Path,
    workspaces_root: Path,
    node_modules: Path,
    node_binary: str,
) -> dict[str, Any]:
    workspace, fixture = prepare_workspace(
        target, definition, project_root, workspaces_root, node_modules
    )
    base = {
        "schema_version": "0.1",
        "project": "FixProof",
        "protocol_id": PROTOCOL_ID,
        "case_id": CASE_ID,
        "recorded_at": utc_now(),
        "target": {
            "id": target["id"],
            "type": target["type"],
            "source": target["source"],
            "sha256": target["sha256"],
        },
        "fixture": fixture,
        "request": {
            "method": "GET",
            "path": "/file",
            "parameter": "name",
            "value": definition["case"]["value"],
        },
    }
    if not fixture["symlink_created"] or not fixture["resolved_outside_allowed_root"]:
        evaluation = {
            "status": "inconclusive",
            "reason": "The required outside-target symlink fixture was unavailable.",
            "marker_disclosed": False,
            "status_allowed": False,
        }
        return {
            **base,
            "response": response_record(None, "", error=fixture.get("error")),
            "evaluation": evaluation,
            "process": {"return_code": None, "stdout": "", "stderr": ""},
        }

    port = find_open_port()
    environment = os.environ.copy()
    environment["PORT"] = str(port)
    process = subprocess.Popen(
        [node_binary, "app.js"],
        cwd=workspace,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    response = response_record(None, "", error="Application did not execute.")
    process_error: str | None = None
    try:
        wait_for_application(process, port)
        response = send_request(port, definition["case"]["value"])
    except (OSError, PathS06ExtensionError) as exc:
        process_error = str(exc)
        response = response_record(None, "", error=process_error)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=5)

    marker = definition["case"]["marker"]
    evaluation = (
        evaluate_baseline_response(response, marker)
        if target["type"] == "baseline"
        else evaluate_candidate_response(response, marker)
    )
    return {
        **base,
        "response": response,
        "evaluation": evaluation,
        "process": {
            "return_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "error": process_error,
        },
    }


def environment_record(node_binary: str, npm_binary: str) -> dict[str, Any]:
    return {
        "recorded_at": utc_now(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "tools": {
            "node": command_version(node_binary),
            "npm": command_version(npm_binary),
        },
        "network": "loopback application requests; npm registry used only for npm ci",
        "model_calls": 0,
        "sast_runs": 0,
    }


def execute_extension(
    project_root: Path,
    *,
    node_binary: str,
    npm_binary: str,
) -> Path:
    if os.name != "posix" or platform.system() != "Linux":
        raise PathS06ExtensionError("PATH-S06 extension execution requires Linux.")
    definition = verify_protocol(project_root)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-path-s06-v1")
    runs_root = resolve_inside(project_root, DEFAULT_RUNS)
    run_directory = runs_root / run_id
    if run_directory.exists():
        raise PathS06ExtensionError(f"Run directory already exists: {run_directory}")
    run_directory.mkdir(parents=True)
    protected_before = protected_data_snapshot(project_root)
    state: dict[str, Any] = {
        "schema_version": "0.1",
        "project": "FixProof",
        "protocol_id": PROTOCOL_ID,
        "run_id": run_id,
        "started_at": utc_now(),
        "status": "running",
        "model_calls": 0,
        "sast_runs": 0,
    }
    write_json(run_directory / "run.json", state)

    try:
        environment = environment_record(node_binary, npm_binary)
        write_json(run_directory / "environment.json", environment)
        with tempfile.TemporaryDirectory(prefix="fixproof-path-s06-") as temp_name:
            temporary_root = Path(temp_name)
            node_modules, dependency = build_dependencies(
                definition, project_root, temporary_root, npm_binary
            )
            write_json(run_directory / "dependency-install.json", dependency)
            workspaces = temporary_root / "workspaces"
            workspaces.mkdir()
            targets = definition["targets"]
            baseline_target = next(row for row in targets if row["type"] == "baseline")
            baseline_result = run_target(
                baseline_target,
                definition,
                project_root,
                workspaces,
                node_modules,
                node_binary,
            )
            baseline_path = run_directory / "baseline" / "result.json"
            write_json(baseline_path, baseline_result)
            if baseline_result["evaluation"]["status"] != "pass":
                integrity = record_protected_data_integrity(
                    run_directory, project_root, protected_before
                )
                summary = {
                    "schema_version": "0.1",
                    "project": "FixProof",
                    "protocol_id": PROTOCOL_ID,
                    "run_id": run_id,
                    "status": "halted_baseline_gate",
                    "baseline": baseline_result["evaluation"],
                    "baseline_result": {
                        "result": str(baseline_path.relative_to(project_root)).replace(
                            "\\", "/"
                        ),
                        "sha256": sha256_file(baseline_path),
                    },
                    "candidate_counts": {"pass": 0, "fail": 0, "inconclusive": 0},
                    "candidate_results": [],
                    "protected_data_unchanged": integrity["unchanged"],
                }
                write_json(run_directory / "summary.json", summary)
                state.update({"status": "halted_baseline_gate", "completed_at": utc_now()})
                write_json(run_directory / "run.json", state)
                return run_directory

            candidate_results = []
            counts = {"pass": 0, "fail": 0, "inconclusive": 0}
            for target in (row for row in targets if row["type"] == "candidate"):
                result = run_target(
                    target,
                    definition,
                    project_root,
                    workspaces,
                    node_modules,
                    node_binary,
                )
                result_path = run_directory / "candidates" / target["id"] / "result.json"
                write_json(result_path, result)
                counts[result["evaluation"]["status"]] += 1
                candidate_results.append(
                    {
                        "target_id": target["id"],
                        "status": result["evaluation"]["status"],
                        "marker_disclosed": result["evaluation"]["marker_disclosed"],
                        "status_code": result["response"]["status_code"],
                        "result": str(result_path.relative_to(project_root)).replace("\\", "/"),
                        "sha256": sha256_file(result_path),
                    }
                )

        integrity = record_protected_data_integrity(
            run_directory, project_root, protected_before
        )
        summary = {
            "schema_version": "0.1",
            "project": "FixProof",
            "protocol_id": PROTOCOL_ID,
            "run_id": run_id,
            "status": "complete",
            "baseline": baseline_result["evaluation"],
            "baseline_result": {
                "result": str(baseline_path.relative_to(project_root)).replace(
                    "\\", "/"
                ),
                "sha256": sha256_file(baseline_path),
            },
            "candidate_counts": counts,
            "candidate_results": candidate_results,
            "protected_data_unchanged": integrity["unchanged"],
            "interpretation_boundary": (
                "Separate PATH-S06 extension evidence; not part of the 140 "
                "supplemental-v1 observations and not a human approval."
            ),
        }
        write_json(run_directory / "summary.json", summary)
        state.update({"status": "complete", "completed_at": utc_now()})
        write_json(run_directory / "run.json", state)
        return run_directory
    except Exception as exc:
        try:
            record_protected_data_integrity(
                run_directory, project_root, protected_before
            )
        except Exception:
            pass
        state.update(
            {
                "status": "infrastructure_error",
                "completed_at": utc_now(),
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }
        )
        write_json(run_directory / "run.json", state)
        raise


def verify_run(project_root: Path, run_id: str) -> dict[str, Any]:
    definition = verify_protocol(project_root)
    run_directory = resolve_inside(project_root, DEFAULT_RUNS / run_id)
    summary = read_json(run_directory / "summary.json")
    if summary.get("protocol_id") != PROTOCOL_ID or summary.get("run_id") != run_id:
        raise PathS06ExtensionError("Run summary identity mismatch.")
    if summary.get("status") != "complete":
        raise PathS06ExtensionError("The requested extension run is not complete.")
    baseline_binding = summary.get("baseline_result") or {}
    baseline_path = resolve_inside(project_root, baseline_binding.get("result", ""))
    if sha256_file(baseline_path) != baseline_binding.get("sha256"):
        raise PathS06ExtensionError("Baseline result binding changed.")
    baseline = read_json(baseline_path)
    if baseline.get("evaluation") != summary.get("baseline"):
        raise PathS06ExtensionError("Baseline result does not match the summary.")
    integrity = read_json(run_directory / "protected-data-integrity.json")
    if not integrity.get("unchanged") or not summary.get("protected_data_unchanged"):
        raise PathS06ExtensionError("Protected primary or supplemental data changed.")
    if integrity.get("after") != protected_data_snapshot(project_root):
        raise PathS06ExtensionError(
            "Protected data no longer matches the post-run fingerprint."
        )
    rows = summary.get("candidate_results") or []
    expected_ids = {
        row["id"] for row in definition["targets"] if row["type"] == "candidate"
    }
    if {row.get("target_id") for row in rows} != expected_ids:
        raise PathS06ExtensionError("Candidate result set does not match the freeze.")
    counts = {"pass": 0, "fail": 0, "inconclusive": 0}
    for row in rows:
        result_path = resolve_inside(project_root, row["result"])
        if sha256_file(result_path) != row.get("sha256"):
            raise PathS06ExtensionError(f"Result binding changed: {row['result']}")
        result = read_json(result_path)
        status = result.get("evaluation", {}).get("status")
        if status not in counts:
            raise PathS06ExtensionError(f"Unknown candidate status: {status}")
        counts[status] += 1
    if counts != summary.get("candidate_counts"):
        raise PathS06ExtensionError("Candidate summary counts do not recompute.")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run or verify the frozen Linux PATH-S06 extension."
    )
    parser.add_argument(
        "command", choices=("check-protocol", "run", "verify-run")
    )
    parser.add_argument("--project-root", type=Path, default=project_root_from_module())
    parser.add_argument("--node", default="node", help="Native Linux Node.js binary.")
    parser.add_argument("--npm", default="npm", help="Native Linux npm binary.")
    parser.add_argument("--run-id", help="Run ID required by verify-run.")
    args = parser.parse_args()
    project_root = args.project_root.resolve()

    if args.command == "check-protocol":
        definition = verify_protocol(project_root)
        print(
            f"PATH-S06 protocol verified: 1 baseline, "
            f"{sum(row['type'] == 'candidate' for row in definition['targets'])} candidates"
        )
        return
    if args.command == "run":
        run_directory = execute_extension(
            project_root, node_binary=args.node, npm_binary=args.npm
        )
        print(f"PATH-S06 extension run recorded: {run_directory}")
        return
    if not args.run_id:
        parser.error("--run-id is required for verify-run")
    summary = verify_run(project_root, args.run_id)
    counts = summary["candidate_counts"]
    print(
        "PATH-S06 run verified: "
        f"{counts['pass']} pass, {counts['fail']} fail, "
        f"{counts['inconclusive']} inconclusive"
    )


if __name__ == "__main__":
    try:
        main()
    except PathS06ExtensionError as exc:
        print(f"PATH-S06 extension error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
