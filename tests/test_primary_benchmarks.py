from __future__ import annotations

import json
import unittest
from pathlib import Path

from fixproof.evaluation.benchmark_verifier import (
    sha256_file,
    verify_file_bindings,
    verify_restore_copy,
)
from fixproof.validation.functional_validator import (
    FUNCTIONAL_TESTS,
    PATH_TRAVERSAL_FUNCTIONAL_TESTS,
    SQLI_FUNCTIONAL_TESTS,
)
from fixproof.validation.security_validator import (
    PATH_TRAVERSAL_SECURITY_TESTS,
    SQLI_SECURITY_TESTS,
    XSS_PAYLOADS,
)


class PrimaryBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.manifest_path = (
            cls.project_root
            / "data"
            / "evaluation"
            / "primary-benchmark-manifest.json"
        )
        cls.manifest = json.loads(
            cls.manifest_path.read_text(encoding="utf-8")
        )

    def test_manifest_has_one_target_only_application_per_cwe(self) -> None:
        cases = self.manifest["cases"]

        self.assertTrue(self.manifest["suite_frozen"])
        self.assertEqual(self.manifest["frozen_at"], "2026-09-03")
        self.assertEqual(len(cases), 3)
        self.assertEqual(
            {case["cwe"] for case in cases},
            {"CWE-79", "CWE-89", "CWE-22"},
        )
        for case in cases:
            self.assertEqual(case["intentionally_seeded_vulnerabilities"], [case["cwe"]])
            source = self.project_root / case["source_file"]
            self.assertEqual(source.read_text(encoding="utf-8").count("app.get("), 1)

    def test_manifest_hashes_bind_every_baseline_file(self) -> None:
        for case in self.manifest["cases"]:
            result = verify_file_bindings(self.project_root, case)
            self.assertEqual(result["status"], "pass", msg=case["case_id"])
            for binding in case["files"]:
                path = self.project_root / binding["path"]
                self.assertEqual(sha256_file(path), binding["sha256"])

    def test_clean_restore_reproduces_bound_files(self) -> None:
        for case in self.manifest["cases"]:
            result = verify_restore_copy(self.project_root, case)
            self.assertEqual(result["status"], "pass", msg=case["case_id"])

    def test_manifest_test_counts_match_validator_contracts(self) -> None:
        expected = {
            "xss": (XSS_PAYLOADS, FUNCTIONAL_TESTS),
            "sqli": (SQLI_SECURITY_TESTS, SQLI_FUNCTIONAL_TESTS),
            "path-traversal": (
                PATH_TRAVERSAL_SECURITY_TESTS,
                PATH_TRAVERSAL_FUNCTIONAL_TESTS,
            ),
        }

        for case in self.manifest["cases"]:
            security, functional = expected[case["case_id"]]
            self.assertEqual(case["tests"]["security"]["count"], len(security))
            self.assertEqual(case["tests"]["functional"]["count"], len(functional))
            self.assertEqual(
                case["tests"]["security"]["names"],
                [test["name"] for test in security],
            )
            self.assertEqual(
                case["tests"]["functional"]["names"],
                [test["name"] for test in functional],
            )

    def test_xss_requires_browser_execution_ground_truth(self) -> None:
        xss = next(case for case in self.manifest["cases"] if case["case_id"] == "xss")

        self.assertTrue(xss["tests"]["security"]["browser_execution_required"])
        self.assertEqual(
            xss["tests"]["security"]["expected_browser_executions"],
            len(XSS_PAYLOADS),
        )


if __name__ == "__main__":
    unittest.main()
