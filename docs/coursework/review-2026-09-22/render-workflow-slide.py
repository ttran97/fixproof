"""Render the slide-sized FixProof SVG to PNG and PDF with local Chromium."""

from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    folder = Path(__file__).resolve().parent
    html = folder / "fixproof-workflow-slide-print.html"
    png = folder / "fixproof-workflow-slide.png"
    pdf = folder / "fixproof-workflow-slide.pdf"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": 1600, "height": 900},
                device_scale_factor=1,
            )
            page.goto(html.as_uri(), wait_until="load")
            image_loaded = page.locator("img").evaluate(
                "image => image.complete && image.naturalWidth === 1600"
            )
            if not image_loaded:
                raise RuntimeError("The local slide SVG did not load at 1600 px width.")
            page.screenshot(path=str(png), full_page=True)
            page.pdf(
                path=str(pdf),
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()

    print(f"Rendered {png.name} and {pdf.name}")


if __name__ == "__main__":
    main()
