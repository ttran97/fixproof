from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fixproof.evaluation.report_builder import ReportDataError, build_report


class EvaluationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.manifest = (
            cls.project_root / "data" / "evaluation" / "experiment-manifest.json"
        )

    def test_current_experiment_matrix_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            report = build_report(
                project_root=self.project_root,
                manifest_path=self.manifest,
                json_output=output_root / "report.json",
                markdown_output=output_root / "report.md",
            )

            self.assertEqual(report["case_count"], 3)
            self.assertEqual(report["attempt_count"], 4)

            rows = {
                (row["case_id"], row["attempt"]): row
                for row in report["experiment_matrix"]
            }
            self.assertEqual(rows[("xss", 1)]["decision"], "REJECT")
            self.assertEqual(
                rows[("xss", 2)]["decision"],
                "NEEDS_HUMAN_ADJUDICATION",
            )
            self.assertTrue(
                rows[("xss", 2)]["artifacts"]["decision"]["path"].endswith(
                    "-attempt-02-policy-02.json"
                )
            )
            self.assertEqual(
                rows[("sqli", 1)]["scanner_evidence"]["rule_origins"],
                ["fixproof_controlled"],
            )
            self.assertEqual(
                rows[("sqli", 1)]["decision"],
                "READY_FOR_HUMAN_REVIEW",
            )
            self.assertEqual(
                rows[("sqli", 1)]["evidence"]["target_sast"],
                "resolved",
            )
            self.assertEqual(
                rows[("sqli", 1)]["evidence_revision"]["revision"],
                "controlled-sqli-rule-v2",
            )
            self.assertEqual(
                rows[("sqli", 1)]["evidence_revision"][
                    "historical_adjudication"
                ]["verdict"],
                "ACCEPT_CANDIDATE",
            )
            self.assertEqual(
                rows[("path-traversal", 1)]["scanner_evidence"]["rule_origins"],
                ["semgrep_oss"],
            )

            metrics = report["metrics"]
            self.assertEqual(
                metrics["sast_remediation_success_rate"]["numerator"], 1
            )
            self.assertEqual(
                metrics["targeted_security_validation_pass_rate"]["percentage"],
                100.0,
            )
            self.assertEqual(
                metrics["functional_preservation_rate"]["percentage"], 75.0
            )
            self.assertEqual(
                metrics["security_regression_new_finding_rate"]["numerator"], 0
            )
            self.assertEqual(metrics["sast_false_success_count"], 0)
            self.assertEqual(metrics["sast_runtime_disagreement_count"], 2)
            self.assertEqual(
                metrics["retry_improvement_rate"]["percentage"], 100.0
            )
            self.assertEqual(
                metrics["human_adjudication_rate"]["percentage"], 50.0
            )
            self.assertEqual(
                metrics["human_adjudication_completion_rate"]["percentage"],
                100.0,
            )

            required_adjudications = [
                row["adjudication"]
                for row in report["experiment_matrix"]
                if row["adjudication"]["required"]
            ]
            self.assertEqual(len(required_adjudications), 2)
            self.assertTrue(
                all(item["status"] == "completed" for item in required_adjudications)
            )
            self.assertEqual(
                report["adjudication_summary"],
                {
                    "required": 2,
                    "missing_packet": 0,
                    "pending": 0,
                    "completed": 2,
                    "verdict_distribution": {"ACCEPT_CANDIDATE": 2},
                },
            )

            self.assertEqual(report["control_count"], 1)
            control = report["outcome_coverage_controls"][0]
            self.assertEqual(control["candidate_origin"], "deterministic_non_ai")
            self.assertEqual(control["metric_scope"], "outcome_coverage_only")
            self.assertEqual(control["classification"], "sast_false_success")
            self.assertTrue(control["evidence"]["false_success"])
            coverage = report["outcome_coverage"]
            self.assertTrue(coverage["all_required_outcomes_covered"])
            self.assertTrue(
                coverage["required_outcomes"]["validated_candidate"][
                    "observed_in_primary_ai_attempts"
                ]
            )
            self.assertFalse(
                coverage["required_outcomes"]["sast_false_success"][
                    "observed_in_primary_ai_attempts"
                ]
            )
            self.assertTrue(
                coverage["required_outcomes"]["sast_false_success"][
                    "demonstrated_by_non_ai_control"
                ]
            )

            self.assertEqual(len(report["retry_analysis"]), 1)
            self.assertTrue(report["retry_analysis"][0]["improved"])
            self.assertEqual(
                report["retry_analysis"][0]["improved_dimensions"],
                ["functional_validation"],
            )

            markdown = (output_root / "report.md").read_text(encoding="utf-8")
            self.assertIn("| SQLi | 89 | 1 | Resolved | Pass (2/2)", markdown)
            self.assertIn("| Path traversal | 22 | 1 | Persistent", markdown)
            self.assertIn("SAST/runtime disagreement count | 2", markdown)
            self.assertIn("Human adjudication completion rate | 2/2", markdown)
            self.assertIn("deterministic_non_ai", markdown)
            self.assertIn("controlled-sqli-rule-v2", markdown)
            self.assertIn("ACCEPT_CANDIDATE by Tony Tran", markdown)

    def test_report_is_deterministic_for_unchanged_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            first_json = output_root / "first.json"
            first_markdown = output_root / "first.md"
            second_json = output_root / "second.json"
            second_markdown = output_root / "second.md"

            build_report(
                self.project_root,
                self.manifest,
                first_json,
                first_markdown,
            )
            build_report(
                self.project_root,
                self.manifest,
                second_json,
                second_markdown,
            )

            self.assertEqual(first_json.read_bytes(), second_json.read_bytes())
            self.assertEqual(
                first_markdown.read_bytes(), second_markdown.read_bytes()
            )

    def test_stale_decision_evidence_is_rejected(self) -> None:
        source_manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        selected_attempt = source_manifest["attempts"][0]

        with tempfile.TemporaryDirectory(dir=self.project_root) as temporary_directory:
            temporary_root = Path(temporary_directory)
            decision_source = (
                self.project_root / selected_attempt["artifacts"]["decision"]
            )
            stale_decision = json.loads(decision_source.read_text(encoding="utf-8"))
            stale_decision["decision"]["evidence"]["target_sast"] = "resolved"
            stale_decision_path = temporary_root / "stale-decision.json"
            stale_decision_path.write_text(
                json.dumps(stale_decision), encoding="utf-8"
            )

            selected_attempt["artifacts"]["decision"] = (
                stale_decision_path.relative_to(self.project_root).as_posix()
            )
            temporary_manifest = {
                "schema_version": "0.1",
                "project": "FixProof",
                "study_id": "stale-decision-test",
                "attempts": [selected_attempt],
            }
            temporary_manifest_path = temporary_root / "manifest.json"
            temporary_manifest_path.write_text(
                json.dumps(temporary_manifest), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ReportDataError,
                "disagrees with its selected validation artifacts",
            ):
                build_report(
                    project_root=self.project_root,
                    manifest_path=temporary_manifest_path,
                    json_output=temporary_root / "report.json",
                    markdown_output=temporary_root / "report.md",
                )

    def test_non_ai_control_cannot_enter_primary_metrics(self) -> None:
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["controls"][0]["candidate_origin"] = "ai_generated"

        with tempfile.TemporaryDirectory(dir=self.project_root) as directory:
            temporary_root = Path(directory)
            manifest_path = temporary_root / "invalid-control-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(
                ReportDataError,
                "must not be labeled ai_generated",
            ):
                build_report(
                    project_root=self.project_root,
                    manifest_path=manifest_path,
                    json_output=temporary_root / "report.json",
                    markdown_output=temporary_root / "report.md",
                )


if __name__ == "__main__":
    unittest.main()
