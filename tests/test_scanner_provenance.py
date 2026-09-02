from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fixproof.agent.context_builder import build_contexts
from fixproof.agent.prompt_builder import build_prompt
from fixproof.findings.finding_correlator import correlate_findings
from fixproof.scanners.semgrep_parser import parse_semgrep
from fixproof.scanners.semgrep_runner import build_semgrep_command


class ScannerProvenanceTests(unittest.TestCase):
    def test_command_combines_auto_local_and_additional_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "app.js"
            output = root / "scan.json"
            rules = root / "rules"

            target.write_text("const app = {};\n", encoding="utf-8")
            rules.mkdir()

            command = build_semgrep_command(
                target=target,
                output=output,
                project_rule_dir=rules,
                additional_configs=["extra.yml"],
            )

            self.assertEqual(
                command[:4],
                ["semgrep", "scan", "--config", "auto"],
            )
            self.assertIn(str(rules.resolve()), command)
            self.assertIn("extra.yml", command)
            self.assertEqual(command[-1], str(target))

    def test_rule_origin_survives_the_preparation_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "app.js"
            raw = root / "raw.json"
            normalized_path = root / "normalized.json"
            correlated_path = root / "correlated.json"
            contexts_path = root / "contexts.json"

            source.write_text(
                "const express = require('express');\n"
                "const app = express();\n"
                "app.get('/user', (req, res) => {\n"
                "  const query = req.query.username;\n"
                "  db.all(query, () => {});\n"
                "});\n",
                encoding="utf-8",
            )

            raw.write_text(
                json.dumps(
                    {
                        "version": "test",
                        "engine_requested": "OSS",
                        "paths": {"scanned": ["app.js"]},
                        "errors": [],
                        "results": [
                            {
                                "check_id": "rules.fixproof.sqli",
                                "path": "app.js",
                                "start": {"line": 5},
                                "end": {"line": 5},
                                "extra": {
                                    "engine_kind": "OSS",
                                    "severity": "ERROR",
                                    "message": "Controlled SQLi finding",
                                    "metadata": {
                                        "cwe": "CWE-89",
                                        "confidence": "HIGH",
                                        "fixproof_controlled_rule": True,
                                    },
                                },
                            },
                            {
                                "check_id": "javascript.express.csrf",
                                "path": "app.js",
                                "start": {"line": 2},
                                "end": {"line": 2},
                                "extra": {
                                    "engine_kind": "OSS",
                                    "severity": "INFO",
                                    "message": "OSS CSRF finding",
                                    "metadata": {
                                        "cwe": "CWE-352: CSRF",
                                        "confidence": "LOW",
                                    },
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            normalized = parse_semgrep(
                input_file=raw,
                output_file=normalized_path,
                source_root=root,
            )
            correlated = correlate_findings(
                input_file=normalized_path,
                output_file=correlated_path,
            )
            contexts = build_contexts(
                input_file=correlated_path,
                output_file=contexts_path,
                project_root=root,
            )

            self.assertEqual(
                normalized["scan"]["finding_count_by_rule_origin"],
                {"fixproof_controlled": 1, "semgrep_oss": 1},
            )

            normalized_origins = {
                finding["rule_origin"]
                for finding in normalized["findings"]
            }
            self.assertEqual(
                normalized_origins,
                {"fixproof_controlled", "semgrep_oss"},
            )

            correlated_origins = {
                origin
                for finding in correlated["findings"]
                for origin in finding["rule_origins"]
            }
            self.assertEqual(
                correlated_origins,
                {"fixproof_controlled", "semgrep_oss"},
            )

            context_origins = {
                origin
                for context in contexts["contexts"]
                for origin in context["scanner_evidence"]["rule_origins"]
            }
            self.assertEqual(
                context_origins,
                {"fixproof_controlled", "semgrep_oss"},
            )

            controlled_context = next(
                context
                for context in contexts["contexts"]
                if context["finding"]["cwe"] == "CWE-89"
            )
            self.assertIn(
                "origin: fixproof_controlled",
                build_prompt(controlled_context),
            )


if __name__ == "__main__":
    unittest.main()
