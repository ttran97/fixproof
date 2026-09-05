from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from fixproof.findings.lifecycle import (
    LifecycleError, append_snapshot, empty_history, validate_history,
    snapshot_from_scan, record_snapshot,
)


def snapshot(version, present=True, file="app.js"):
    return {"version": version, "ruleset_id": "fixed-test-rules", "scanner_version": "1.136.0",
            "scan_complete": True, "coverage": ["a/app.js", "app.js", "b/app.js"],
            "findings": [{"identity": {"file": file, "cwe": "CWE-89", "scope": "express:get:/user"},
                          "start_line": 10, "rule_ids": ["test-rule"]}] if present else []}


class LifecycleTests(unittest.TestCase):
    def test_new_persistent_resolved_reopened_then_persistent(self):
        history = empty_history()
        for version, present, expected in (("v1", True, "new"), ("v2", True, "persistent"),
                                            ("v3", False, "resolved"), ("v4", True, "reopened"),
                                            ("v5", True, "persistent")):
            history = append_snapshot(history, snapshot(version, present))
            state = next(iter(history["findings"].values()))
            self.assertEqual(state["status"], expected)
        self.assertEqual(state["reopen_count"], 1)
        self.assertEqual(state["first_seen"], "v1")
        validate_history(history)

    def test_empty_later_scan_does_not_repeat_resolution(self):
        history = append_snapshot(empty_history(), snapshot("v1"))
        history = append_snapshot(history, snapshot("v2", False))
        history = append_snapshot(history, snapshot("v3", False))
        self.assertEqual(history["snapshots"][-1]["events"], [])

    def test_retry_same_version_is_idempotent_but_changed_evidence_fails(self):
        original = snapshot("v1")
        history = append_snapshot(empty_history(), original)
        self.assertEqual(append_snapshot(history, original), history)
        with self.assertRaisesRegex(LifecycleError, "Version already exists"):
            append_snapshot(history, snapshot("v1", False))

    def test_incomplete_or_incomparable_scan_does_not_resolve(self):
        history = append_snapshot(empty_history(), snapshot("v1"))
        for field, value in (("scan_complete", False), ("coverage", ["app.js"]),
                             ("ruleset_id", "different"), ("scanner_version", "other")):
            with self.subTest(field=field):
                changed = snapshot("v2", False)
                changed[field] = value
                with self.assertRaises(LifecycleError):
                    append_snapshot(history, changed)

    def test_same_filename_in_different_directories_is_distinct(self):
        first = snapshot("v1", file="a/app.js")
        first["findings"] += snapshot("v1", file="b/app.js")["findings"]
        history = append_snapshot(empty_history(), first)
        self.assertEqual(len(history["findings"]), 2)

    def test_ambiguous_same_scope_findings_are_rejected(self):
        ambiguous = snapshot("v1")
        ambiguous["findings"] *= 2
        with self.assertRaisesRegex(LifecycleError, "Ambiguous"):
            append_snapshot(empty_history(), ambiguous)

    def test_modified_event_or_derived_state_breaks_history_validation(self):
        history = append_snapshot(empty_history(), snapshot("v1"))
        for change_event in (True, False):
            tampered = copy.deepcopy(history)
            if change_event:
                tampered["snapshots"][0]["events"][0]["status"] = "reopened"
            else:
                next(iter(tampered["findings"].values()))["status"] = "resolved"
            with self.assertRaisesRegex(LifecycleError, "inconsistent"):
                validate_history(tampered)

    def test_real_recorded_sqli_snapshots_reopen_on_baseline_reintroduction(self):
        root = Path(__file__).resolve().parents[1]
        baseline_scan = root / "data/primary_baselines/raw_scans/sqli-configured.json"
        baseline_root = root / "benchmarks/primary/v1/sqli"
        folder = root / "data/primary_trials/v1/cases/sqli/attempt-01"
        candidate_root = next((folder / "workspace").glob("*/attempt-01/app"))
        history = empty_history()
        for version, source, scan in (("vulnerable", baseline_root, baseline_scan),
                                       ("fixed", candidate_root, folder / "sast/candidate-semgrep-raw.json"),
                                       ("reintroduced", baseline_root, baseline_scan)):
            recorded = snapshot_from_scan(root, source, scan, version, "recorded-primary-v1-sqli")
            history = append_snapshot(history, recorded)
        sqli = next(f for f in history["findings"].values() if f["identity"]["cwe"] == "CWE-89")
        self.assertEqual(sqli["status"], "reopened")
        self.assertEqual(sqli["reopen_count"], 1)

    def test_storage_lock_and_failed_append_preserve_existing_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.json"
            history = record_snapshot(path, snapshot("v1"))
            with self.assertRaises(LifecycleError):
                record_snapshot(path, snapshot("v1", False))
            self.assertEqual(json.loads(path.read_text()), history)
            self.assertFalse(path.with_suffix(".json.lock").exists())
            path.with_suffix(".json.lock").write_text("another writer")
            with self.assertRaises(FileExistsError):
                record_snapshot(path, snapshot("v2"))
            self.assertTrue(path.with_suffix(".json.lock").exists())


if __name__ == "__main__":
    unittest.main()
