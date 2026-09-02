from __future__ import annotations

import unittest
from pathlib import Path

from fixproof.evaluation.report_builder import build_report_data


class SelectedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.report = build_report_data(
            cls.project_root,
            cls.project_root / "data" / "evaluation" / "experiment-manifest.json",
        )

    def test_selected_cases_cover_the_declared_cwes(self) -> None:
        observed = {
            (row["case_id"], row["cwe"])
            for row in self.report["experiment_matrix"]
        }
        self.assertEqual(
            observed,
            {
                ("xss", "CWE-79"),
                ("sqli", "CWE-89"),
                ("path-traversal", "CWE-22"),
            },
        )

    def test_every_ai_attempt_binds_the_complete_evidence_chain(self) -> None:
        required = {
            "baseline_correlated",
            "remediation",
            "preliminary",
            "security",
            "functional",
            "decision",
            "workspace",
        }
        for row in self.report["experiment_matrix"]:
            self.assertEqual(row["candidate_origin"], "ai_generated")
            self.assertTrue(required.issubset(row["artifacts"]))
            for name in required:
                artifact = row["artifacts"][name]
                self.assertTrue(
                    (self.project_root / artifact["path"]).is_file(),
                    msg=f"Missing {name} for {row['case_id']} attempt {row['attempt']}",
                )
                self.assertEqual(len(artifact["sha256"]), 64)

    def test_selected_attempts_record_runtime_security_and_regression_tests(self) -> None:
        security_total = sum(
            row["evidence"]["security"]["total"]
            for row in self.report["experiment_matrix"]
        )
        functional_total = sum(
            row["evidence"]["functional"]["total"]
            for row in self.report["experiment_matrix"]
        )
        self.assertEqual(security_total, 12)
        self.assertEqual(functional_total, 18)
        self.assertEqual(security_total + functional_total, 30)


if __name__ == "__main__":
    unittest.main()
