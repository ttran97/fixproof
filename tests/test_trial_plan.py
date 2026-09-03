from __future__ import annotations

import json
import unittest
from pathlib import Path

from fixproof.evaluation.benchmark_verifier import sha256_file


class TrialPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.plan_path = (
            cls.project_root / "data" / "evaluation" / "trial-plan.json"
        )
        cls.plan = json.loads(cls.plan_path.read_text(encoding="utf-8"))

    def test_revised_protocol_document_exists(self) -> None:
        protocol = self.project_root / self.plan["protocol_document"]

        self.assertTrue(protocol.is_file())
        self.assertEqual(self.plan["schema_version"], "0.2")

    def test_primary_scope_is_three_cases_and_fifteen_attempts(self) -> None:
        treatments = self.plan["treatments"]
        benchmarks = self.plan["benchmarks"]

        self.assertEqual(len(benchmarks), 3)
        self.assertEqual(
            {benchmark["cwe"] for benchmark in benchmarks},
            {"CWE-79", "CWE-89", "CWE-22"},
        )
        self.assertEqual(treatments["planned_attempts_per_case"], 5)
        self.assertEqual(
            treatments["planned_primary_attempts"],
            len(benchmarks) * treatments["planned_attempts_per_case"],
        )

    def test_primary_benchmarks_are_frozen_separately_from_pilot_apps(self) -> None:
        for benchmark in self.plan["benchmarks"]:
            self.assertNotEqual(
                benchmark["primary_application"],
                benchmark["pilot_application"],
            )
            self.assertEqual(
                benchmark["primary_baseline_status"],
                "verified_and_frozen",
            )

        self.assertFalse(
            self.plan["pilot_evidence"]["included_in_primary_metrics"]
        )

    def test_ai_contract_and_retry_separation_are_explicit(self) -> None:
        treatment = self.plan["treatments"]
        model_settings = treatment["model_settings"]
        retry = treatment["retry"]

        self.assertEqual(treatment["candidate_generator"], "gpt-5.2")
        self.assertEqual(treatment["prompt_template_version"], "1.0")
        self.assertFalse(model_settings["tools_enabled"])
        self.assertEqual(retry["limit_per_primary_attempt"], 1)
        self.assertEqual(retry["analysis_role"], "paired_secondary_outcome")
        self.assertFalse(retry["included_in_primary_metrics"])
        self.assertTrue(self.plan["candidate_contract"]["receives"])
        self.assertTrue(self.plan["candidate_contract"]["withheld"])
        self.assertTrue(self.plan["candidate_contract"]["returns"])

    def test_sast_only_mapping_and_human_boundary_are_explicit(self) -> None:
        comparison = self.plan["comparison"]

        self.assertEqual(
            comparison["sast_only_mapping"]["resolved"],
            "APPARENT_SUCCESS",
        )
        self.assertEqual(
            comparison["sast_only_mapping"]["persistent"],
            "FAILURE",
        )
        self.assertFalse(comparison["automatic_production_acceptance"])
        self.assertEqual(
            set(comparison["fixproof_dispositions"]),
            {
                "REJECT",
                "READY_FOR_HUMAN_REVIEW",
                "NEEDS_HUMAN_ADJUDICATION",
            },
        )

    def test_completed_controls_freeze_the_protocol(self) -> None:
        scanner_timeout_implemented = self.plan["failure_handling"][
            "scanner_timeout_implemented"
        ]

        self.assertTrue(scanner_timeout_implemented)
        self.assertEqual(
            self.plan["failure_handling"]["scanner_timeout_seconds"],
            120,
        )
        self.assertTrue(self.plan["protocol_frozen"])
        self.assertEqual(
            self.plan["plan_status"],
            "frozen_ready_for_primary_collection",
        )

    def test_freeze_evidence_is_hash_bound(self) -> None:
        for evidence in self.plan["freeze_evidence"].values():
            path = self.project_root / evidence["path"]
            self.assertTrue(path.is_file(), msg=evidence["path"])
            if "sha256" in evidence:
                self.assertRegex(evidence["sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(
                    sha256_file(path),
                    evidence["sha256"],
                    msg=evidence["path"],
                )

        verification_binding = self.plan["freeze_evidence"][
            "baseline_verification"
        ]
        verification_path = self.project_root / verification_binding["path"]
        verification = json.loads(
            verification_path.read_text(encoding="utf-8")
        )
        self.assertEqual(verification["status"], "ready")
        self.assertEqual(
            verification["manifest"]["sha256"],
            verification_binding["manifest_sha256"],
        )
        self.assertEqual(
            verification_binding["manifest_sha256"],
            self.plan["freeze_evidence"]["benchmark_manifest"]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()
