"""Browser and privacy checks for the static FixProof public reference."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "fixproof-public"
SCREENSHOT = Path(__file__).resolve().parent / "fixproof-public-preview.png"
EVIDENCE_SCREENSHOT = (
    Path(__file__).resolve().parent / "fixproof-student-test-evidence-preview.png"
)
URL = os.environ.get("FIXPROOF_PUBLIC_URL", "http://127.0.0.1:8765/")
if URL.startswith("https://"):
    SCREENSHOT = Path(__file__).resolve().parent / "fixproof-netlify-preview.png"
    EVIDENCE_SCREENSHOT = (
        Path(__file__).resolve().parent / "fixproof-netlify-test-evidence-preview.png"
    )


def main() -> None:
    raw = (PUBLIC / "data" / "public-evidence.json").read_text(encoding="utf-8")
    evidence = json.loads(raw)

    assert len(evidence["candidates"]) == 15
    assert sum(bool(item["primary"]["original_human"]) for item in evidence["candidates"]) == 10
    assert sum(bool(item["supplemental"]["later_human"]) for item in evidence["candidates"]) == 14
    assert sum(bool(item["path_s06_extension"]) for item in evidence["candidates"]) == 5
    assert evidence["path_s06_extension_summary"]["candidate_observations"] == {
        "pass": 0,
        "fail": 5,
        "inconclusive": 0,
    }
    assert evidence["path_s06_extension_summary"]["human_qualifications"] == 5
    assert evidence["supplemental_summary"]["candidate_case_observations"] == {
        "total": 140,
        "pass": 120,
        "fail": 15,
        "inconclusive": 5,
    }
    for marker in ("C:\\\\Users\\\\", "resp_", "OPENAI_API_KEY", '"sha256"'):
        assert marker not in raw, f"Forbidden public-data marker: {marker}"

    case_raw = (PUBLIC / "data" / "student-test-evidence.json").read_text(
        encoding="utf-8"
    )
    case_evidence = json.loads(case_raw)
    assert len(case_evidence["candidate_summary"]) == 15
    assert len(case_evidence["primary_cases"]) == 100
    assert len(case_evidence["supplemental_cases"]) == 140
    assert len(case_evidence["path_s06_extension"]) == 5
    assert len(case_evidence["human_decisions"]) == 29
    assert (
        sum(
            row["Result"] == "PASS"
            for row in case_evidence["supplemental_cases"]
        )
        == 120
    )
    assert (
        sum(
            row["Result"] == "FAIL"
            for row in case_evidence["supplemental_cases"]
        )
        == 15
    )
    assert (
        sum(
            row["Result"] == "INCONCLUSIVE"
            for row in case_evidence["supplemental_cases"]
        )
        == 5
    )
    for marker in (
        "C:\\Users\\",
        "C:\\\\Users\\\\",
        "/mnt/c/Users/",
        "/home/tony",
        "resp_",
        "OPENAI_API_KEY",
    ):
        assert marker not in case_raw, f"Forbidden case-export marker: {marker}"

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
        assert page.locator("#metric-grid .metric-card").count() == 5
        assert "140" in page.locator("#metric-grid").inner_text()
        assert "5/5" in page.locator("#metric-grid").inner_text()

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

        page.locator(
            '#primary-body button[data-candidate="primary-v1-path-traversal-initial-02"]'
        ).click()
        assert dialog.is_visible()
        path_detail = dialog.inner_text()
        assert "PATH-S06 extension" in path_detail
        assert "HTTP STATUS" in path_detail and "200" in path_detail
        assert "OUTSIDE MARKER DISCLOSED" in path_detail and "Yes" in path_detail
        assert "Traversal 02 spot-check" in path_detail
        assert "Reject candidate" in path_detail
        page.locator("#dialog-close").click()

        page.locator("#case-filter").select_option("sqli")
        assert page.locator("#primary-body tr").count() == 5
        assert page.locator("#supplemental-body tr").count() == 5
        page.locator("#case-filter").select_option("all")

        page.screenshot(path=str(SCREENSHOT), full_page=True)

        case_response = page.goto(
            URL.rstrip("/") + "/test-evidence.html", wait_until="networkidle"
        )
        assert case_response is not None and case_response.ok
        assert page.locator("#candidate-body tr").count() == 15
        assert page.locator("#case-body tr").count() == 25
        assert page.locator("#count-body tr").count() == 10
        assert page.locator("#decision-body tr").count() == 29
        assert page.locator("#evidence-metrics .metric-card").count() == 5
        assert "Showing 1–25 of 245 matching rows" in page.locator(
            "#case-result-count"
        ).inner_text()
        assert "Page 1 of 10" in page.locator("#page-status").inner_text()
        page.locator("#next-page").click()
        assert "Showing 26–50 of 245 matching rows" in page.locator(
            "#case-result-count"
        ).inner_text()
        page.locator("#previous-page").click()

        page.locator("#layer-filter").select_option("supplemental-v1")
        assert page.locator("#case-body tr").count() == 25
        page.locator("#result-filter").select_option("FAIL")
        assert page.locator("#case-body tr").count() == 15
        page.locator("#layer-filter").select_option("all")
        assert page.locator("#case-body tr").count() == 20
        page.locator("#result-filter").select_option("all")
        page.locator("#candidate-filter").select_option("XSS 01")
        assert page.locator("#case-body tr").count() == 19
        page.locator("#candidate-filter").select_option("all")
        page.locator("#case-search").fill("PATH-S06")
        assert page.locator("#case-body tr").count() == 10
        page.locator("#case-search").fill("")
        assert page.locator("#case-body tr").count() == 25
        page.screenshot(path=str(EVIDENCE_SCREENSHOT), full_page=True)
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
    print(
        "Original reviews: 10; supplemental-v1 records: 14; "
        "PATH-S06 qualifications: 5"
    )
    print(
        "Student tables: 15 candidates; 100 primary cases; "
        "140 supplemental-v1 cases; 5 PATH-S06 extension cases; "
        "29 human records"
    )
    if expected_netlify_csp:
        print(
            "Expected hosting-layer CSP blocks: "
            f"{len(expected_netlify_csp)} (site application unaffected)"
        )
    print(f"Screenshot: {SCREENSHOT}")
    print(f"Student evidence screenshot: {EVIDENCE_SCREENSHOT}")


if __name__ == "__main__":
    main()
