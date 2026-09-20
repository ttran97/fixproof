from __future__ import annotations

import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fixproof.evaluation.supplemental_protocol import load_json
from fixproof.evaluation.supplemental_report import (
    build_supplemental_report,
    main,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SupplementalReportTests(unittest.TestCase):
    def test_check_verifies_saved_run_bindings_not_later_reruns(self) -> None:
        stored = load_json(
            PROJECT_ROOT / "data/supplemental/v1/supplemental-report.json"
        )
        with (
            patch(
                "fixproof.evaluation.supplemental_report.latest_successful_baseline",
                side_effect=AssertionError("Selected a newer baseline"),
            ),
            patch(
                "fixproof.evaluation.supplemental_report.latest_completed_candidate_group",
                side_effect=AssertionError("Selected a newer candidate run"),
            ),
        ):
            self.assertEqual(
                build_supplemental_report(PROJECT_ROOT, bound_report=stored),
                stored,
            )
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "supplemental_report",
                        "--project-root",
                        str(PROJECT_ROOT),
                        "--check",
                    ],
                ),
                redirect_stdout(io.StringIO()),
            ):
                main()

    def test_check_rejects_changed_saved_run_hash(self) -> None:
        stored = load_json(
            PROJECT_ROOT / "data/supplemental/v1/supplemental-report.json"
        )
        changed = copy.deepcopy(stored)
        changed["cwes"][0]["candidate_group"]["sha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "Bound run hash mismatch"):
            build_supplemental_report(PROJECT_ROOT, bound_report=changed)

    def test_recorded_supplemental_report_recomputes(self) -> None:
        report = build_supplemental_report(PROJECT_ROOT)

        self.assertTrue(report["evidence_verified"])
        self.assertEqual(report["baseline_count"], 3)
        self.assertEqual(report["saved_candidate_count"], 15)
        self.assertEqual(
            report["candidate_case_observations"],
            {
                "total": 140,
                "pass": 120,
                "fail": 15,
                "inconclusive": 5,
            },
        )
        self.assertEqual(
            report["candidate_observations_by_category"]["security"],
            {
                "total": 60,
                "pass": 55,
                "fail": 0,
                "inconclusive": 5,
            },
        )
        self.assertEqual(
            report["candidate_observations_by_category"][
                "behavioral_parity"
            ],
            {
                "total": 45,
                "pass": 40,
                "fail": 5,
                "inconclusive": 0,
            },
        )
        self.assertEqual(
            report["candidate_observations_by_category"][
                "robustness_contract"
            ],
            {
                "total": 35,
                "pass": 25,
                "fail": 10,
                "inconclusive": 0,
            },
        )
        self.assertFalse(report["automatic_acceptance"])
        self.assertTrue(report["human_follow_up_required"])

    def test_path_runner_defect_is_preserved_but_not_used_as_gate(self) -> None:
        report = build_supplemental_report(PROJECT_ROOT)
        superseded = report["superseded_or_invalid_runs"]

        self.assertEqual(len(superseded), 1)
        self.assertEqual(
            superseded[0]["status"],
            "baseline_expectation_mismatch",
        )
        self.assertFalse(superseded[0]["used_as_candidate_gate"])
        self.assertIn("investigation", superseded[0])

    def test_report_is_deterministic_for_unchanged_evidence(self) -> None:
        first = build_supplemental_report(PROJECT_ROOT)
        second = build_supplemental_report(PROJECT_ROOT)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
