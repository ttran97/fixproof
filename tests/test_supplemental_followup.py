from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fixproof.evaluation.supplemental_followup import (
    build_follow_up_packet,
    record_follow_up,
    verify_recorded_follow_ups,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SupplementalFollowUpTests(unittest.TestCase):
    def test_all_registered_human_records_verify(self) -> None:
        summary = verify_recorded_follow_ups(PROJECT_ROOT)

        self.assertEqual(summary["registered_targets"], 14)
        self.assertEqual(summary["completed"], 14)
        self.assertEqual(summary["pending"], 0)

    def test_ready_candidate_without_primary_human_review_can_be_reviewed(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-sqli-initial-01",
        )

        self.assertEqual(packet["status"], "pending_human_review")
        self.assertIsNone(packet["original_primary_review"]["verdict"])
        self.assertEqual(
            packet["original_primary_review"]["context_type"],
            "automated_decision_without_human_review",
        )
        self.assertTrue(
            packet["original_primary_review"]["result"]["path"].endswith(
                "/decision.json"
            )
        )
        self.assertIn(
            {
                "test_id": "SQL-R01",
                "category": "robustness_contract",
                "status": "fail",
            },
            packet["supplemental_candidate_result"]["nonpassing_tests"],
        )
        self.assertIn("first dated human decision", packet["purpose"])

    def test_accepted_traversal_candidate_can_request_more_testing(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-path-traversal-initial-05",
        )

        self.assertEqual(
            packet["original_primary_review"]["verdict"],
            "ACCEPT_CANDIDATE",
        )
        self.assertIn(
            {
                "test_id": "PATH-R03",
                "category": "robustness_contract",
                "status": "fail",
            },
            packet["supplemental_candidate_result"]["nonpassing_tests"],
        )
        self.assertIn(
            {
                "test_id": "PATH-S06",
                "category": "security",
                "status": "inconclusive",
            },
            packet["supplemental_candidate_result"]["nonpassing_tests"],
        )

    def test_accepted_candidate_can_receive_later_qualification(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-xss-initial-01",
        )

        self.assertEqual(packet["status"], "pending_human_review")
        self.assertEqual(
            packet["original_primary_review"]["verdict"],
            "ACCEPT_CANDIDATE",
        )
        self.assertEqual(packet["attempt"], 1)
        self.assertIn(
            {
                "test_id": "XSS-P01",
                "category": "behavioral_parity",
                "status": "fail",
            },
            packet["supplemental_candidate_result"]["nonpassing_tests"],
        )
        self.assertIn("qualification", packet["purpose"])
        self.assertEqual(
            packet["effect_on_primary_record"],
            "none_original_record_is_preserved",
        )

    def test_packet_binds_original_and_supplemental_evidence(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-xss-initial-04",
        )

        self.assertEqual(packet["status"], "pending_human_review")
        self.assertEqual(
            packet["original_primary_review"]["verdict"],
            "REQUEST_ADDITIONAL_TESTING",
        )
        self.assertEqual(packet["attempt"], 4)
        self.assertIn(
            {
                "test_id": "XSS-P01",
                "category": "behavioral_parity",
                "status": "fail",
            },
            packet["supplemental_candidate_result"]["nonpassing_tests"],
        )
        self.assertEqual(
            packet["effect_on_primary_record"],
            "none_original_record_is_preserved",
        )

    def test_record_requires_explicit_checks_and_does_not_overwrite(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-path-traversal-initial-01",
        )
        with tempfile.TemporaryDirectory() as temporary:
            packet_path = Path(temporary) / "packet.json"
            output_path = Path(temporary) / "result.json"
            from fixproof.evaluation.supplemental_protocol import write_json

            write_json(packet_path, packet)
            with self.assertRaises(ValueError):
                record_follow_up(
                    PROJECT_ROOT,
                    packet_path,
                    output_path,
                    "Tony Tran",
                    "FOLLOW_UP_REJECT_CANDIDATE",
                    "This rationale is intentionally long enough for testing.",
                    False,
                )

    def test_short_rationale_is_rejected(self) -> None:
        packet = build_follow_up_packet(
            PROJECT_ROOT,
            "primary-v1-xss-initial-05",
        )
        with tempfile.TemporaryDirectory() as temporary:
            packet_path = Path(temporary) / "packet.json"
            output_path = Path(temporary) / "result.json"
            from fixproof.evaluation.supplemental_protocol import write_json

            write_json(packet_path, packet)
            with self.assertRaises(ValueError):
                record_follow_up(
                    PROJECT_ROOT,
                    packet_path,
                    output_path,
                    "Tony Tran",
                    "FOLLOW_UP_ACCEPT_CANDIDATE",
                    "Too short.",
                    True,
                )

    def test_completed_result_is_separate_from_primary_review(self) -> None:
        packet_path = (
            PROJECT_ROOT
            / "data/supplemental/v1/follow-up-reviews"
            / "primary-v1-xss-initial-04/packet.json"
        )
        allowed_root = (
            PROJECT_ROOT / "data/supplemental/v1/follow-up-reviews"
        )
        with tempfile.TemporaryDirectory(dir=allowed_root) as temporary:
            output_path = Path(temporary) / "result.json"
            result = record_follow_up(
                PROJECT_ROOT,
                packet_path,
                output_path,
                "Tony Tran",
                "FOLLOW_UP_REJECT_CANDIDATE",
                (
                    "I reviewed the patch and supplemental evidence. The "
                    "registered parity failure supports this test conclusion."
                ),
                True,
            )

            self.assertEqual(result["status"], "completed")
            self.assertTrue(output_path.is_file())
            self.assertEqual(
                result["effect_on_primary_record"],
                "none_original_record_is_preserved",
            )


if __name__ == "__main__":
    unittest.main()
