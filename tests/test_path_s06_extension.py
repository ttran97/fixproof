from __future__ import annotations

import json
import unittest
from pathlib import Path

from fixproof.evaluation.path_s06_extension import (
    evaluate_baseline_response,
    evaluate_candidate_response,
    validate_definition,
    verify_protocol,
)


MARKER = "FIXPROOF_CONTROLLED_TRAVERSAL_SECRET"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PathS06OracleTests(unittest.TestCase):
    def test_baseline_requires_http_200_and_marker(self) -> None:
        passed = evaluate_baseline_response(
            {"status_code": 200, "body": MARKER}, MARKER
        )
        missing_marker = evaluate_baseline_response(
            {"status_code": 200, "body": "not found"}, MARKER
        )
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(missing_marker["status"], "fail")

    def test_candidate_accepts_only_registered_denial_statuses(self) -> None:
        for status_code in (400, 403, 404):
            with self.subTest(status_code=status_code):
                result = evaluate_candidate_response(
                    {"status_code": status_code, "body": "denied"}, MARKER
                )
                self.assertEqual(result["status"], "pass")

    def test_candidate_http_200_without_marker_still_fails_contract(self) -> None:
        result = evaluate_candidate_response(
            {"status_code": 200, "body": "safe-looking response"}, MARKER
        )
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["marker_disclosed"])
        self.assertFalse(result["status_allowed"])

    def test_candidate_marker_disclosure_fails(self) -> None:
        result = evaluate_candidate_response(
            {"status_code": 200, "body": MARKER}, MARKER
        )
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["marker_disclosed"])

    def test_missing_http_observation_is_inconclusive(self) -> None:
        result = evaluate_candidate_response(
            {"status_code": None, "body": "", "error": "timeout"}, MARKER
        )
        self.assertEqual(result["status"], "inconclusive")

    def test_frozen_definition_contains_one_baseline_and_five_candidates(self) -> None:
        definition = json.loads(
            (PROJECT_ROOT / "tests/extensions/path_s06/v1/case.json").read_text(
                encoding="utf-8"
            )
        )
        validate_definition(definition)
        self.assertEqual(
            sum(row["type"] == "baseline" for row in definition["targets"]), 1
        )
        self.assertEqual(
            sum(row["type"] == "candidate" for row in definition["targets"]), 5
        )

    def test_frozen_protocol_and_all_input_hashes_verify(self) -> None:
        definition = verify_protocol(PROJECT_ROOT)
        self.assertEqual(definition["protocol_id"], "path-s06-extension-v1")


if __name__ == "__main__":
    unittest.main()
