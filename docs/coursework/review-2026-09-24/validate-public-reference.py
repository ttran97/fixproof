"""Browser and privacy checks for the static FixProof public reference."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "fixproof-public"
SCREENSHOT = Path(__file__).resolve().parent / "fixproof-public-preview.png"
URL = os.environ.get("FIXPROOF_PUBLIC_URL", "http://127.0.0.1:8765/")
if URL.startswith("https://"):
    SCREENSHOT = Path(__file__).resolve().parent / "fixproof-netlify-preview.png"


def main() -> None:
    raw = (PUBLIC / "data" / "public-evidence.json").read_text(encoding="utf-8")
    evidence = json.loads(raw)

    assert len(evidence["candidates"]) == 15
    assert sum(bool(item["primary"]["original_human"]) for item in evidence["candidates"]) == 10
    assert sum(bool(item["supplemental"]["later_human"]) for item in evidence["candidates"]) == 14
    assert evidence["supplemental_summary"]["candidate_case_observations"] == {
        "total": 140,
        "pass": 120,
        "fail": 15,
        "inconclusive": 5,
    }
    for marker in ("C:\\\\Users\\\\", "resp_", "OPENAI_API_KEY", '"sha256"'):
        assert marker not in raw, f"Forbidden public-data marker: {marker}"

    page_errors: list[str] = []
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        response = page.goto(URL, wait_until="networkidle")
        assert response is not None and response.ok
        assert page.locator("#primary-body tr").count() == 15
        assert page.locator("#supplemental-body tr").count() == 15
        assert page.locator("#metric-grid .metric-card").count() == 4
        assert "140" in page.locator("#metric-grid").inner_text()

        page.locator(
            '#primary-body button[data-candidate="primary-v1-xss-initial-04"]'
        ).click()
        dialog = page.locator("#candidate-dialog")
        assert dialog.is_visible()
        detail = dialog.inner_text()
        assert "XSS-P01" in detail
        assert "Reject candidate" in detail
        assert "String(value ?? \"\")" in detail
        page.locator("#dialog-close").click()

        page.locator("#case-filter").select_option("sqli")
        assert page.locator("#primary-body tr").count() == 5
        assert page.locator("#supplemental-body tr").count() == 5
        page.locator("#case-filter").select_option("all")

        page.screenshot(path=str(SCREENSHOT), full_page=True)
        browser.close()

    # Netlify's preview/injection layer can attempt an inline style or script.
    # The site's strict CSP correctly blocks those optional injections. Treat
    # only those host-generated CSP messages as expected warnings; application
    # errors and all other console errors still fail validation.
    expected_netlify_csp = [
        message
        for message in console_errors
        if URL.startswith("https://")
        and "Content Security Policy" in message
        and ("inline style" in message or "inline script" in message)
    ]
    unexpected_console_errors = [
        message for message in console_errors if message not in expected_netlify_csp
    ]

    assert not page_errors, page_errors
    assert not unexpected_console_errors, unexpected_console_errors
    print("Public reference validation passed")
    print("Primary rows: 15; supplemental rows: 15")
    print("Original reviews: 10; later records: 14")
    if expected_netlify_csp:
        print(
            "Expected hosting-layer CSP blocks: "
            f"{len(expected_netlify_csp)} (site application unaffected)"
        )
    print(f"Screenshot: {SCREENSHOT}")


if __name__ == "__main__":
    main()
