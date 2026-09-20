from __future__ import annotations

import tempfile
import unittest
import urllib.parse
from pathlib import Path

from fixproof.evaluation.supplemental_protocol import sha256_file
from fixproof.evaluation.supplemental_runner import (
    DOTFILE_CONTENT,
    SPACEFILE_CONTENT,
    build_urls,
    ensure_supplemental_output_root,
    evaluate_baseline_case,
    evaluate_candidate_case,
    prepare_disposable_app,
    summarize_candidate_cases,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SupplementalRunnerTests(unittest.TestCase):
    def test_output_must_stay_in_supplemental_runs(self) -> None:
        allowed = ensure_supplemental_output_root(
            PROJECT_ROOT,
            Path("data/supplemental/v1/runs"),
        )
        self.assertEqual(
            allowed,
            (PROJECT_ROOT / "data/supplemental/v1/runs").resolve(),
        )

        with self.assertRaises(ValueError):
            ensure_supplemental_output_root(
                PROJECT_ROOT,
                Path("data/primary_trials/v1"),
            )

    def test_repeated_query_values_are_not_collapsed(self) -> None:
        urls = build_urls(
            3000,
            "/hello",
            "name",
            {
                "mode": "pairs",
                "pairs": [["name", "Tony"], ["name", "Admin"]],
            },
            {},
        )
        query = urllib.parse.urlsplit(urls[0]["url"]).query
        self.assertEqual(
            urllib.parse.parse_qs(query),
            {"name": ["Tony", "Admin"]},
        )

    def test_path_fixture_is_disposable_and_preserves_source(self) -> None:
        source = PROJECT_ROOT / "benchmarks/primary/v1/path-traversal"
        source_hash = sha256_file(source / "app.js")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "app"
            result = prepare_disposable_app(
                source,
                "path-traversal",
                destination,
            )

            self.assertEqual(
                (destination / "public-files/..notes.txt").read_bytes(),
                DOTFILE_CONTENT.encode("utf-8"),
            )
            self.assertEqual(
                (
                    destination / "public-files/annual report 2026.txt"
                ).read_bytes(),
                SPACEFILE_CONTENT.encode("utf-8"),
            )
            self.assertEqual(result["source_app_sha256"], source_hash)
            self.assertEqual(sha256_file(source / "app.js"), source_hash)

    def test_sql_seed_transform_changes_only_disposable_copy(self) -> None:
        source = PROJECT_ROOT / "benchmarks/primary/v1/sqli"
        source_text = (source / "app.js").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "app"
            prepare_disposable_app(source, "sqli", destination)
            candidate_text = (destination / "app.js").read_text(
                encoding="utf-8"
            )

        self.assertNotIn('statement.run("o\'connor"', source_text)
        self.assertIn('statement.run("o\'connor"', candidate_text)
        self.assertEqual(
            (source / "app.js").read_text(encoding="utf-8"),
            source_text,
        )

    def test_xss_missing_input_baseline_oracle(self) -> None:
        evidence = {
            "observations": [
                {
                    "browser": {
                        "status": "observed",
                        "http_status": 200,
                        "h1_texts": ["Hello undefined"],
                    }
                }
            ]
        }
        result = evaluate_baseline_case("xss", "XSS-P01", evidence)
        self.assertEqual(result["status"], "match")

    def test_symlink_unavailability_is_inconclusive(self) -> None:
        result = evaluate_baseline_case(
            "path-traversal",
            "PATH-S06",
            {"fixture_unavailable": True},
        )
        self.assertEqual(result["status"], "inconclusive")

    def test_xss_missing_input_change_fails_parity_oracle(self) -> None:
        evidence = {
            "observations": [
                {
                    "browser": {
                        "status": "observed",
                        "http_status": 200,
                        "dialogs": [],
                        "h1_count": 1,
                        "h1_texts": ["Hello "],
                        "active_element_counts": {
                            "script": 0,
                            "img": 0,
                            "svg": 0,
                            "input": 0,
                            "b": 0,
                        },
                    }
                }
            ]
        }
        result = evaluate_candidate_case("xss", "XSS-P01", evidence)
        self.assertEqual(result["status"], "fail")

    def test_path_400_json_conforms_to_robustness_contract(self) -> None:
        evidence = {
            "observations": [
                {
                    "http": {
                        "status_code": 400,
                        "body": '{"error":"Invalid path"}',
                    }
                }
            ]
        }
        result = evaluate_candidate_case(
            "path-traversal",
            "PATH-R01",
            evidence,
        )
        self.assertEqual(result["status"], "pass")

    def test_sqli_attack_requires_zero_rows(self) -> None:
        safe = {
            "observations": [
                {"http": {"status_code": 200, "body": "[]"}}
            ]
        }
        exposed = {
            "observations": [
                {
                    "http": {
                        "status_code": 200,
                        "body": '[{"username":"alice"}]',
                    }
                }
            ]
        }
        self.assertEqual(
            evaluate_candidate_case("sqli", "SQL-S01", safe)["status"],
            "pass",
        )
        self.assertEqual(
            evaluate_candidate_case("sqli", "SQL-S01", exposed)["status"],
            "fail",
        )

    def test_candidate_summary_keeps_categories_separate(self) -> None:
        cases = [
            {
                "category": "security",
                "candidate_expectation_evaluation": {"status": "pass"},
            },
            {
                "category": "behavioral_parity",
                "candidate_expectation_evaluation": {"status": "fail"},
            },
            {
                "category": "robustness_contract",
                "candidate_expectation_evaluation": {
                    "status": "inconclusive"
                },
            },
        ]
        result = summarize_candidate_cases(cases)

        self.assertEqual(result["pass"], 1)
        self.assertEqual(result["fail"], 1)
        self.assertEqual(result["inconclusive"], 1)
        self.assertFalse(result["automatic_acceptance"])
        self.assertEqual(result["by_category"]["security"]["pass"], 1)


if __name__ == "__main__":
    unittest.main()
