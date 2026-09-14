from __future__ import annotations

import json
import unittest
from pathlib import Path

from fixproof.evaluation.supplemental_protocol import (
    detect_environment,
    load_json,
    validate_case_manifest,
    verify_protocol_lock,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SupplementalProtocolTests(unittest.TestCase):
    def test_frozen_protocol_bindings_verify(self) -> None:
        result = verify_protocol_lock(PROJECT_ROOT)

        self.assertEqual(result["protocol_id"], "supplemental-v1")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(len(result["bindings"]), 3)

    def test_case_manifest_matches_frozen_matrix(self) -> None:
        result = validate_case_manifest(PROJECT_ROOT)

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["test_count"], 28)
        self.assertEqual(
            result["case_counts"],
            {"xss": 9, "path-traversal": 11, "sqli": 8},
        )
        self.assertTrue(result["definition_only"])
        self.assertTrue(result["does_not_execute_applications"])

    def test_manifest_has_three_distinct_outcome_categories(self) -> None:
        manifest = load_json(
            PROJECT_ROOT / "tests/supplemental/v1/cases.json"
        )
        categories = {
            test["category"]
            for case in manifest["cwes"].values()
            for test in case["tests"]
        }

        self.assertEqual(
            categories,
            {"security", "behavioral_parity", "robustness_contract"},
        )

    def test_preflight_reports_missing_tools_without_running_apps(self) -> None:
        result = detect_environment(
            PROJECT_ROOT,
            which=lambda _: None,
            chromium_path=str(PROJECT_ROOT / "missing-chromium.exe"),
        )

        self.assertFalse(result["ready_for_live_supplemental_execution"])
        self.assertIn("node_not_on_path", result["blockers"])
        self.assertIn("npm_not_on_path", result["blockers"])
        self.assertIn(
            "chromium_not_installed_for_playwright",
            result["blockers"],
        )
        self.assertEqual(
            result["check_type"],
            "environment_preflight_no_candidate_execution",
        )

    def test_protocol_lock_remains_machine_readable(self) -> None:
        lock_path = PROJECT_ROOT / "data/supplemental/v1/protocol-lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))

        self.assertEqual(lock["status"], "frozen")
        self.assertEqual(lock["execution_count_at_freeze"], 0)
        self.assertEqual(
            lock["candidate_policy"],
            "reuse_saved_primary_candidates_no_new_model_calls",
        )


if __name__ == "__main__":
    unittest.main()
