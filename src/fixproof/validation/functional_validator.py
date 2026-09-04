from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from fixproof.validation.security_validator import (
    extract_query_parameter,
    extract_reflected_value,
    extract_route,
    find_context,
    load_json,
    send_request,
    start_candidate_application,
    stop_application,
)


FUNCTIONAL_TESTS = [
    {
        "name": "simple_name",
        "value": "Tony",
    },
    {
        "name": "name_with_space",
        "value": "Tony Tran",
    },
    {
        "name": "ampersand_text",
        "value": "Tony & Alicia",
    },
    {
        "name": "single_markup_character",
        "value": "Tony < Alicia",
    },
    {
        "name": "adjacent_special_characters",
        "value": "Tony &<> Alicia",
    },
    {
        "name": "quote_and_markup",
        "value": "\"><hello>",
    },
]


SQLI_FUNCTIONAL_TESTS = [
    {
        "name": "alice_lookup",
        "value": "alice",
        "expected_rows": [
            {
                "id": 1,
                "username": "alice",
                "role": "user",
            }
        ],
    },
    {
        "name": "bob_lookup",
        "value": "bob",
        "expected_rows": [
            {
                "id": 2,
                "username": "bob",
                "role": "admin",
            }
        ],
    },
    {
        "name": "unknown_user_lookup",
        "value": "unknown-user",
        "expected_rows": [],
    },
]


PATH_TRAVERSAL_FUNCTIONAL_TESTS = [
    {
        "name": "welcome_file",
        "value": "welcome.txt",
        "expected_status": 200,
        "expected_body": "FixProof public fixture: welcome",
        "expected_json": None,
    },
    {
        "name": "guide_file",
        "value": "guide.txt",
        "expected_status": 200,
        "expected_body": "FixProof public fixture: guide",
        "expected_json": None,
    },
    {
        "name": "missing_file",
        "value": "missing.txt",
        "expected_status": 404,
        "expected_body": None,
        "expected_json": {
            "error": "File not found",
        },
    },
]


def evaluate_functional_response(
    expected_value: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify that the candidate preserves the user's intended
    displayed value.

    Security escaping may change the HTML representation:

        <  -> &lt;
        &  -> &amp;

    Therefore, compare the decoded visible value rather than
    requiring one specific encoding implementation.
    """

    if not response["request_succeeded"]:
        return {
            "status": "fail",
            "reason": "HTTP request failed.",
            "expected_value": expected_value,
            "reflected_value": None,
            "decoded_value": None,
            "semantic_match": False,
        }

    reflected_value = extract_reflected_value(
        response["body"]
    )

    if reflected_value is None:
        return {
            "status": "fail",
            "reason": (
                "Response did not preserve the expected "
                "Hello response structure."
            ),
            "expected_value": expected_value,
            "reflected_value": None,
            "decoded_value": None,
            "semantic_match": False,
        }

    # Convert HTML entities back into their displayed characters.
    #
    # Example:
    # Tony &amp; Alicia
    #
    # becomes:
    # Tony & Alicia
    decoded_value = html.unescape(
        reflected_value
    )

    semantic_match = (
        decoded_value == expected_value
    )

    if semantic_match:
        status = "pass"
        reason = (
            "The candidate preserved the expected "
            "user-visible value."
        )

    else:
        status = "fail"
        reason = (
            "The candidate changed or corrupted the "
            "expected user-visible value."
        )

    return {
        "status": status,
        "reason": reason,
        "expected_value": expected_value,
        "reflected_value": reflected_value,
        "decoded_value": decoded_value,
        "semantic_match": semantic_match,
    }


def run_functional_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:

    results = []

    for test_case in FUNCTIONAL_TESTS:

        print(
            f"Testing functional case: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        evaluation = (
            evaluate_functional_response(
                expected_value=(
                    test_case["value"]
                ),
                response=response,
            )
        )

        results.append(
            {
                "test": test_case["name"],
                "input": test_case["value"],
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: "
            f"{evaluation['status']}"
        )

        if evaluation[
            "status"
        ] == "fail":

            print(
                "  Expected: "
                f"{evaluation['expected_value']}"
            )

            print(
                "  Decoded: "
                f"{evaluation['decoded_value']}"
            )

    return results


def evaluate_sqli_functional_response(
    expected_rows: list[dict[str, Any]],
    response: dict[str, Any],
) -> dict[str, Any]:
    """Verify the controlled endpoint's legitimate JSON semantics."""

    if not response["request_succeeded"]:
        return {
            "status": "fail",
            "reason": "HTTP request failed.",
            "expected_rows": expected_rows,
            "actual_rows": None,
            "semantic_match": False,
        }

    try:
        actual_rows = json.loads(
            response["body"]
        )
    except json.JSONDecodeError:
        return {
            "status": "fail",
            "reason": "Response body was not valid JSON.",
            "expected_rows": expected_rows,
            "actual_rows": None,
            "semantic_match": False,
        }

    semantic_match = (
        isinstance(actual_rows, list)
        and actual_rows == expected_rows
    )

    if semantic_match:
        status = "pass"
        reason = (
            "The candidate preserved the expected query result."
        )
    else:
        status = "fail"
        reason = (
            "The candidate changed the expected query result."
        )

    return {
        "status": status,
        "reason": reason,
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "semantic_match": semantic_match,
    }


def run_sqli_functional_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:
    """Run fixed legitimate lookups for the controlled SQLi app."""

    results = []

    for test_case in SQLI_FUNCTIONAL_TESTS:
        print(
            "Testing SQLi functional case: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        evaluation = evaluate_sqli_functional_response(
            expected_rows=test_case["expected_rows"],
            response=response,
        )

        results.append(
            {
                "test": test_case["name"],
                "input": test_case["value"],
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: {evaluation['status']}"
        )

    return results


def evaluate_path_traversal_functional_response(
    expected_status: int,
    expected_body: str | None,
    expected_json: dict[str, Any] | None,
    response: dict[str, Any],
) -> dict[str, Any]:
    """Verify legitimate and missing-file response semantics."""

    status_match = (
        response.get("status_code")
        == expected_status
    )

    actual_body = response.get("body", "")
    actual_json = None

    if expected_json is not None:
        try:
            actual_json = json.loads(
                actual_body
            )
        except json.JSONDecodeError:
            actual_json = None

        content_match = (
            actual_json == expected_json
        )
    else:
        content_match = (
            actual_body.strip()
            == expected_body
        )

    semantic_match = (
        status_match
        and content_match
    )

    if semantic_match:
        status = "pass"
        reason = (
            "The candidate preserved the expected file response."
        )
    else:
        status = "fail"
        reason = (
            "The candidate changed the expected file response."
        )

    return {
        "status": status,
        "reason": reason,
        "expected_status": expected_status,
        "actual_status": response.get("status_code"),
        "expected_body": expected_body,
        "actual_body": actual_body,
        "expected_json": expected_json,
        "actual_json": actual_json,
        "semantic_match": semantic_match,
    }


def run_path_traversal_functional_tests(
    route: str,
    parameter: str,
) -> list[dict[str, Any]]:
    """Run the fixed public and missing-file cases for CWE-22."""

    results = []

    for test_case in PATH_TRAVERSAL_FUNCTIONAL_TESTS:
        print(
            "Testing file functional case: "
            f"{test_case['name']}"
        )

        response = send_request(
            route=route,
            parameter=parameter,
            payload=test_case["value"],
        )

        evaluation = evaluate_path_traversal_functional_response(
            expected_status=test_case["expected_status"],
            expected_body=test_case["expected_body"],
            expected_json=test_case["expected_json"],
            response=response,
        )

        results.append(
            {
                "test": test_case["name"],
                "input": test_case["value"],
                "http": response,
                "evaluation": evaluation,
            }
        )

        print(
            f"  Result: {evaluation['status']}"
        )

    return results


def determine_functional_status(
    tests: list[dict[str, Any]],
) -> str:

    if any(
        test["evaluation"]["status"]
        == "fail"
        for test in tests
    ):
        return "fail"

    return "pass"


def run_functional_validation(
    contexts_file: Path,
    workspace_dir: Path,
    canonical_id: str,
    output_file: Path,
) -> dict[str, Any]:

    print("=" * 60)
    print(
        "FixProof Functional Regression Validation"
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
            "The current functional validator supports "
            "CWE-22, CWE-79, and CWE-89 only. "
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
                workspace_dir=workspace_dir
            )
        )

        print(
            "Candidate application started."
        )

        print()

        print(
            "[2/2] Running functional "
            "regression tests..."
        )

        if cwe == "CWE-79":
            tests = run_functional_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "express_reflected_output"
            validation_property = (
                "The remediation must preserve the user-visible query "
                "parameter value while allowing safe HTML encoding."
            )
            limitations = [
                (
                    "This MVP functional validator is specific to the "
                    "controlled /hello Express endpoint."
                ),
                (
                    "It verifies response semantics rather than full "
                    "application behavior."
                ),
            ]
        elif cwe == "CWE-89":
            tests = run_sqli_functional_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "express_sqlite_user_lookup"
            validation_property = (
                "The remediation must preserve exact JSON results for "
                "legitimate and unknown username lookups."
            )
            limitations = [
                (
                    "This validator covers only three controlled lookup "
                    "cases against the seeded in-memory database."
                ),
                (
                    "It does not establish full application functional "
                    "correctness."
                ),
            ]
        else:
            tests = run_path_traversal_functional_tests(
                route=route,
                parameter=query_parameter,
            )
            validator = "express_restricted_file_lookup"
            validation_property = (
                "The remediation must preserve public-file contents and "
                "the existing missing-file 404 response."
            )
            limitations = [
                (
                    "This validator covers two public fixtures and one "
                    "missing-file case."
                ),
                (
                    "It does not establish full application functional "
                    "correctness."
                ),
            ]

        functional_status = (
            determine_functional_status(
                tests
            )
        )

        passed = sum(
            1
            for test in tests
            if test[
                "evaluation"
            ]["status"] == "pass"
        )

        failed = (
            len(tests)
            - passed
        )

        result = {
            "schema_version": "0.2",
            "project": "FixProof",

            "functional_validation": {
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
                    functional_status
                ),

                "summary": {
                    "tests": len(tests),
                    "passed": passed,
                    "failed": failed,
                },

                "tests": tests,

                "validation_property": validation_property,

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
            "Functional validation did not "
            "produce a result."
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
        "FixProof Functional Validation Complete"
    )
    print("=" * 60)

    print(
        "Functional status: "
        f"{result['functional_validation']['status']}"
    )

    print(
        "Tests passed: "
        f"{result['functional_validation']['summary']['passed']}"
    )

    print(
        "Tests failed: "
        f"{result['functional_validation']['summary']['failed']}"
    )

    print(
        f"Report: {output_file}"
    )

    return result


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Run FixProof functional regression "
            "validation against an isolated "
            "AI-generated remediation."
        )
    )

    parser.add_argument(
        "--contexts",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--workspace",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--canonical-id",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    run_functional_validation(
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
