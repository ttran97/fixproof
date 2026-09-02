from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fixproof.agent import remediation_agent
from fixproof.config import (
    EnvironmentFileError,
    find_environment_file,
    load_environment_file,
)


class EnvironmentFileTests(unittest.TestCase):
    def test_only_approved_nonempty_settings_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment_file = Path(directory) / ".env"
            environment_file.write_text(
                "# local configuration\n"
                "OPENAI_API_KEY='test-key'\n"
                'FIXPROOF_MODEL="test-model"\n'
                "UNRELATED_SECRET=must-not-load\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                loaded = load_environment_file(environment_file)

                self.assertEqual(
                    loaded,
                    ("OPENAI_API_KEY", "FIXPROOF_MODEL"),
                )
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")
                self.assertEqual(os.environ["FIXPROOF_MODEL"], "test-model")
                self.assertNotIn("UNRELATED_SECRET", os.environ)

    def test_shell_environment_takes_precedence_and_blank_values_are_ignored(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment_file = Path(directory) / ".env"
            environment_file.write_text(
                "OPENAI_API_KEY=file-key\nFIXPROOF_MODEL=\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "shell-key"},
                clear=True,
            ):
                loaded = load_environment_file(environment_file)

                self.assertEqual(loaded, ())
                self.assertEqual(os.environ["OPENAI_API_KEY"], "shell-key")
                self.assertNotIn("FIXPROOF_MODEL", os.environ)

    def test_malformed_environment_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment_file = Path(directory) / ".env"
            environment_file.write_text(
                'OPENAI_API_KEY="unterminated\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(EnvironmentFileError, "Unterminated"):
                load_environment_file(environment_file)

            with self.assertRaisesRegex(EnvironmentFileError, "not found"):
                load_environment_file(
                    Path(directory) / "missing.env",
                    required=True,
                )

    def test_nearest_environment_file_is_found(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment_file = root / ".env"
            environment_file.write_text("FIXPROOF_MODEL=test-model\n")
            nested = root / "data" / "prompts"
            nested.mkdir(parents=True)

            self.assertEqual(
                find_environment_file(nested),
                environment_file.resolve(),
            )

    def test_remediation_cli_loads_nearest_environment_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt_dir = root / "data" / "prompts"
            prompt_dir.mkdir(parents=True)
            prompt_file = prompt_dir / "case.json"
            prompt_file.write_text('{"prompts": []}', encoding="utf-8")
            output_file = root / "candidate.json"
            (root / ".env").write_text(
                "OPENAI_API_KEY=test-key\nFIXPROOF_MODEL=test-model\n",
                encoding="utf-8",
            )

            arguments = [
                "remediation_agent",
                "--input",
                str(prompt_file),
                "--canonical-id",
                "CF-test",
                "--output",
                str(output_file),
            ]
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(sys, "argv", arguments),
                patch.object(remediation_agent, "run_remediation") as run,
            ):
                remediation_agent.main()

                run.assert_called_once_with(
                    prompt_file=prompt_file,
                    output_file=output_file,
                    canonical_id="CF-test",
                    model="test-model",
                )
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")


if __name__ == "__main__":
    unittest.main()
