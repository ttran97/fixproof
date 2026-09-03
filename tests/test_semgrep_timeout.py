from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fixproof.scanners.semgrep_runner import (
    DEFAULT_SEMGREP_TIMEOUT_SECONDS,
    run_semgrep,
)


class SemgrepTimeoutTests(unittest.TestCase):
    @patch("fixproof.scanners.semgrep_runner.subprocess.run")
    def test_default_timeout_is_passed_to_subprocess(self, run_mock) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "app.js"
            output = root / "scan.json"
            target.write_text("const app = {};\n", encoding="utf-8")
            output.write_text("{}\n", encoding="utf-8")
            run_mock.return_value = SimpleNamespace(returncode=0)

            run_semgrep(
                target=target,
                output=output,
                project_rule_dir=root / "missing-rules",
            )

            self.assertEqual(
                run_mock.call_args.kwargs["timeout"],
                DEFAULT_SEMGREP_TIMEOUT_SECONDS,
            )

    @patch("fixproof.scanners.semgrep_runner.subprocess.run")
    def test_process_timeout_becomes_clear_runtime_error(
        self,
        run_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "app.js"
            target.write_text("const app = {};\n", encoding="utf-8")
            run_mock.side_effect = subprocess.TimeoutExpired(
                cmd=["semgrep"],
                timeout=7,
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "fixed process timeout of 7 seconds",
            ):
                run_semgrep(
                    target=target,
                    output=root / "scan.json",
                    project_rule_dir=root / "missing-rules",
                    timeout_seconds=7,
                )

    def test_nonpositive_timeout_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "app.js"
            target.write_text("const app = {};\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "greater than zero"):
                run_semgrep(
                    target=target,
                    output=root / "scan.json",
                    project_rule_dir=root / "missing-rules",
                    timeout_seconds=0,
                )


if __name__ == "__main__":
    unittest.main()
