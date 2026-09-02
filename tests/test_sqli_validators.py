from __future__ import annotations

import json
import unittest

from fixproof.validation.functional_validator import (
    evaluate_sqli_functional_response,
)
from fixproof.validation.security_validator import (
    determine_security_status,
    evaluate_sqli_security_response,
)


def successful_response(body: object) -> dict:
    return {
        "request_succeeded": True,
        "status_code": 200,
        "body": json.dumps(body),
        "error": None,
    }


class SqliSecurityValidatorTests(unittest.TestCase):
    def test_parameterized_injection_result_passes(self) -> None:
        evaluation = evaluate_sqli_security_response(
            test_type="attack",
            expected_usernames=[],
            response=successful_response([]),
        )

        self.assertEqual(evaluation["status"], "pass")
        self.assertEqual(evaluation["returned_usernames"], [])

    def test_exposed_users_fail(self) -> None:
        evaluation = evaluate_sqli_security_response(
            test_type="attack",
            expected_usernames=[],
            response=successful_response(
                [
                    {"id": 1, "username": "alice", "role": "user"},
                    {"id": 2, "username": "bob", "role": "admin"},
                ]
            ),
        )

        self.assertEqual(evaluation["status"], "fail")
        self.assertEqual(
            evaluation["returned_usernames"],
            ["alice", "bob"],
        )

    def test_broken_control_is_inconclusive(self) -> None:
        evaluation = evaluate_sqli_security_response(
            test_type="control",
            expected_usernames=["alice"],
            response=successful_response([]),
        )

        self.assertEqual(evaluation["status"], "inconclusive")
        self.assertEqual(
            determine_security_status(
                [{"evaluation": evaluation}]
            ),
            "inconclusive",
        )


class SqliFunctionalValidatorTests(unittest.TestCase):
    def test_expected_rows_pass(self) -> None:
        expected = [
            {"id": 1, "username": "alice", "role": "user"}
        ]

        evaluation = evaluate_sqli_functional_response(
            expected_rows=expected,
            response=successful_response(expected),
        )

        self.assertEqual(evaluation["status"], "pass")
        self.assertTrue(evaluation["semantic_match"])

    def test_changed_rows_fail(self) -> None:
        evaluation = evaluate_sqli_functional_response(
            expected_rows=[],
            response=successful_response(
                [{"id": 3, "username": "charlie", "role": "user"}]
            ),
        )

        self.assertEqual(evaluation["status"], "fail")
        self.assertFalse(evaluation["semantic_match"])


if __name__ == "__main__":
    unittest.main()
