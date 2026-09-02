from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fixproof.demo import (
    DemoError,
    run_live_validation,
    select_demo_case,
    validate_dashboard_state,
)


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]

    @staticmethod
    def _write_result(path: Path, payload: dict) -> dict:
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def test_latest_manifest_attempt_is_selected_by_default(self) -> None:
        selection = select_demo_case(self.project_root, "xss")

        self.assertEqual(selection.attempt, 2)
        self.assertEqual(selection.canonical_id, "CF-ffcaa5bd5497")
        self.assertTrue(selection.baseline_source.is_file())
        self.assertTrue(selection.patch_file.is_file())
        self.assertFalse(
            selection.workspace_dir.is_relative_to(
                self.project_root / "sample_apps"
            )
        )

    def test_explicit_historical_attempt_can_be_selected(self) -> None:
        selection = select_demo_case(self.project_root, "xss", attempt=1)

        self.assertEqual(selection.attempt, 1)
        self.assertEqual(
            selection.workspace_metadata_file,
            self.project_root / "workspaces" / "CF-ffcaa5bd5497" / "workspace.json",
        )

    def test_unsupported_or_unselected_case_is_rejected(self) -> None:
        with self.assertRaisesRegex(DemoError, "Unsupported demo case"):
            select_demo_case(self.project_root, "command-injection")

        with self.assertRaisesRegex(DemoError, "no sqli entry"):
            select_demo_case(self.project_root, "sqli", attempt=99)

    def test_live_validation_uses_unique_disposable_outputs(self) -> None:
        selection = select_demo_case(self.project_root, "sqli")

        def security_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            self.assertEqual(contexts, selection.contexts_file)
            self.assertEqual(workspace, selection.workspace_dir)
            self.assertEqual(canonical_id, selection.canonical_id)
            return self._write_result(
                output,
                {
                    "security_validation": {
                        "canonical_id": canonical_id,
                        "status": "pass",
                    }
                },
            )

        def functional_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            return self._write_result(
                output,
                {
                    "functional_validation": {
                        "canonical_id": canonical_id,
                        "status": "pass",
                    }
                },
            )

        def decision_runner(
            preliminary: Path,
            security: Path,
            functional: Path,
            output: Path,
        ) -> dict:
            self.assertEqual(preliminary, selection.preliminary_file)
            self.assertTrue(security.is_file())
            self.assertTrue(functional.is_file())
            payload = {
                "decision": {
                    "canonical_id": selection.canonical_id,
                    "classification": "validated_candidate",
                    "disposition": "READY_FOR_HUMAN_REVIEW",
                }
            }
            return self._write_result(output, payload)

        with tempfile.TemporaryDirectory() as directory:
            output_parent = Path(directory)
            first = run_live_validation(
                selection,
                output_parent,
                security_runner=security_runner,
                functional_runner=functional_runner,
                decision_runner=decision_runner,
                check_port=False,
            )
            second = run_live_validation(
                selection,
                output_parent,
                security_runner=security_runner,
                functional_runner=functional_runner,
                decision_runner=decision_runner,
                check_port=False,
            )

            self.assertNotEqual(first.output_dir, second.output_dir)
            self.assertEqual(first.output_dir.parent, output_parent.resolve())
            self.assertTrue(first.security_file.is_file())
            self.assertTrue(first.functional_file.is_file())
            self.assertTrue(first.decision_file.is_file())
            summary = json.loads(first.summary_file.read_text(encoding="utf-8"))
            self.assertFalse(summary["authoritative_experiment_artifact"])
            self.assertTrue(summary["recorded_decision_match"])
            self.assertEqual(summary["evidence_mode"]["candidate_sast"], "recorded")

    def test_fresh_sast_mode_uses_disposable_preliminary_artifacts(self) -> None:
        selection = select_demo_case(self.project_root, "sqli")

        def preliminary_runner(
            project_root: Path,
            baseline: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
            artifact_dir: Path | None,
        ) -> dict:
            self.assertEqual(project_root, selection.project_root)
            self.assertEqual(baseline, selection.baseline_correlated_file)
            self.assertEqual(workspace, selection.workspace_dir)
            self.assertEqual(canonical_id, selection.canonical_id)
            self.assertIsNotNone(artifact_dir)
            assert artifact_dir is not None
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "candidate-semgrep-raw.json").write_text(
                "{}",
                encoding="utf-8",
            )
            return self._write_result(
                output,
                {
                    "validation": {
                        "canonical_id": canonical_id,
                        "syntax": {"status": "pass"},
                    }
                },
            )

        def security_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            return self._write_result(
                output,
                {
                    "security_validation": {
                        "canonical_id": canonical_id,
                        "status": "pass",
                    }
                },
            )

        def functional_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            return self._write_result(
                output,
                {
                    "functional_validation": {
                        "canonical_id": canonical_id,
                        "status": "pass",
                    }
                },
            )

        def decision_runner(
            preliminary: Path,
            security: Path,
            functional: Path,
            output: Path,
        ) -> dict:
            self.assertNotEqual(preliminary, selection.preliminary_file)
            self.assertTrue(preliminary.is_file())
            payload = {
                "decision": {
                    "canonical_id": selection.canonical_id,
                    "classification": "validated_candidate",
                    "disposition": "READY_FOR_HUMAN_REVIEW",
                }
            }
            return self._write_result(output, payload)

        with tempfile.TemporaryDirectory() as directory:
            result = run_live_validation(
                selection,
                Path(directory),
                fresh_sast=True,
                preliminary_runner=preliminary_runner,
                security_runner=security_runner,
                functional_runner=functional_runner,
                decision_runner=decision_runner,
                check_port=False,
            )

            self.assertEqual(result.preliminary_file.parent, result.output_dir)
            self.assertEqual(result.evidence_mode["candidate_sast"], "live")
            summary = json.loads(result.summary_file.read_text(encoding="utf-8"))
            self.assertEqual(summary["evidence_mode"]["candidate_sast"], "live")
            self.assertEqual(
                Path(summary["outputs"]["preliminary"]),
                result.preliminary_file,
            )

    def test_live_decision_drift_is_rejected(self) -> None:
        selection = select_demo_case(self.project_root, "sqli")

        def security_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            return self._write_result(
                output,
                {"security_validation": {"status": "pass"}},
            )

        def functional_runner(
            contexts: Path,
            workspace: Path,
            canonical_id: str,
            output: Path,
        ) -> dict:
            return self._write_result(
                output,
                {"functional_validation": {"status": "pass"}},
            )

        def decision_runner(
            preliminary: Path,
            security: Path,
            functional: Path,
            output: Path,
        ) -> dict:
            payload = {
                "decision": {
                    "classification": "sast_false_success",
                    "disposition": "REJECT",
                }
            }
            return self._write_result(output, payload)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DemoError, "disagrees"):
                run_live_validation(
                    selection,
                    Path(directory),
                    security_runner=security_runner,
                    functional_runner=functional_runner,
                    decision_runner=decision_runner,
                    check_port=False,
                )

    def test_dashboard_report_is_current_and_ready(self) -> None:
        report = validate_dashboard_state(self.project_root)

        self.assertEqual(report["attempt_count"], 4)
        self.assertTrue(report["outcome_coverage"]["all_required_outcomes_covered"])


if __name__ == "__main__":
    unittest.main()
