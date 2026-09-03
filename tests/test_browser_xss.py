from __future__ import annotations

import unittest

from fixproof.validation.browser_xss import (
    build_browser_url,
    combine_xss_evidence,
)


class BrowserXssTests(unittest.TestCase):
    def test_browser_url_encodes_payload(self) -> None:
        url = build_browser_url(
            host="127.0.0.1",
            port=3000,
            route="/hello",
            parameter="name",
            payload="<script>alert(1)</script>",
        )

        self.assertTrue(url.startswith("http://127.0.0.1:3000/hello?"))
        self.assertIn("name=%3Cscript%3Ealert%281%29%3C%2Fscript%3E", url)

    def test_executed_payload_fails_even_when_http_appears_safe(self) -> None:
        result = combine_xss_evidence(
            http_evaluation={"status": "pass", "reason": "safe"},
            browser_evaluation={"status": "executed"},
        )

        self.assertEqual(result["status"], "fail")

    def test_both_evidence_channels_must_pass(self) -> None:
        result = combine_xss_evidence(
            http_evaluation={"status": "pass", "reason": "safe"},
            browser_evaluation={"status": "not_executed"},
        )

        self.assertEqual(result["status"], "pass")

    def test_missing_browser_evidence_is_inconclusive(self) -> None:
        result = combine_xss_evidence(
            http_evaluation={"status": "pass", "reason": "safe"},
            browser_evaluation={"status": "inconclusive"},
        )

        self.assertEqual(result["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
