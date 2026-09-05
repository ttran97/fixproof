from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fixproof.evaluation.primary_report import (
    STUDY, REVIEWS, build_primary_report, write_primary_report, ReportDataError,
)
from fixproof.evaluation.adjudication import record_completed_result


class PrimaryReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fixproof-report-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = Path(__file__).resolve().parents[1]
        for name in ("src", "data", "benchmarks", "rules", "docs"):
            shutil.copytree(source / name, self.root / name,
                            ignore=shutil.ignore_patterns("node_modules", "__pycache__", "primary_reviews"))
        shutil.copy2(source / "pyproject.toml", self.root / "pyproject.toml")
        self.attempt = self.root / STUDY / "cases/xss/attempt-01"

    def test_relocated_study_verifies_and_preserves_denominator(self):
        report = build_primary_report(self.root)
        self.assertEqual(report["attempt_count"], 15)
        self.assertEqual(report["metrics"]["sast_false_success"]["count"], 0)
        self.assertEqual(report["metrics"]["sast_runtime_disagreement"]["count"], 10)
        self.assertEqual(report["unique_candidate_sources"]["sqli"], 1)
        self.assertEqual(report["adjudication_summary"]["completed"], 0)

    def test_tampered_bound_decision_is_rejected(self):
        path = self.attempt / "decision.json"
        path.write_text(path.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(ReportDataError, "Changed evidence"):
            build_primary_report(self.root)

    def test_candidate_content_is_verified_in_relocated_copy(self):
        path = next((self.attempt / "workspace").glob("*/attempt-01/app/app.js"))
        path.write_text("broken candidate", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Workspace content changed"):
            build_primary_report(self.root)

    def test_missing_attempt_cannot_reduce_denominator(self):
        (self.attempt / "attempt.json").unlink()
        with self.assertRaises(OSError):
            build_primary_report(self.root)

    def test_stale_collection_metrics_are_rejected(self):
        path = self.root / STUDY / "collection-state.json"
        data = json.loads(path.read_text())
        data["primary_metrics"]["sast_false_success"]["count"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ReportDataError, "summary is stale"):
            build_primary_report(self.root)

    def test_altered_scan_normalization_is_rejected(self):
        path = self.attempt / "sast/candidate-normalized.json"
        data = json.loads(path.read_text())
        data["findings"] = []
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ReportDataError, "normalization"):
            build_primary_report(self.root)

    def test_review_initialization_is_pending_and_idempotent(self):
        before = {p: p.read_bytes() for p in (self.root / STUDY).rglob("*") if p.is_file()}
        report = write_primary_report(self.root, initialize_reviews=True)
        self.assertEqual(report["adjudication_summary"],
                         {"required": 10, "completed": 0, "pending": 10, "missing_packet": 0})
        again = write_primary_report(self.root, initialize_reviews=True)
        self.assertEqual(report, again)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(list((self.root / REVIEWS).rglob("result.json")), [])

    def test_explicit_review_result_is_separate_from_automated_disposition(self):
        report = write_primary_report(self.root, initialize_reviews=True)
        row = report["experiment_matrix"][0]
        folder = self.root / REVIEWS / row["trial_id"]
        record_completed_result(
            self.root, folder / "packet.json", folder / "result.json",
            "automated-test-fixture", "REQUEST_ADDITIONAL_TESTING",
            "Test fixture only: exercise storage of a separate reviewer decision.",
            "2026-09-04T20:00:00Z", True,
        )
        revised = build_primary_report(self.root)
        self.assertEqual(revised["adjudication_summary"]["completed"], 1)
        self.assertEqual(revised["experiment_matrix"][0]["decision"], "NEEDS_HUMAN_ADJUDICATION")
        self.assertEqual(revised["metrics"], report["metrics"])


if __name__ == "__main__":
    unittest.main()
