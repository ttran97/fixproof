from __future__ import annotations

import urllib.parse
from typing import Any


BROWSER_TIMEOUT_MILLISECONDS = 5_000
BROWSER_SETTLE_MILLISECONDS = 250


def build_browser_url(
    host: str,
    port: int,
    route: str,
    parameter: str,
    payload: str,
) -> str:
    query = urllib.parse.urlencode({parameter: payload})
    return f"http://{host}:{port}{route}?{query}"


def run_browser_xss_test(
    host: str,
    port: int,
    route: str,
    parameter: str,
    payload: str,
    *,
    timeout_milliseconds: int = BROWSER_TIMEOUT_MILLISECONDS,
) -> dict[str, Any]:
    """Execute one controlled XSS payload in headless Chromium.

    The fixed FixProof XSS payloads call ``alert(1)`` when JavaScript executes.
    Playwright dismisses the dialog and records it as execution evidence.
    """

    url = build_browser_url(
        host=host,
        port=port,
        route=route,
        parameter=parameter,
        payload=payload,
    )

    try:
        from playwright.sync_api import (
            Error as PlaywrightError,
            TimeoutError as PlaywrightTimeoutError,
            sync_playwright,
        )
    except ImportError as exc:
        return {
            "status": "inconclusive",
            "executed": None,
            "url": url,
            "browser": "chromium",
            "dialogs": [],
            "http_status": None,
            "error": f"Playwright is not installed: {exc}",
        }

    dialogs: list[dict[str, str]] = []

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()

                def record_dialog(dialog: Any) -> None:
                    dialogs.append(
                        {
                            "type": dialog.type,
                            "message": dialog.message,
                        }
                    )
                    dialog.dismiss()

                page.on("dialog", record_dialog)
                response = page.goto(
                    url,
                    wait_until="load",
                    timeout=timeout_milliseconds,
                )
                page.wait_for_timeout(BROWSER_SETTLE_MILLISECONDS)

                executed = bool(dialogs)

                return {
                    "status": "executed" if executed else "not_executed",
                    "executed": executed,
                    "url": url,
                    "browser": "chromium",
                    "dialogs": dialogs,
                    "http_status": response.status if response else None,
                    "error": None,
                }
            finally:
                browser.close()

    except (PlaywrightTimeoutError, PlaywrightError, OSError) as exc:
        return {
            "status": "inconclusive",
            "executed": None,
            "url": url,
            "browser": "chromium",
            "dialogs": dialogs,
            "http_status": None,
            "error": str(exc),
        }


def combine_xss_evidence(
    http_evaluation: dict[str, Any],
    browser_evaluation: dict[str, Any],
) -> dict[str, str]:
    """Require both safe reflected output and no browser execution."""

    http_status = http_evaluation["status"]
    browser_status = browser_evaluation["status"]

    if browser_status == "executed":
        return {
            "status": "fail",
            "reason": "The controlled payload executed in headless Chromium.",
        }

    if http_status == "fail":
        return {
            "status": "fail",
            "reason": http_evaluation["reason"],
        }

    if http_status == "inconclusive" or browser_status == "inconclusive":
        return {
            "status": "inconclusive",
            "reason": (
                "HTTP reflection or browser-execution evidence was "
                "inconclusive."
            ),
        }

    return {
        "status": "pass",
        "reason": (
            "The payload was not present as unsafe reflected markup and did "
            "not execute in headless Chromium."
        ),
    }

