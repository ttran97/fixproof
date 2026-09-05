from __future__ import annotations

import argparse
import posixpath
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """Serve only the dashboard assets and generated evaluation report."""

    allowed_exact_paths = {
        "/data/evaluation/experiment-report.json",
        "/data/evaluation/primary-report.json",
    }
    allowed_prefixes = (
        "/ui/",
    )

    def _request_path(self) -> str:
        decoded = unquote(urlsplit(self.path).path).replace("\\", "/")
        normalized = "/" + posixpath.normpath(decoded).lstrip("/")
        if decoded.endswith("/") and not normalized.endswith("/"):
            normalized += "/"
        return normalized

    def _is_allowed(self, request_path: str) -> bool:
        return (
            request_path in self.allowed_exact_paths
            or request_path.startswith(self.allowed_prefixes)
        )

    def _redirect_root(self) -> None:
        self.send_response(302)
        self.send_header("Location", "/ui/")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - inherited HTTP method name
        request_path = self._request_path()
        if request_path == "/":
            self._redirect_root()
            return
        if not self._is_allowed(request_path):
            self.send_error(404, "Dashboard resource not found")
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - inherited HTTP method name
        request_path = self._request_path()
        if request_path == "/":
            self._redirect_root()
            return
        if not self._is_allowed(request_path):
            self.send_error(404, "Dashboard resource not found")
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def create_dashboard_server(
    project_root: Path,
    bind: str,
    port: int,
) -> ThreadingHTTPServer:
    project_root = project_root.resolve()
    required_files = (
        project_root / "ui" / "index.html",
        project_root / "ui" / "app.js",
        project_root / "ui" / "styles.css",
        project_root / "data" / "evaluation" / "experiment-report.json",
    )
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Dashboard inputs are missing: " + ", ".join(missing)
        )

    handler = partial(DashboardRequestHandler, directory=str(project_root))
    return ThreadingHTTPServer((bind, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the read-only FixProof evaluation dashboard locally."
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = create_dashboard_server(
        project_root=args.project_root,
        bind=args.bind,
        port=args.port,
    )
    host, port = server.server_address[:2]
    print("=" * 60)
    print("FixProof Read-Only Evaluation Dashboard")
    print("=" * 60)
    print(f"URL: http://{host}:{port}/ui/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
