from __future__ import annotations

import json
import unittest

from fixproof.validation.functional_validator import (
    evaluate_path_traversal_functional_response,
)
from fixproof.validation.security_validator import (
    determine_security_status,
    evaluate_path_traversal_security_response,
)


def response(
    *,
    succeeded: bool,
    status_code: int | None,
    body: str,
) -> dict:
    return {
        "request_succeeded": succeeded,
        "status_code": status_code,
        "body": body,
        "error": None if succeeded else "HTTP error",
    }


class PathTraversalSecurityValidatorTests(unittest.TestCase):
    def test_disclosed_outside_file_fails(self) -> None:
        evaluation = evaluate_path_traversal_security_response(
            test_type="attack",
            expected_body=None,
            forbidden_body="FIXPROOF_CONTROLLED_TRAVERSAL_SECRET",
            response=response(
                succeeded=True,
                status_code=200,
                body="FIXPROOF_CONTROLLED_TRAVERSAL_SECRET\n",
            ),
        )

        self.assertEqual(evaluation["status"], "fail")
        self.assertTrue(evaluation["outside_file_disclosed"])

    def test_rejected_traversal_passes(self) -> None:
        evaluation = evaluate_path_traversal_security_response(
            test_type="attack",
            expected_body=None,
            forbidden_body="FIXPROOF_CONTROLLED_TRAVERSAL_SECRET",
            response=response(
                succeeded=False,
                status_code=403,
                body=json.dumps({"error": "Forbidden"}),
            ),
        )

        self.assertEqual(evaluation["status"], "pass")
        self.assertFalse(evaluation["outside_file_disclosed"])

    def test_broken_control_is_inconclusive(self) -> None:
        evaluation = evaluate_path_traversal_security_response(
            test_type="control",
            expected_body="FixProof public fixture: welcome",
            forbidden_body=None,
            response=response(
                succeeded=False,
                status_code=500,
                body="",
            ),
        )

        self.assertEqual(evaluation["status"], "inconclusive")
        self.assertEqual(
            determine_security_status(
                [{"evaluation": evaluation}]
            ),
            "inconclusive",
        )


class PathTraversalFunctionalValidatorTests(unittest.TestCase):
    def test_public_file_passes(self) -> None:
        evaluation = evaluate_path_traversal_functional_response(
            expected_status=200,
            expected_body="FixProof public fixture: welcome",
            expected_json=None,
            response=response(
                succeeded=True,
                status_code=200,
                body="FixProof public fixture: welcome\n",
            ),
        )

        self.assertEqual(evaluation["status"], "pass")

    def test_missing_file_404_passes(self) -> None:
        expected = {"error": "File not found"}
        evaluation = evaluate_path_traversal_functional_response(
            expected_status=404,
            expected_body=None,
            expected_json=expected,
            response=response(
                succeeded=False,
                status_code=404,
                body=json.dumps(expected),
            ),
        )

        self.assertEqual(evaluation["status"], "pass")

    def test_changed_public_file_fails(self) -> None:
        evaluation = evaluate_path_traversal_functional_response(
            expected_status=200,
            expected_body="FixProof public fixture: welcome",
            expected_json=None,
            response=response(
                succeeded=True,
                status_code=200,
                body="different content",
            ),
        )

        self.assertEqual(evaluation["status"], "fail")


if __name__ == "__main__":
    unittest.main()
