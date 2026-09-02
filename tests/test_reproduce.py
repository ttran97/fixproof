from __future__ import annotations

import copy
import unittest
from pathlib import Path

from fixproof.evaluation.report_builder import build_report_data
from fixproof.reproduce import evaluate_readiness


class ReproducibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.report = build_report_data(
            cls.project_root,
            cls.project_root
            / "data"
            / "evaluation"
            / "experiment-manifest.json",
        )

    @staticmethod
    def _checks_by_name(report: dict) -> dict[str, bool]:
        return {
            check.name: check.passed for check in evaluate_readiness(report)
        }

    def test_current_experiment_passes_every_readiness_check(self) -> None:
        checks = evaluate_readiness(self.report)

        self.assertTrue(all(check.passed for check in checks))
        self.assertEqual(len(checks), 8)

    def test_ai_labeled_control_fails_metric_separation(self) -> None:
        report = copy.deepcopy(self.report)
        report["outcome_coverage_controls"][0][
            "candidate_origin"
        ] = "ai_generated"

        checks = self._checks_by_name(report)

        self.assertFalse(checks["control metric separation"])
        self.assertTrue(checks["primary AI metric scope"])

    def test_pending_adjudication_fails_readiness(self) -> None:
        report = copy.deepcopy(self.report)
        report["adjudication_summary"]["completed"] = 1
        report["adjudication_summary"]["pending"] = 1

        checks = self._checks_by_name(report)

        self.assertFalse(checks["human adjudication"])

    def test_incomplete_outcome_and_artifact_binding_fail_readiness(self) -> None:
        report = copy.deepcopy(self.report)
        report["outcome_coverage"]["all_required_outcomes_covered"] = False
        report["experiment_matrix"][0]["artifacts"]["decision"][
            "sha256"
        ] = "not-a-digest"

        checks = self._checks_by_name(report)

        self.assertFalse(checks["required policy outcomes"])
        self.assertFalse(checks["artifact bindings"])


if __name__ == "__main__":
    unittest.main()
