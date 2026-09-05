from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fixproof.evaluation.adjudication import main


class AdjudicationCliTests(unittest.TestCase):
    def test_rationale_file_preserves_quotes_newlines_and_windows_bom(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rationale = 'Test fixture only: encodes &<>"\' correctly.\nSecond evidence observation.'
            (root / 'review.txt').write_text(rationale, encoding='utf-8-sig')
            argv = ['adjudication', 'record', '--project-root', str(root),
                    '--packet', 'packet.json', '--output', 'result.json',
                    '--reviewer', 'automated-test-fixture',
                    '--verdict', 'REQUEST_ADDITIONAL_TESTING',
                    '--rationale-file', 'review.txt', '--confirm-all-required-checks']
            with patch('sys.argv', argv), patch(
                'fixproof.evaluation.adjudication.record_completed_result',
                return_value=root / 'result.json',
            ) as record, contextlib.redirect_stdout(io.StringIO()):
                main()
            self.assertEqual(record.call_args.kwargs['rationale'], rationale)
            self.assertTrue(record.call_args.kwargs['confirm_all_required_checks'])
            self.assertFalse((root / 'result.json').exists())

    def test_unreadable_or_conflicting_rationale_inputs_do_not_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = ['adjudication', 'record', '--project-root', temporary,
                    '--packet', 'packet.json', '--output', 'result.json',
                    '--reviewer', 'automated-test-fixture',
                    '--verdict', 'REQUEST_ADDITIONAL_TESTING',
                    '--rationale-file', 'missing.txt']
            for extra in ([], ['--rationale', 'Conflicting inline rationale text']):
                with self.subTest(extra=extra), patch('sys.argv', base + extra), patch(
                    'fixproof.evaluation.adjudication.record_completed_result'
                ) as record, contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        main()
                    self.assertEqual(error.exception.code, 2)
                    record.assert_not_called()


if __name__ == '__main__':
    unittest.main()
