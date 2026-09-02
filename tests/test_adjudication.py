from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fixproof.evaluation.adjudication import (
    AdjudicationDataError,
    REQUIRED_REVIEW_CHECKS,
    _resolve_project_file,
    build_completed_result,
    validate_packet,
    validate_result,
)
from fixproof.evaluation.report_builder import build_report_data


class AdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.manifest = (
            cls.project_root / "data" / "evaluation" / "experiment-manifest.json"
        )
        cls.report = build_report_data(cls.project_root, cls.manifest)
        cls.xss_retry = next(
            row
            for row in cls.report["experiment_matrix"]
            if row["case_id"] == "xss" and row["attempt"] == 2
        )
        cls.packet_path = (
            cls.project_root
            / cls.xss_retry["artifacts"]["adjudication_packet"]["path"]
        )

    def test_selected_completed_packet_matches_bound_evidence(self) -> None:
        packet = validate_packet(
            self.project_root,
            self.xss_retry,
            self.packet_path,
        )
        self.assertEqual(packet["artifact_type"], "adjudication_packet")
        self.assertEqual(
            packet["adjudication_packet"]["canonical_id"],
            "CF-ffcaa5bd5497",
        )
        self.assertEqual(self.xss_retry["adjudication"]["status"], "completed")
        self.assertEqual(
            self.xss_retry["adjudication"]["verdict"], "ACCEPT_CANDIDATE"
        )

    def test_completed_result_is_separate_and_valid(self) -> None:
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        checks = {name: True for name in REQUIRED_REVIEW_CHECKS}
        result = build_completed_result(
            project_root=self.project_root,
            packet_path=self.packet_path,
            packet_payload=packet,
            reviewer="test-reviewer",
            verdict="ACCEPT_CANDIDATE",
            rationale=(
                "The test reviewer inspected the candidate and all bound "
                "evidence for this unit test."
            ),
            reviewed_at="2026-08-27T12:00:00Z",
            confirmed_checks=checks,
        )

        with tempfile.TemporaryDirectory(dir=self.project_root) as directory:
            temporary_root = Path(directory)
            result_path = temporary_root / "result.json"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            validated = validate_result(
                project_root=self.project_root,
                row=self.xss_retry,
                packet_path=self.packet_path,
                packet_payload=packet,
                result_path=result_path,
            )

            manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
            xss_retry_entry = next(
                entry
                for entry in manifest["attempts"]
                if entry["case_id"] == "xss" and entry["attempt"] == 2
            )
            xss_retry_entry["artifacts"]["adjudication_result"] = (
                result_path.relative_to(self.project_root).as_posix()
            )
            manifest_path = temporary_root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            completed_report = build_report_data(self.project_root, manifest_path)

        self.assertEqual(
            validated["adjudication_result"]["verdict"], "ACCEPT_CANDIDATE"
        )
        self.assertTrue(
            validated["adjudication_result"]["automated_decision_unchanged"]
        )
        completed_xss_retry = next(
            row
            for row in completed_report["experiment_matrix"]
            if row["case_id"] == "xss" and row["attempt"] == 2
        )
        self.assertEqual(completed_xss_retry["decision"], "NEEDS_HUMAN_ADJUDICATION")
        self.assertEqual(completed_xss_retry["adjudication"]["status"], "completed")
        self.assertEqual(
            completed_report["metrics"]["human_adjudication_completion_rate"][
                "numerator"
            ],
            2,
        )

    def test_incomplete_human_checklist_is_rejected(self) -> None:
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        checks = {name: True for name in REQUIRED_REVIEW_CHECKS}
        checks[REQUIRED_REVIEW_CHECKS[-1]] = False

        with self.assertRaisesRegex(
            AdjudicationDataError,
            "Human review checks are incomplete",
        ):
            build_completed_result(
                project_root=self.project_root,
                packet_path=self.packet_path,
                packet_payload=packet,
                reviewer="test-reviewer",
                verdict="REJECT_CANDIDATE",
                rationale="This is a sufficiently detailed test rationale.",
                reviewed_at="2026-08-27T12:00:00Z",
                confirmed_checks=checks,
            )

    def test_tampered_packet_is_rejected(self) -> None:
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        packet["adjudication_packet"]["evidence_binding"]["artifacts"][
            "decision"
        ]["sha256"] = "0" * 64

        with tempfile.TemporaryDirectory(dir=self.project_root) as directory:
            packet_path = Path(directory) / "tampered-packet.json"
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            with self.assertRaisesRegex(
                AdjudicationDataError,
                "changed after packet creation",
            ):
                validate_packet(
                    self.project_root,
                    self.xss_retry,
                    packet_path,
                )

    def test_historical_absolute_path_relocates_to_active_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            candidate = (
                temporary_root
                / "workspaces"
                / "example"
                / "candidate.patch"
            )
            candidate.parent.mkdir(parents=True)
            candidate.write_text("example patch\n", encoding="utf-8")

            historical = (
                "C:/Users/Example/old-fixproof/"
                "workspaces/example/candidate.patch"
            )
            resolved = _resolve_project_file(
                temporary_root,
                historical,
                "test historical path",
            )

        self.assertEqual(resolved, candidate.resolve())


if __name__ == "__main__":
    unittest.main()
