from __future__ import annotations

import unittest
from pathlib import Path

from fixproof.evaluation.path_s06_extension_followup import (
    EXPECTED_PRIOR_VERDICTS,
    TARGETS,
    VERDICT,
    build_packet,
    load_approval,
    result_path,
    verify_extension_follow_ups,
)
from fixproof.evaluation.path_s06_extension import read_json, resolve_inside
from fixproof.evaluation.supplemental_followup import verify_recorded_follow_ups


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PathS06ExtensionFollowUpTests(unittest.TestCase):
    def test_approval_contains_five_rejections(self) -> None:
        approval = load_approval(PROJECT_ROOT)
        self.assertEqual(len(approval["decisions"]), 5)
        self.assertEqual(
            {row["verdict"] for row in approval["decisions"]}, {VERDICT}
        )

    def test_only_traversal_02_claims_manual_reproduction(self) -> None:
        approval = load_approval(PROJECT_ROOT)
        manual = {
            row["trial_id"]
            for row in approval["decisions"]
            if row["manual_reproduction"]
        }
        self.assertEqual(manual, {"primary-v1-path-traversal-initial-02"})

    def test_packets_preserve_prior_verdicts_and_bind_security_failure(self) -> None:
        for trial_id in TARGETS:
            with self.subTest(trial_id=trial_id):
                packet = build_packet(PROJECT_ROOT, trial_id)
                self.assertEqual(
                    packet["prior_supplemental_follow_up"]["verdict"],
                    EXPECTED_PRIOR_VERDICTS[trial_id],
                )
                extension = packet["extension_candidate_result"]
                self.assertEqual(extension["status"], "fail")
                self.assertEqual(extension["status_code"], 200)
                self.assertTrue(extension["marker_disclosed"])

    def test_all_extension_human_results_verify(self) -> None:
        self.assertEqual(
            verify_extension_follow_ups(PROJECT_ROOT),
            {"registered_targets": 5, "completed": 5},
        )

    def test_results_do_not_replace_supplemental_follow_ups(self) -> None:
        self.assertEqual(
            verify_recorded_follow_ups(PROJECT_ROOT),
            {"registered_targets": 14, "completed": 14, "pending": 0},
        )
        for trial_id in TARGETS:
            result = read_json(resolve_inside(PROJECT_ROOT, result_path(trial_id)))
            self.assertEqual(
                result["effect_on_frozen_records"],
                "none_earlier_records_are_preserved",
            )


if __name__ == "__main__":
    unittest.main()
