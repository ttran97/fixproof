from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from fixproof.validation.browser_xss import (
    combine_xss_evidence,
    run_browser_xss_test,
)


# ---------------------------------------------------------
# MVP configuration
# ---------------------------------------------------------

HOST = "127.0.0.1"
PORT = 3000

STARTUP_TIMEOUT_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 5


EXPRESS_ROUTE_PATTERN = re.compile(
    r'\b(?:app|router)\.get'
    r'\s*\(\s*["\']([^"\']+)["\']'
)

QUERY_PARAMETER_PATTERN = re.compile(
    r'req\.query\.([A-Za-z_$][A-Za-z0-9_$]*)'
)


XSS_PAYLOADS = [
    {
        "name": "script_tag",
        "value": "<script>alert(1)</script>",
    },
    {
        "name": "img_event_handler",
        "value": "<img src=x onerror=alert(1)>",
    },
    {
        "name": "quote_svg_event",
        "value": "\"><svg onload=alert(1)>",
    },
    {
        "name": "consecutive_markup_characters",
        "value": "<<script>alert(1)//<</script>",
    },
]


SQLI_SECURITY_TESTS = [
    {
        "name": "legitimate_lookup_control",
        "test_type": "control",
        "value": "alice",
        "expected_usernames": ["alice"],
    },
    {
        "name": "boolean_or_injection",
        "test_type": "attack",
        "value": "' OR '1'='1",
        "expected_usernames": [],
    },
]


PATH_TRAVERSAL_SECURITY_TESTS = [
    {
        "name": "legitimate_file_control",
        "test_type": "control",
        "value": "welcome.txt",
        "expected_body": "FixProof public fixture: welcome",
        "forbidden_body": None,
    },
    {
        "name": "parent_directory_traversal",
        "test_type": "attack",
        "value": "../outside-secret.txt",
        "expected_body": None,
        "forbidden_body": "FIXPROOF_CONTROLLED_TRAVERSAL_SECRET",
    },
]


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def load_json(
    path: Path,
) -> dict[str, Any]:

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def find_context(
    context_data: dict[str, Any],
    canonical_id: str,
) -> dict[str, Any]:

    for context in context_data.get(
        "contexts",
        [],
    ):
        if (
            context.get("canonical_id")
            == canonical_id
        ):
            return context

    raise ValueError(
        f"Context not found for "
        f"{canonical_id}"
    )


def extract_route(
    context: dict[str, Any],
) -> str:

    code = context[
        "source_context"
    ].get(
        "code",
        "",
    )

    match = EXPRESS_ROUTE_PATTERN.search(
        code
    )

    if not match:
        raise ValueError(
            "Could not determine Express GET route "
            "from finding context."
        )

    return match.group(1)


def extract_query_parameter(
    context: dict[str, Any],
) -> str:

    code = context[
        "source_context"
    ].get(
        "code",
        "",
    )

    match = QUERY_PARAMETER_PATTERN.search(
        code
    )

    if not match:
        raise ValueError(
            "Could not determine request query "
            "parameter from finding context."
        )

    return match.group(1)


def port_is_open(
    host: str,
    port: int,
) -> bool:

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:

        sock.settimeout(0.5)

        return (
            sock.connect_ex(
                (host, port)
            )
            == 0
        )


def wait_for_application(
    process: subprocess.Popen,
    host: str,
    port: int,
    timeout_seconds: int,
) -> bool:

    deadline = (
        time.time()
        + timeout_seconds
    )

    while time.time() < deadline:

        # Application exited unexpectedly.
        if process.poll() is not None:
            return False

        if port_is_open(
            host,
            port,
        ):
            return True

        time.sleep(0.25)

    return False


def stop_application(
    process: subprocess.Popen,
) -> None:

    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(
            timeout=5
        )

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(
            timeout=5
        )


# ---------------------------------------------------------
# Application startup
# ---------------------------------------------------------

def start_candidate_application(
    workspace_dir: Path,
) -> tuple[
    subprocess.Popen,
    Path,
]:

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

    patch_info = workspace_metadata[
        "patch_workspace"
    ]

    candidate_source = Path(
        patch_info[
            "workspace_source"
        ]
    )

    original_source = Path(
        patch_info[
            "original_source"
        ]
    )

    if not candidate_source.exists():
        raise FileNotFoundError(
            f"Candidate source not found: "
            f"{candidate_source}"
        )

    original_node_modules = (
        original_source.parent
        / "node_modules"
    )

    if not original_node_modules.exists():
        raise FileNotFoundError(
            "Original application node_modules "
            "directory was not found. "
            "Run npm install in the original "
            "sample application first."
        )

    if port_is_open(
        HOST,
        PORT,
    ):
        raise RuntimeError(
            f"Port {PORT} is already in use. "
            "Stop the existing application "
            "before running security validation."
        )

    environment = os.environ.copy()

    existing_node_path = (
        environment.get(
            "NODE_PATH",
            "",
        )
    )

    node_paths = [
        str(
            original_node_modules.resolve()
        )
    ]

    if existing_node_path:
        node_paths.append(
            existing_node_path
        )

    environment[
        "NODE_PATH"
    ] = os.pathsep.join(
        node_paths
    )

    process = subprocess.Popen(
        [
            "node",
            str(candidate_source),
        ],
        cwd=str(
            candidate_source.parent
        ),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    started = wait_for_application(
        process=process,
        host=HOST,
        port=PORT,
        timeout_seconds=(
            STARTUP_TIMEOUT_SECONDS
        ),
    )

    if not started:

        stdout, stderr = (
            process.communicate(
                timeout=2
            )
            if process.poll()
            is not None
            else ("", "")
        )

        stop_application(
            process
        )

        raise RuntimeError(
            "Candidate application failed "
            "to start.\n"
            f"STDOUT:\n{stdout}\n"
            f"STDERR:\n{stderr}"
        )

    return (
        process,
        candidate_source,
    )


# ---------------------------------------------------------
# HTTP test helpers
# ---------------------------------------------------------

def send_request(
    route: str,
    parameter: str,
    payload: str,
) -> dict[str, Any]:

    query = urllib.parse.urlencode(
        {
            parameter: payload
        }
    )

    url = (
        f"http://{HOST}:{PORT}"
        f"{route}?{query}"
    )

    try:

        with urllib.request.urlopen(
            url,
            timeout=(
                REQUEST_TIMEOUT_SECONDS
            ),
        ) as response:

            body = response.read().decode(
                "utf-8",
                errors="replace",
            )

            return {
                "request_succeeded": True,
                "status_code": (
                    response.status
                ),
                "body": body,
                "error": None,
            }

    except urllib.error.HTTPError as exc:

        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        return {
            "request_succeeded": False,
            "status_code": exc.code,
            "body": body,
            "error": str(exc),
        }

    except Exception as exc:

        return {
            "request_succeeded": False,
            "status_code": None,
            "body": "",
            "error": str(exc),
        }


def extract_reflected_value(
    body: str,
) -> str | None:
    """
    Current controlled sample application returns:

        <h1>Hello USER_VALUE</h1>

    Extract only the user-controlled portion so that
    the legitimate <h1> markup is not confused with XSS.
    """

    prefix = "<h1>Hello "
    suffix = "</h1>"

    if not body.startswith(
        prefix
    ):
        return None

    if not body.endswith(
        suffix
    ):
        return None

    return body[
        len(prefix):
        -len(suffix)
    ]


# ---------------------------------------------------------
# XSS validation
# ---------------------------------------------------------

def evaluate_xss_response(
    payload: str,
    response: dict[str, Any],
) -> dict[str, Any]:

    if not response[
        "request_succeeded"
    ]:

        return {
            "status": "inconclusive",
            "reason": (
                "HTTP request failed."
            ),
            "reflected_value": None,
            "payload_reflected_verbatim": None,
            "raw_markup_present": None,
        }

    reflected_value = (
        extract_reflected_value(
            response["body"]
        )
    )

    if reflected_value is None:

        return {
            "status": "inconclusive",
            "reason": (
                "Could not identify the "
                "expected reflected response "
                "region."
            ),
            "reflected_value": None,
            "payload_reflected_verbatim": None,
            "raw_markup_present": None,
        }

    payload_reflected_verbatim = (
        payload in reflected_value
    )

    # In this endpoint the untrusted value is inserted
    # into HTML element content. Raw angle brackets in
    # that reflected value can create HTML elements.
    raw_markup_present = (
        "<" in reflected_value
        or ">" in reflected_value
    )

    if (
        payload_reflected_verbatim
        or raw_markup_present
    ):

        status = "fail"

        reason = (
            "User-controlled markup remained "
            "unescaped in the HTML response."
        )

    else:

        status = "pass"

        reason = (
            "No raw HTML markup from the "
            "payload remained in the reflected "
            "response value."
        )

    return {
        "status": status,
        "reason": reason,
        "reflected_value": (
            reflected_value
        ),
        "payload_reflected_verbatim": (
            payload_reflected_verbatim
        ),
        "raw_markup_present": (
            raw_markup_present
        ),
    }


def run_xss_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:

    test_results = []

    for test_case in XSS_PAYLOADS:

        print(
            f"Testing XSS payload: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        http_evaluation = (
            evaluate_xss_response(
                payload=test_case[
                    "value"
                ],
                response=response,
            )
        )

        browser_evaluation = run_browser_xss_test(
            host=HOST,
            port=PORT,
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        combined = combine_xss_evidence(
            http_evaluation=http_evaluation,
            browser_evaluation=browser_evaluation,
        )

        evaluation = {
            **http_evaluation,
            "http_status": http_evaluation["status"],
            "browser": browser_evaluation,
            "status": combined["status"],
            "reason": combined["reason"],
        }

        test_results.append(
            {
                "test": (
                    test_case["name"]
                ),
                "payload": (
                    test_case["value"]
                ),
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: "
            f"{evaluation['status']}"
        )

    return test_results


# ---------------------------------------------------------
# SQL injection validation
# ---------------------------------------------------------

def parse_json_rows(
    response: dict[str, Any],
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Parse the controlled JSON endpoint into a list of row objects."""

    if not response["request_succeeded"]:
        return None, "HTTP request failed."

    try:
        rows = json.loads(response["body"])
    except json.JSONDecodeError:
        return None, "Response body was not valid JSON."

    if not isinstance(rows, list):
        return None, "Response JSON was not an array."

    if not all(isinstance(row, dict) for row in rows):
        return None, "Response array contained a non-object row."

    return rows, None


def evaluate_sqli_security_response(
    test_type: str,
    expected_usernames: list[str],
    response: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate data exposure for the controlled SQLite endpoint."""

    rows, parse_error = parse_json_rows(response)

    if rows is None:
        return {
            "status": "inconclusive",
            "reason": parse_error,
            "expected_usernames": expected_usernames,
            "returned_usernames": None,
            "returned_rows": None,
        }

    usernames = [
        row.get("username")
        for row in rows
    ]

    if not all(
        isinstance(username, str)
        for username in usernames
    ):
        return {
            "status": "inconclusive",
            "reason": (
                "A returned row did not contain a string username."
            ),
            "expected_usernames": expected_usernames,
            "returned_usernames": usernames,
            "returned_rows": rows,
        }

    if test_type == "control":
        if usernames == expected_usernames:
            status = "pass"
            reason = (
                "The legitimate lookup returned only the expected user."
            )
        elif any(
            username not in expected_usernames
            for username in usernames
        ):
            status = "fail"
            reason = (
                "The legitimate lookup exposed an unexpected user."
            )
        else:
            status = "inconclusive"
            reason = (
                "The legitimate control lookup did not establish the "
                "expected endpoint behavior."
            )

    elif test_type == "attack":
        if usernames:
            status = "fail"
            reason = (
                "The SQL injection payload returned database users."
            )
        else:
            status = "pass"
            reason = (
                "The SQL injection payload did not return any users."
            )

    else:
        raise ValueError(
            f"Unsupported SQLi security test type: {test_type}"
        )

    return {
        "status": status,
        "reason": reason,
        "expected_usernames": expected_usernames,
        "returned_usernames": usernames,
        "returned_rows": rows,
    }


def run_sqli_security_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:
    """Run the fixed control and attack cases for CWE-89."""

    test_results = []

    for test_case in SQLI_SECURITY_TESTS:
        print(
            "Testing SQLi case: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        evaluation = evaluate_sqli_security_response(
            test_type=test_case["test_type"],
            expected_usernames=(
                test_case["expected_usernames"]
            ),
            response=response,
        )

        test_results.append(
            {
                "test": test_case["name"],
                "test_type": test_case["test_type"],
                "payload": test_case["value"],
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: {evaluation['status']}"
        )

    return test_results


# ---------------------------------------------------------
# Path traversal validation
# ---------------------------------------------------------

def evaluate_path_traversal_security_response(
    test_type: str,
    expected_body: str | None,
    forbidden_body: str | None,
    response: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate whether a request escaped the allowed file directory."""

    body = response.get("body", "")
    normalized_body = body.strip()

    if forbidden_body and forbidden_body in body:
        return {
            "status": "fail",
            "reason": (
                "The response disclosed the controlled file outside "
                "the allowed directory."
            ),
            "expected_body": expected_body,
            "forbidden_body": forbidden_body,
            "returned_body": body,
            "outside_file_disclosed": True,
        }

    if test_type == "control":
        if (
            response["request_succeeded"]
            and normalized_body == expected_body
        ):
            status = "pass"
            reason = (
                "The legitimate file request returned the expected "
                "public fixture."
            )
        else:
            status = "inconclusive"
            reason = (
                "The legitimate control request did not establish the "
                "expected public-file behavior."
            )

    elif test_type == "attack":
        status_code = response.get("status_code")

        if response["request_succeeded"]:
            status = "pass"
            reason = (
                "The traversal request did not disclose the controlled "
                "outside file."
            )
        elif status_code in {
            400,
            403,
            404,
        }:
            status = "pass"
            reason = (
                "The traversal request was rejected without disclosing "
                "the controlled outside file."
            )
        else:
            status = "inconclusive"
            reason = (
                "The traversal request failed for an unexpected reason."
            )

    else:
        raise ValueError(
            "Unsupported path-traversal security test type: "
            f"{test_type}"
        )

    return {
        "status": status,
        "reason": reason,
        "expected_body": expected_body,
        "forbidden_body": forbidden_body,
        "returned_body": body,
        "outside_file_disclosed": False,
    }


def run_path_traversal_security_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:
    """Run fixed legitimate and escaping path requests for CWE-22."""

    test_results = []

    for test_case in PATH_TRAVERSAL_SECURITY_TESTS:
        print(
            "Testing path-traversal case: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        evaluation = evaluate_path_traversal_security_response(
            test_type=test_case["test_type"],
            expected_body=test_case["expected_body"],
            forbidden_body=test_case["forbidden_body"],
            response=response,
        )

        test_results.append(
            {
                "test": test_case["name"],
                "test_type": test_case["test_type"],
                "payload": test_case["value"],
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: {evaluation['status']}"
        )

    return test_results


def determine_security_status(
    tests: list[dict[str, Any]],
) -> str:

    statuses = [
        test[
            "evaluation"
        ]["status"]
        for test in tests
    ]

    if "fail" in statuses:
        return "fail"

    if "inconclusive" in statuses:
        return "inconclusive"

    return "pass"


# ---------------------------------------------------------
# Main validation workflow
# ---------------------------------------------------------

def run_security_validation(
    contexts_file: Path,
    workspace_dir: Path,
    canonical_id: str,
    output_file: Path,
) -> dict[str, Any]:

    print("=" * 60)
    print(
        "FixProof Targeted Security Validation"
    )
    print("=" * 60)

    print(
        f"Canonical finding: {canonical_id}"
    )

    print()

    context_data = load_json(
        contexts_file
    )

    context = find_context(
        context_data=context_data,
        canonical_id=canonical_id,
    )

    cwe = context[
        "finding"
    ].get(
        "cwe"
    )

    if cwe not in {
        "CWE-22",
        "CWE-79",
        "CWE-89",
    }:

        raise NotImplementedError(
            "The current security validator "
            "supports CWE-22, CWE-79, and CWE-89 only. "
            f"Received: {cwe}"
        )

    route = extract_route(
        context
    )

    query_parameter = (
        extract_query_parameter(
            context
        )
    )

    print(
        f"CWE: {cwe}"
    )

    print(
        f"Route: {route}"
    )

    print(
        f"Input parameter: "
        f"{query_parameter}"
    )

    print()

    process = None
    result = None

    try:

        print(
            "[1/2] Starting isolated "
            "candidate application..."
        )

        process, candidate_source = (
            start_candidate_application(
                workspace_dir=(
                    workspace_dir
                )
            )
        )

        print(
            "Candidate application started."
        )

        print()

        print(
            "[2/2] Running targeted "
            f"{cwe} tests..."
        )

        if cwe == "CWE-79":
            tests = run_xss_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "cwe79_reflected_xss_browser"
            limitations = [
                (
                    "This controlled validator combines reflected-output "
                    "inspection with Playwright headless Chromium execution."
                ),
                (
                    "The validator is specific to reflected XSS in "
                    "HTML element content and the fixed payload suite."
                ),
            ]
        elif cwe == "CWE-89":
            tests = run_sqli_security_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "cwe89_sqlite_query_injection"
            limitations = [
                (
                    "This controlled validator checks one Boolean SQL "
                    "injection payload against a seeded SQLite dataset."
                ),
                (
                    "A passing result applies to this endpoint and does "
                    "not establish application-wide SQL injection safety."
                ),
            ]
        else:
            tests = run_path_traversal_security_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "cwe22_restricted_file_read"
            limitations = [
                (
                    "This controlled validator checks one parent-directory "
                    "traversal payload against one outside fixture."
                ),
                (
                    "A passing result applies to this endpoint and does "
                    "not establish application-wide filesystem safety."
                ),
            ]

        security_status = (
            determine_security_status(
                tests
            )
        )

        result = {
            "schema_version": "0.2",
            "project": "FixProof",

            "security_validation": {
                "canonical_id": (
                    canonical_id
                ),

                "validator": validator,

                "cwe": cwe,

                "target": {
                    "source": str(
                        candidate_source
                    ),
                    "route": route,
                    "query_parameter": (
                        query_parameter
                    ),
                },

                "status": (
                    security_status
                ),

                "test_count": len(
                    tests
                ),

                "tests": tests,

                "limitations": limitations,
            },
        }

    finally:

        if process is not None:

            print()
            print(
                "Stopping candidate "
                "application..."
            )

            stop_application(
                process
            )

    if result is None:
        raise RuntimeError(
            "Security validation did not produce a result."
        )

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
    print(
        "FixProof Security Validation Complete"
    )
    print("=" * 60)

    print(
        f"Security status: "
        f"{result['security_validation']['status']}"
    )

    print(
        f"Tests executed: "
        f"{result['security_validation']['test_count']}"
    )

    print(
        f"Report: {output_file}"
    )

    return result


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Run targeted FixProof runtime "
            "security validation against an "
            "isolated AI-generated patch."
        )
    )

    parser.add_argument(
        "--contexts",
        required=True,
        type=Path,
        help=(
            "FixProof remediation context JSON."
        ),
    )

    parser.add_argument(
        "--workspace",
        required=True,
        type=Path,
        help=(
            "Candidate FixProof workspace."
        ),
    )

    parser.add_argument(
        "--canonical-id",
        required=True,
        help=(
            "Canonical finding being validated."
        ),
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help=(
            "Security validation JSON output."
        ),
    )

    args = parser.parse_args()

    run_security_validation(
        contexts_file=(
            args.contexts.resolve()
        ),
        workspace_dir=(
            args.workspace.resolve()
        ),
        canonical_id=(
            args.canonical_id
        ),
        output_file=(
            args.output.resolve()
        ),
    )


if __name__ == "__main__":
    main()
