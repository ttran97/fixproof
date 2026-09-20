from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fixproof.evaluation.supplemental_protocol import (
    DEFAULT_CASES,
    detect_environment,
    load_json,
    resolve_project_path,
    sha256_file,
    verify_definition,
    write_json,
)


HOST = "127.0.0.1"
STARTUP_TIMEOUT_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 5
BROWSER_TIMEOUT_MILLISECONDS = 5_000
BROWSER_SETTLE_MILLISECONDS = 250

OUTSIDE_MARKER = "FIXPROOF_CONTROLLED_TRAVERSAL_SECRET"
SIBLING_MARKER = "FIXPROOF_SUPPLEMENTAL_SIBLING_SECRET"
DOTFILE_CONTENT = "FixProof supplemental allowed fixture: ..notes.txt\n"
SPACEFILE_CONTENT = (
    "FixProof supplemental allowed fixture: annual report 2026.txt\n"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_run_id(kind: str, cwe: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{kind}-{cwe}"


def ensure_supplemental_output_root(
    project_root: Path,
    requested: Path,
) -> Path:
    root = project_root.resolve()
    output = (
        requested.resolve()
        if requested.is_absolute()
        else (root / requested).resolve()
    )
    allowed = (root / "data/supplemental/v1/runs").resolve()
    try:
        output.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(
            "Supplemental run output must stay under "
            "data/supplemental/v1/runs."
        ) from exc
    return output


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {"node_modules"} & set(names)


def prepare_disposable_app(
    source_app: Path,
    cwe: str,
    destination: Path,
) -> dict[str, Any]:
    source = source_app.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"Disposable app already exists: {destination}")

    source_hash = sha256_file(source / "app.js")
    shutil.copytree(source, destination, ignore=_copy_ignore)
    transformations: list[dict[str, Any]] = []
    fixture_status: dict[str, Any] = {}

    if cwe == "path-traversal":
        allowed_root = destination / "public-files"
        allowed_root.mkdir(parents=True, exist_ok=True)
        (allowed_root / "..notes.txt").write_bytes(
            DOTFILE_CONTENT.encode("utf-8")
        )
        (allowed_root / "annual report 2026.txt").write_bytes(
            SPACEFILE_CONTENT.encode("utf-8")
        )

        outside = destination / "outside-secret.txt"
        outside.write_bytes((OUTSIDE_MARKER + "\n").encode("utf-8"))
        sibling = destination / "public-files-evil"
        sibling.mkdir(parents=True, exist_ok=True)
        (sibling / "secret.txt").write_bytes(
            (SIBLING_MARKER + "\n").encode("utf-8")
        )

        link = allowed_root / "link"
        link_error = None
        try:
            link.symlink_to(destination, target_is_directory=True)
        except OSError as exc:
            link_error = str(exc)

        fixture_status = {
            "allowed_root": str(allowed_root),
            "outside_marker_path": str(outside),
            "sibling_marker_path": str(sibling / "secret.txt"),
            "symlink_path": str(link),
            "symlink_created": link.is_symlink(),
            "symlink_error": link_error,
        }
        transformations.append(
            {
                "type": "supplemental_path_fixture",
                "files": [
                    "public-files/..notes.txt",
                    "public-files/annual report 2026.txt",
                    "outside-secret.txt",
                    "public-files-evil/secret.txt",
                ],
                "symlink_created": link.is_symlink(),
            }
        )

    elif cwe == "sqli":
        app_file = destination / "app.js"
        source_text = app_file.read_text(encoding="utf-8")
        marker = "    statement.finalize();"
        if source_text.count(marker) != 1:
            raise ValueError(
                "Could not identify the deterministic SQL seed insertion point."
            )
        extra_seeds = (
            '    statement.run("o\'connor", "user");\n'
            '    statement.run("semi;colon", "user");\n'
            '    statement.run("zoë", "user");\n'
        )
        app_file.write_text(
            source_text.replace(marker, extra_seeds + marker, 1),
            encoding="utf-8",
        )
        transformations.append(
            {
                "type": "supplemental_sql_seed",
                "usernames": ["o'connor", "semi;colon", "zoë"],
            }
        )

    if sha256_file(source / "app.js") != source_hash:
        raise RuntimeError("Source application changed while making a copy.")

    return {
        "source_app": str(source),
        "source_app_sha256": source_hash,
        "disposable_app": str(destination),
        "disposable_app_sha256": sha256_file(destination / "app.js"),
        "transformations": transformations,
        "fixture_status": fixture_status,
    }


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def wait_for_application(
    process: subprocess.Popen[str],
    port: int,
) -> bool:
    deadline = time.time() + STARTUP_TIMEOUT_SECONDS
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            if sock.connect_ex((HOST, port)) == 0:
                return True
        time.sleep(0.1)
    return False


def start_application(
    node_path: str,
    app_dir: Path,
    dependency_dir: Path,
    port: int,
) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["PORT"] = str(port)
    existing_node_path = environment.get("NODE_PATH", "")
    node_paths = [str(dependency_dir.resolve())]
    if existing_node_path:
        node_paths.append(existing_node_path)
    environment["NODE_PATH"] = os.pathsep.join(node_paths)

    process = subprocess.Popen(
        [node_path, str((app_dir / "app.js").resolve())],
        cwd=str(app_dir.resolve()),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if not wait_for_application(process, port):
        stdout, stderr = stop_application(process)
        raise RuntimeError(
            "Disposable application failed to start.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
    return process


def stop_application(process: subprocess.Popen[str]) -> tuple[str, str]:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    stdout, stderr = process.communicate(timeout=2)
    return stdout, stderr


def build_urls(
    port: int,
    route: str,
    parameter: str,
    request: dict[str, Any],
    fixture_status: dict[str, Any],
) -> list[dict[str, str]]:
    base = f"http://{HOST}:{port}{route}"
    mode = request["mode"]
    if mode == "omit":
        return [{"label": "omitted", "url": base}]
    if mode == "pairs":
        pairs = [(str(key), str(value)) for key, value in request["pairs"]]
        query = urllib.parse.urlencode(pairs)
        return [{"label": "request", "url": f"{base}?{query}"}]
    if mode == "raw_query":
        return [{"label": "raw_query", "url": f"{base}?{request['query']}"}]
    if mode == "multiple":
        return [
            {
                "label": value,
                "url": f"{base}?{urllib.parse.urlencode({parameter: value})}",
            }
            for value in request["values"]
        ]
    if mode == "generated_absolute_paths":
        outside = Path(fixture_status["outside_marker_path"]).resolve()
        windows_value = str(outside)
        posix_value = "/" + outside.as_posix()
        return [
            {
                "label": "windows_absolute",
                "url": f"{base}?{urllib.parse.urlencode({parameter: windows_value})}",
            },
            {
                "label": "posix_absolute",
                "url": f"{base}?{urllib.parse.urlencode({parameter: posix_value})}",
            },
        ]
    if mode == "aggregate":
        return []
    raise ValueError(f"Unsupported supplemental request mode: {mode}")


def send_request(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            return {
                "status_code": response.status,
                "body": response.read().decode("utf-8", errors="replace"),
                "content_type": response.headers.get("Content-Type"),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status_code": exc.code,
            "body": exc.read().decode("utf-8", errors="replace"),
            "content_type": exc.headers.get("Content-Type"),
            "error": str(exc),
        }
    except (OSError, urllib.error.URLError) as exc:
        return {
            "status_code": None,
            "body": "",
            "content_type": None,
            "error": str(exc),
        }


def browser_observation(page: Any, url: str) -> dict[str, Any]:
    dialogs: list[dict[str, str]] = []
    page_errors: list[str] = []

    def on_dialog(dialog: Any) -> None:
        dialogs.append({"type": dialog.type, "message": dialog.message})
        dialog.dismiss()

    page.on("dialog", on_dialog)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    try:
        response = page.goto(
            url,
            wait_until="load",
            timeout=BROWSER_TIMEOUT_MILLISECONDS,
        )
        page.wait_for_timeout(BROWSER_SETTLE_MILLISECONDS)
        return {
            "status": "observed",
            "http_status": response.status if response else None,
            "dialogs": dialogs,
            "h1_count": page.locator("h1").count(),
            "h1_texts": page.locator("h1").all_text_contents(),
            "active_element_counts": {
                selector: page.locator(selector).count()
                for selector in ("script", "img", "svg", "input", "b")
            },
            "body_inner_html": page.locator("body").inner_html(),
            "page_errors": page_errors,
            "error": None,
        }
    except Exception as exc:  # Playwright exposes several environment errors.
        return {
            "status": "inconclusive",
            "http_status": None,
            "dialogs": dialogs,
            "h1_count": None,
            "h1_texts": None,
            "active_element_counts": None,
            "body_inner_html": None,
            "page_errors": page_errors,
            "error": str(exc),
        }


def run_xss_cases(
    case_definition: dict[str, Any],
    port: int,
    fixture_status: dict[str, Any],
    *,
    target_type: str = "baseline",
) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for test in case_definition["tests"]:
                if test["request"]["mode"] == "aggregate":
                    references = test["request"]["references"]
                    evidence = {
                        "references": references,
                        "referenced_results": [
                            next(
                                item
                                for item in results
                                if item["test_id"] == reference
                            )["evidence"]
                            for reference in references
                        ],
                    }
                else:
                    observations = []
                    for request in build_urls(
                        port,
                        case_definition["route"],
                        case_definition["parameter"],
                        test["request"],
                        fixture_status,
                    ):
                        page = browser.new_page()
                        try:
                            observations.append(
                                {
                                    **request,
                                    "http": send_request(request["url"]),
                                    "browser": browser_observation(
                                        page,
                                        request["url"],
                                    ),
                                }
                            )
                        finally:
                            page.close()
                    evidence = {"observations": observations}

                evaluation = evaluate_target_case(
                    target_type, "xss", test["id"], evidence
                )
                evaluation_field = f"{target_type}_expectation_evaluation"
                results.append(
                    {
                        "test_id": test["id"],
                        "category": test["category"],
                        "input": test["input"],
                        f"{target_type}_expectation": test[
                            f"{target_type}_expectation"
                        ],
                        "evidence": evidence,
                        evaluation_field: evaluation,
                    }
                )
        finally:
            browser.close()
    return results


def run_http_cases(
    cwe: str,
    case_definition: dict[str, Any],
    port: int,
    fixture_status: dict[str, Any],
    *,
    target_type: str = "baseline",
) -> list[dict[str, Any]]:
    results = []
    for test in case_definition["tests"]:
        if (
            test["id"] == "PATH-S06"
            and not fixture_status.get("symlink_created")
        ):
            evidence = {
                "observations": [],
                "fixture_unavailable": True,
                "reason": fixture_status.get("symlink_error"),
            }
        else:
            evidence = {
                "observations": [
                    {
                        **request,
                        "http": send_request(request["url"]),
                    }
                    for request in build_urls(
                        port,
                        case_definition["route"],
                        case_definition["parameter"],
                        test["request"],
                        fixture_status,
                    )
                ]
            }
        evaluation_field = f"{target_type}_expectation_evaluation"
        results.append(
            {
                "test_id": test["id"],
                "category": test["category"],
                "input": test["input"],
                f"{target_type}_expectation": test[
                    f"{target_type}_expectation"
                ],
                "evidence": evidence,
                evaluation_field: evaluate_target_case(
                    target_type, cwe, test["id"], evidence
                ),
            }
        )
    return results


def _only_observation(evidence: dict[str, Any]) -> dict[str, Any] | None:
    observations = evidence.get("observations", [])
    return observations[0] if len(observations) == 1 else None


def _json_body(observation: dict[str, Any]) -> Any:
    try:
        return json.loads(observation["http"]["body"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _evaluation(matches: bool, reason: str) -> dict[str, str]:
    return {
        "status": "match" if matches else "mismatch",
        "reason": reason,
    }


def _candidate_evaluation(
    matches: bool,
    reason: str,
    *,
    inconclusive: bool = False,
) -> dict[str, str]:
    return {
        "status": "inconclusive" if inconclusive else (
            "pass" if matches else "fail"
        ),
        "reason": reason,
    }


def evaluate_target_case(
    target_type: str,
    cwe: str,
    test_id: str,
    evidence: dict[str, Any],
) -> dict[str, str]:
    if target_type == "baseline":
        return evaluate_baseline_case(cwe, test_id, evidence)
    if target_type == "candidate":
        return evaluate_candidate_case(cwe, test_id, evidence)
    raise ValueError(f"Unknown supplemental target type: {target_type}")


def evaluate_baseline_case(
    cwe: str,
    test_id: str,
    evidence: dict[str, Any],
) -> dict[str, str]:
    if evidence.get("fixture_unavailable"):
        return {
            "status": "inconclusive",
            "reason": "Required symlink or junction fixture was unavailable.",
        }

    if cwe == "xss":
        if test_id == "XSS-S03":
            referenced = evidence.get("referenced_results", [])
            matches = len(referenced) == 2 and all(
                item.get("observations")
                and item["observations"][0]["browser"].get("dialogs")
                and sum(
                    item["observations"][0]["browser"].get(
                        "active_element_counts", {}
                    ).values()
                )
                > 0
                for item in referenced
            )
            return _evaluation(
                matches,
                "Both registered attacks altered the vulnerable baseline DOM "
                "and executed." if matches else
                "One or more registered baseline attacks did not produce the "
                "expected DOM/execution evidence.",
            )

        observation = _only_observation(evidence)
        if observation is None:
            return _evaluation(False, "Expected one browser observation.")
        browser = observation["browser"]
        if browser.get("status") != "observed":
            return {
                "status": "inconclusive",
                "reason": browser.get("error") or "Browser evidence unavailable.",
            }
        expected_text = {
            "XSS-P01": "Hello undefined",
            "XSS-P02": "Hello ",
            "XSS-P03": "Hello Tony,Admin",
            "XSS-P04": "Hello Zoë 漢字 😀",
            "XSS-P05": "Hello O'Reilly `admin`",
            "XSS-R01": "Hello <b>Tony</b>",
        }
        if test_id in expected_text:
            matches = (
                browser.get("http_status") == 200
                and browser.get("h1_texts") == [expected_text[test_id]]
            )
            return _evaluation(
                matches,
                f"Expected one h1 with text {expected_text[test_id]!r}.",
            )
        selector = "script" if test_id == "XSS-S01" else "img"
        matches = bool(browser.get("dialogs")) and (
            browser.get("active_element_counts", {}).get(selector, 0) > 0
        )
        return _evaluation(
            matches,
            f"Expected controlled dialog execution and an injected {selector}.",
        )

    observation = _only_observation(evidence)
    if cwe == "path-traversal":
        if test_id == "PATH-S04":
            observations = evidence.get("observations", [])
            return _evaluation(
                len(observations) == 2
                and all(item["http"]["status_code"] is not None for item in observations),
                "Expected two characterized absolute-path responses.",
            )
        if observation is None:
            return _evaluation(False, "Expected one HTTP observation.")
        response = observation["http"]
        body = response["body"]
        if test_id == "PATH-P01":
            return _evaluation(
                response["status_code"] == 200 and body == DOTFILE_CONTENT,
                "Expected the in-root ..notes.txt fixture.",
            )
        if test_id == "PATH-P02":
            return _evaluation(
                response["status_code"] == 200 and body == SPACEFILE_CONTENT,
                "Expected the in-root spaced filename fixture.",
            )
        if test_id in {"PATH-R01", "PATH-R02", "PATH-R03"}:
            return _evaluation(
                response["status_code"] is not None
                and OUTSIDE_MARKER not in body
                and SIBLING_MARKER not in body,
                "Baseline malformed-input behavior was characterized without "
                "disclosing a marker.",
            )
        if test_id in {"PATH-S01", "PATH-S03", "PATH-S06"}:
            return _evaluation(
                response["status_code"] == 200 and OUTSIDE_MARKER in body,
                "Expected the vulnerable baseline to disclose the outside marker.",
            )
        if test_id == "PATH-S02":
            return _evaluation(
                OUTSIDE_MARKER not in body,
                "Expected one decoding pass to leave a nondisclosing literal name.",
            )
        if test_id == "PATH-S05":
            return _evaluation(
                response["status_code"] == 200 and SIBLING_MARKER in body,
                "Expected the vulnerable baseline to disclose the sibling marker.",
            )

    if cwe == "sqli":
        if test_id == "SQL-R03":
            observations = evidence.get("observations", [])
            expected = {"semi;colon", "zoë"}
            observed = set()
            for item in observations:
                rows = _json_body(item)
                if (
                    item["http"]["status_code"] == 200
                    and isinstance(rows, list)
                    and len(rows) == 1
                ):
                    observed.add(rows[0].get("username"))
            return _evaluation(
                observed == expected,
                "Expected exact rows for both seeded punctuation/Unicode users.",
            )
        if observation is None:
            return _evaluation(False, "Expected one HTTP observation.")
        response = observation["http"]
        rows = _json_body(observation)
        if test_id in {"SQL-P01", "SQL-P02"}:
            return _evaluation(
                response["status_code"] == 200 and rows == [],
                "Expected HTTP 200 with an empty array.",
            )
        if test_id == "SQL-R01":
            return _evaluation(
                response["status_code"] is not None,
                "Repeated-parameter baseline behavior was characterized.",
            )
        if test_id == "SQL-R02":
            return _evaluation(
                response["status_code"] == 500,
                "Expected raw query construction to fail on the apostrophe.",
            )
        if test_id == "SQL-S01":
            usernames = [row.get("username") for row in rows or []]
            return _evaluation(
                response["status_code"] == 200 and usernames == ["alice"],
                "Expected comment injection to return Alice.",
            )
        if test_id == "SQL-S02":
            usernames = {row.get("username") for row in rows or []}
            return _evaluation(
                response["status_code"] == 200
                and usernames
                == {"alice", "bob", "charlie", "o'connor", "semi;colon", "zoë"},
                "Expected Boolean injection to return all six seeded users.",
            )
        if test_id == "SQL-S03":
            usernames = [row.get("username") for row in rows or []]
            return _evaluation(
                response["status_code"] == 200 and usernames == ["synthetic"],
                "Expected UNION injection to return the synthetic row.",
            )

    raise ValueError(f"No baseline oracle registered for {cwe}/{test_id}.")


def evaluate_candidate_case(
    cwe: str,
    test_id: str,
    evidence: dict[str, Any],
) -> dict[str, str]:
    if evidence.get("fixture_unavailable"):
        return _candidate_evaluation(
            False,
            "Required symlink or junction fixture was unavailable.",
            inconclusive=True,
        )

    if cwe == "xss":
        if test_id == "XSS-S03":
            referenced = evidence.get("referenced_results", [])
            safe = len(referenced) == 2
            for item in referenced:
                observations = item.get("observations", [])
                if len(observations) != 1:
                    safe = False
                    continue
                browser = observations[0]["browser"]
                counts = browser.get("active_element_counts") or {}
                safe = safe and (
                    browser.get("status") == "observed"
                    and not browser.get("dialogs")
                    and browser.get("h1_count") == 1
                    and sum(counts.values()) == 0
                )
            return _candidate_evaluation(
                safe,
                "Expected both attack cases to retain one heading with no "
                "dialog or attacker-created active element.",
            )

        observation = _only_observation(evidence)
        if observation is None:
            return _candidate_evaluation(
                False,
                "Expected one browser observation.",
                inconclusive=True,
            )
        browser = observation["browser"]
        if browser.get("status") != "observed":
            return _candidate_evaluation(
                False,
                browser.get("error") or "Browser evidence unavailable.",
                inconclusive=True,
            )

        expected_text = {
            "XSS-P01": "Hello undefined",
            "XSS-P02": "Hello ",
            "XSS-P03": "Hello Tony,Admin",
            "XSS-P04": "Hello Zoë 漢字 😀",
            "XSS-P05": "Hello O'Reilly `admin`",
            "XSS-R01": "Hello &lt;b&gt;Tony&lt;/b&gt;",
        }
        if test_id in expected_text:
            counts = browser.get("active_element_counts") or {}
            safe_structure = (
                not browser.get("dialogs")
                and sum(counts.values()) == 0
                and browser.get("h1_count") == 1
            )
            matches = (
                browser.get("http_status") == 200
                and browser.get("h1_texts") == [expected_text[test_id]]
                and safe_structure
            )
            return _candidate_evaluation(
                matches,
                f"Expected one safe h1 with text {expected_text[test_id]!r}.",
            )

        selector = "script" if test_id == "XSS-S01" else "img"
        counts = browser.get("active_element_counts") or {}
        matches = (
            browser.get("http_status") == 200
            and not browser.get("dialogs")
            and counts.get(selector, 0) == 0
            and browser.get("h1_count") == 1
        )
        return _candidate_evaluation(
            matches,
            f"Expected no dialog or injected {selector} and one greeting h1.",
        )

    observation = _only_observation(evidence)
    if cwe == "path-traversal":
        if test_id == "PATH-S04":
            observations = evidence.get("observations", [])
            safe = len(observations) == 2 and all(
                item["http"]["status_code"] not in {None, 500}
                and OUTSIDE_MARKER not in item["http"]["body"]
                for item in observations
            )
            return _candidate_evaluation(
                safe,
                "Expected both absolute-path variants to avoid the marker and "
                "HTTP 500.",
            )
        if observation is None:
            return _candidate_evaluation(
                False,
                "Expected one HTTP observation.",
                inconclusive=True,
            )
        response = observation["http"]
        body = response["body"]
        if test_id == "PATH-P01":
            return _candidate_evaluation(
                response["status_code"] == 200 and body == DOTFILE_CONTENT,
                "Expected the legitimate in-root ..notes.txt contents.",
            )
        if test_id == "PATH-P02":
            return _candidate_evaluation(
                response["status_code"] == 200 and body == SPACEFILE_CONTENT,
                "Expected the legitimate in-root spaced filename contents.",
            )
        if test_id in {"PATH-R01", "PATH-R02", "PATH-R03"}:
            error_json = _json_body(observation)
            conforms = (
                response["status_code"] == 400
                and isinstance(error_json, dict)
                and isinstance(error_json.get("error"), str)
                and "stack" not in body.lower()
            )
            return _candidate_evaluation(
                conforms,
                "Expected HTTP 400 with a stable JSON error and no stack trace.",
            )
        safe = (
            response["status_code"] not in {None, 500}
            and OUTSIDE_MARKER not in body
            and SIBLING_MARKER not in body
        )
        return _candidate_evaluation(
            safe,
            "Expected no outside/sibling marker and no HTTP 500.",
        )

    if cwe == "sqli":
        if test_id == "SQL-R03":
            observations = evidence.get("observations", [])
            expected = {"semi;colon", "zoë"}
            observed = set()
            valid = len(observations) == 2
            for item in observations:
                rows = _json_body(item)
                if (
                    item["http"]["status_code"] == 200
                    and isinstance(rows, list)
                    and len(rows) == 1
                    and rows[0].get("role") == "user"
                ):
                    observed.add(rows[0].get("username"))
                else:
                    valid = False
            return _candidate_evaluation(
                valid and observed == expected,
                "Expected exact rows for the punctuation and Unicode users.",
            )
        if observation is None:
            return _candidate_evaluation(
                False,
                "Expected one HTTP observation.",
                inconclusive=True,
            )
        response = observation["http"]
        rows = _json_body(observation)
        if test_id in {"SQL-P01", "SQL-P02"}:
            return _candidate_evaluation(
                response["status_code"] == 200 and rows == [],
                "Expected HTTP 200 with an empty array.",
            )
        if test_id == "SQL-R01":
            error_json = rows
            return _candidate_evaluation(
                response["status_code"] == 400
                and isinstance(error_json, dict)
                and isinstance(error_json.get("error"), str),
                "Expected HTTP 400 with a stable JSON error.",
            )
        if test_id == "SQL-R02":
            matches = (
                response["status_code"] == 200
                and isinstance(rows, list)
                and len(rows) == 1
                and rows[0].get("username") == "o'connor"
                and rows[0].get("role") == "user"
            )
            return _candidate_evaluation(
                matches,
                "Expected exactly the seeded o'connor user row.",
            )
        if test_id in {"SQL-S01", "SQL-S02", "SQL-S03"}:
            return _candidate_evaluation(
                response["status_code"] == 200 and rows == [],
                "Expected HTTP 200 with zero rows for the attack input.",
            )

    raise ValueError(f"No candidate oracle registered for {cwe}/{test_id}.")


def run_baseline(
    project_root: Path,
    cwe: str,
    output_root: Path,
) -> tuple[Path, dict[str, Any]]:
    root = project_root.resolve()
    definition = verify_definition(root)
    environment = detect_environment(root)
    if not environment["ready_for_live_supplemental_execution"]:
        raise RuntimeError(
            "Supplemental environment is not ready: "
            + ", ".join(environment["blockers"])
        )

    manifest = load_json(resolve_project_path(root, str(DEFAULT_CASES)))
    case_definition = manifest["cwes"][cwe]
    run_id = make_run_id("baseline", cwe)
    runs_root = ensure_supplemental_output_root(root, output_root)
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    result_path = run_dir / "result.json"
    started_at = utc_now()

    result: dict[str, Any] = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_baseline_characterization",
        "protocol_id": "supplemental-v1",
        "run_id": run_id,
        "target_type": "baseline",
        "cwe_case": cwe,
        "started_at": started_at,
        "status": "running",
        "definition": definition,
        "environment": environment,
    }
    write_json(result_path, result)

    process: subprocess.Popen[str] | None = None
    process_logs = {"stdout": "", "stderr": ""}
    try:
        with tempfile.TemporaryDirectory(
            prefix=f"fixproof-supplemental-{cwe}-"
        ) as temporary:
            source_app = resolve_project_path(root, case_definition["baseline"])
            disposable_app = Path(temporary) / "app"
            preparation = prepare_disposable_app(
                source_app,
                cwe,
                disposable_app,
            )
            port = find_free_port()
            dependency_dir = source_app / "node_modules"
            process = start_application(
                environment["node"],
                disposable_app,
                dependency_dir,
                port,
            )
            if cwe == "xss":
                cases = run_xss_cases(
                    case_definition,
                    port,
                    preparation["fixture_status"],
                )
            else:
                cases = run_http_cases(
                    cwe,
                    case_definition,
                    port,
                    preparation["fixture_status"],
                )

            process_logs["stdout"], process_logs["stderr"] = stop_application(
                process
            )
            process = None

            statuses = [
                case["baseline_expectation_evaluation"]["status"]
                for case in cases
            ]
            mismatches = statuses.count("mismatch")
            inconclusive = statuses.count("inconclusive")
            result.update(
                {
                    "finished_at": utc_now(),
                    "status": (
                        "baseline_expectation_mismatch"
                        if mismatches
                        else "baseline_characterized"
                    ),
                    "port": port,
                    "preparation": preparation,
                    "cases": cases,
                    "summary": {
                        "registered": len(cases),
                        "matched": statuses.count("match"),
                        "mismatched": mismatches,
                        "inconclusive": inconclusive,
                        "candidate_execution_permitted": mismatches == 0,
                    },
                    "process": process_logs,
                }
            )
    except Exception as exc:
        if process is not None:
            process_logs["stdout"], process_logs["stderr"] = stop_application(
                process
            )
        result.update(
            {
                "finished_at": utc_now(),
                "status": "execution_error",
                "error": str(exc),
                "process": process_logs,
            }
        )

    write_json(result_path, result)
    return result_path, result


def latest_successful_baseline(
    project_root: Path,
    cwe: str,
) -> dict[str, str]:
    runs = project_root.resolve() / "data/supplemental/v1/runs"
    candidates = sorted(
        runs.glob(f"*-baseline-{cwe}/result.json"),
        reverse=True,
    )
    for path in candidates:
        result = load_json(path)
        summary = result.get("summary", {})
        if (
            result.get("protocol_id") == "supplemental-v1"
            and result.get("status") == "baseline_characterized"
            and summary.get("mismatched") == 0
            and summary.get("candidate_execution_permitted") is True
        ):
            return {
                "path": str(path.relative_to(project_root.resolve())).replace(
                    "\\", "/"
                ),
                "sha256": sha256_file(path),
                "run_id": result["run_id"],
            }
    raise FileNotFoundError(
        f"No successful supplemental baseline gate exists for {cwe}."
    )


def summarize_candidate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    category_summary: dict[str, dict[str, int]] = {}
    statuses: list[str] = []
    for case in cases:
        status = case["candidate_expectation_evaluation"]["status"]
        statuses.append(status)
        category = case["category"]
        counts = category_summary.setdefault(
            category,
            {"total": 0, "pass": 0, "fail": 0, "inconclusive": 0},
        )
        counts["total"] += 1
        counts[status] += 1

    return {
        "registered": len(cases),
        "pass": statuses.count("pass"),
        "fail": statuses.count("fail"),
        "inconclusive": statuses.count("inconclusive"),
        "by_category": category_summary,
        "automatic_acceptance": False,
    }


def run_candidate(
    project_root: Path,
    cwe: str,
    case_definition: dict[str, Any],
    candidate: dict[str, Any],
    environment: dict[str, Any],
    baseline_binding: dict[str, str],
    candidate_dir: Path,
) -> dict[str, Any]:
    attempt = int(candidate["attempt"])
    result_path = candidate_dir / "result.json"
    candidate_dir.mkdir(parents=True, exist_ok=False)
    result: dict[str, Any] = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_candidate_evaluation",
        "protocol_id": "supplemental-v1",
        "target_type": "saved_primary_candidate",
        "cwe_case": cwe,
        "attempt": attempt,
        "started_at": utc_now(),
        "status": "running",
        "baseline_gate": baseline_binding,
        "environment": environment,
    }
    write_json(result_path, result)

    process: subprocess.Popen[str] | None = None
    process_logs = {"stdout": "", "stderr": ""}
    try:
        with tempfile.TemporaryDirectory(
            prefix=f"fixproof-supplemental-{cwe}-attempt-{attempt:02d}-"
        ) as temporary:
            source_app = resolve_project_path(project_root, candidate["app"])
            disposable_app = Path(temporary) / "app"
            preparation = prepare_disposable_app(
                source_app,
                cwe,
                disposable_app,
            )
            port = find_free_port()
            dependency_dir = resolve_project_path(
                project_root,
                case_definition["baseline"],
            ) / "node_modules"
            process = start_application(
                environment["node"],
                disposable_app,
                dependency_dir,
                port,
            )
            if cwe == "xss":
                cases = run_xss_cases(
                    case_definition,
                    port,
                    preparation["fixture_status"],
                    target_type="candidate",
                )
            else:
                cases = run_http_cases(
                    cwe,
                    case_definition,
                    port,
                    preparation["fixture_status"],
                    target_type="candidate",
                )
            process_logs["stdout"], process_logs["stderr"] = stop_application(
                process
            )
            process = None
            result.update(
                {
                    "finished_at": utc_now(),
                    "status": "candidate_evaluated",
                    "port": port,
                    "preparation": preparation,
                    "cases": cases,
                    "summary": summarize_candidate_cases(cases),
                    "process": process_logs,
                }
            )
    except Exception as exc:
        if process is not None:
            process_logs["stdout"], process_logs["stderr"] = stop_application(
                process
            )
        result.update(
            {
                "finished_at": utc_now(),
                "status": "execution_error",
                "error": str(exc),
                "process": process_logs,
            }
        )

    write_json(result_path, result)
    return result


def run_candidates(
    project_root: Path,
    cwe: str,
    output_root: Path,
) -> tuple[Path, dict[str, Any]]:
    root = project_root.resolve()
    definition = verify_definition(root)
    environment = detect_environment(root)
    if not environment["ready_for_live_supplemental_execution"]:
        raise RuntimeError(
            "Supplemental environment is not ready: "
            + ", ".join(environment["blockers"])
        )
    baseline_binding = latest_successful_baseline(root, cwe)
    manifest = load_json(resolve_project_path(root, str(DEFAULT_CASES)))
    case_definition = manifest["cwes"][cwe]

    run_id = make_run_id("candidates", cwe)
    runs_root = ensure_supplemental_output_root(root, output_root)
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    candidate_results = []
    for candidate in case_definition["candidates"]:
        candidate_results.append(
            run_candidate(
                root,
                cwe,
                case_definition,
                candidate,
                environment,
                baseline_binding,
                run_dir / f"attempt-{int(candidate['attempt']):02d}",
            )
        )

    summary_rows = []
    for result in candidate_results:
        summary_rows.append(
            {
                "attempt": result["attempt"],
                "status": result["status"],
                **result.get(
                    "summary",
                    {"registered": 0, "pass": 0, "fail": 0, "inconclusive": 0},
                ),
            }
        )
    group_result = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_candidate_group_summary",
        "protocol_id": "supplemental-v1",
        "run_id": run_id,
        "cwe_case": cwe,
        "started_at": started_at,
        "finished_at": utc_now(),
        "status": (
            "completed"
            if all(row["status"] == "candidate_evaluated" for row in summary_rows)
            else "completed_with_execution_errors"
        ),
        "definition": definition,
        "environment": environment,
        "baseline_gate": baseline_binding,
        "candidates": summary_rows,
        "candidate_count": len(summary_rows),
        "automatic_acceptance": False,
    }
    summary_path = run_dir / "summary.json"
    write_json(summary_path, group_result)
    return summary_path, group_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run frozen FixProof supplemental baseline or saved-candidate "
            "evaluation in disposable local workspaces."
        )
    )
    parser.add_argument("command", choices=("baseline", "candidates"))
    parser.add_argument(
        "--cwe",
        required=True,
        choices=("xss", "path-traversal", "sqli"),
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/supplemental/v1/runs"),
    )
    args = parser.parse_args()

    if args.command == "baseline":
        result_path, result = run_baseline(
            args.project_root,
            args.cwe,
            args.output_root,
        )
        print(f"Supplemental baseline result: {result_path}")
        print(json.dumps(result.get("summary", {}), indent=2))
        if result["status"] != "baseline_characterized":
            raise SystemExit(2)
    else:
        result_path, result = run_candidates(
            args.project_root,
            args.cwe,
            args.output_root,
        )
        print(f"Supplemental candidate summary: {result_path}")
        print(json.dumps(result.get("candidates", []), indent=2))
        if result["status"] != "completed":
            raise SystemExit(2)


if __name__ == "__main__":
    main()
