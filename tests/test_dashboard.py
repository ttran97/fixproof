from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fixproof.evaluation.dashboard import create_dashboard_server


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]

    def test_dashboard_serves_only_ui_and_report(self) -> None:
        server = create_dashboard_server(
            project_root=self.project_root,
            bind="127.0.0.1",
            port=0,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address[:2]
        base_url = f"http://{host}:{port}"

        try:
            with urlopen(f"{base_url}/ui/", timeout=5) as response:
                html = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("FixProof Evaluation Dashboard", html)
                self.assertIn("/ui/app.js", html)

            with urlopen(
                f"{base_url}/data/evaluation/experiment-report.json",
                timeout=5,
            ) as response:
                report = json.loads(response.read().decode("utf-8"))
                self.assertEqual(report["attempt_count"], 4)
                self.assertEqual(report["control_count"], 1)
                self.assertEqual(
                    response.headers["X-Content-Type-Options"], "nosniff"
                )

            with self.assertRaises(HTTPError) as blocked:
                urlopen(f"{base_url}/README.md", timeout=5)
            self.assertEqual(blocked.exception.code, 404)

            with urlopen(f"{base_url}/ui/primary.html", timeout=5) as response:
                self.assertIn("FixProof Primary Study", response.read().decode("utf-8"))
            with urlopen(f"{base_url}/data/evaluation/primary-report.json", timeout=5) as response:
                primary = json.loads(response.read().decode("utf-8"))
                self.assertEqual(primary["attempt_count"], 15)
                self.assertLessEqual(primary["adjudication_summary"]["completed"],
                                     primary["adjudication_summary"]["required"])
            for raw_path in ("/data/primary_trials/v1/collection-state.json",
                             "/data/primary_reviews/v1/primary-v1-xss-initial-01/packet.json"):
                with self.assertRaises(HTTPError) as blocked_raw:
                    urlopen(f"{base_url}{raw_path}", timeout=5)
                self.assertEqual(blocked_raw.exception.code, 404)

            for secret_path in ("/.env", "/.env.example"):
                with self.subTest(secret_path=secret_path):
                    with self.assertRaises(HTTPError) as secret:
                        urlopen(f"{base_url}{secret_path}", timeout=5)
                    self.assertEqual(secret.exception.code, 404)

            with self.assertRaises(HTTPError) as traversal:
                urlopen(f"{base_url}/ui/%2e%2e/README.md", timeout=5)
            self.assertEqual(traversal.exception.code, 404)

            with self.assertRaises(HTTPError) as blocked_head:
                urlopen(Request(f"{base_url}/README.md", method="HEAD"), timeout=5)
            self.assertEqual(blocked_head.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
