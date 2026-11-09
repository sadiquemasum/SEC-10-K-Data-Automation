
import re
import tempfile
from pathlib import Path
from html import escape

from playwright.sync_api import sync_playwright


def add_base_tag(html: str, base_url: str) -> str:
    """Resolve relative links and assets in SEC HTML."""
    base_tag = f'<base href="{escape(base_url, quote=True)}">'

    if re.search(r"<head[^>]*>", html, re.IGNORECASE):
        return re.sub(
            r"(<head[^>]*>)",
            lambda match: match.group(1) + base_tag,
            html,
            count=1,
            flags=re.IGNORECASE,
        )

    return base_tag + html


def html_to_pdf(html: str, output_path: str, base_url: str) -> Path:
    """Convert SEC filing HTML into a PDF using Chromium."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    html = add_base_tag(html, base_url)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        encoding="utf-8",
        delete=False,
    ) as temp_file:
        temp_file.write(html)
        temp_path = Path(temp_file.name)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()

            page.goto(
                temp_path.as_uri(),
                wait_until="networkidle",
                timeout=120000,
            )

            page.pdf(
                path=str(output),
                format="Letter",
                print_background=True,
            )

            browser.close()
    finally:
        temp_path.unlink(missing_ok=True)

    return output
