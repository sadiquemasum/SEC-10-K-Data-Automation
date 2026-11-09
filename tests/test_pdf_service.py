
import pytest

from app.services.pdf_service import add_base_tag
from pathlib import Path
from urllib.parse import urlparse
from unittest.mock import MagicMock, patch

from app.services.pdf_service import html_to_pdf


def test_add_base_tag_inserts_tag_inside_head():
    html = "<html><head><title>Annual Report</title></head><body></body></html>"
    base_url = "https://www.sec.gov/Archives/edgar/data/"

    result = add_base_tag(html, base_url)

    assert f'<base href="{base_url}">' in result
    assert result.index("<base") < result.index("<title>")


def test_add_base_tag_is_case_insensitive():
    html = "<HTML><HEAD><title>Annual Report</title></HEAD></HTML>"
    base_url = "https://www.sec.gov/"

    result = add_base_tag(html, base_url)

    assert '<base href="https://www.sec.gov/">' in result
    assert result.index("<base") < result.index("<title>")


def test_add_base_tag_without_head():
    html = "<html><body>Annual Report</body></html>"
    base_url = "https://www.sec.gov/"

    result = add_base_tag(html, base_url)

    assert result.startswith(f'<base href="{base_url}">')


def test_add_base_tag_escapes_url():
    html = "<html><head></head></html>"
    base_url = 'https://example.com/report?id=1&name="annual"'

    result = add_base_tag(html, base_url)

    assert 'id=1&amp;name=&quot;annual&quot;' in result


def test_html_to_pdf_creates_pdf_and_cleans_temp_file(tmp_path):
    output_path = tmp_path / "reports" / "annual_report.pdf"

    # Mock Playwright objects
    playwright = MagicMock()
    browser = MagicMock()
    page = MagicMock()

    playwright.chromium.launch.return_value = browser
    browser.new_page.return_value = page

    # Simulate PDF creation
    def create_pdf(path, **kwargs):
        Path(path).write_bytes(b"%PDF-1.4 test")

    page.pdf.side_effect = create_pdf

    playwright_context = MagicMock()
    playwright_context.__enter__.return_value = playwright

    with patch(
        "app.services.pdf_service.sync_playwright",
        return_value=playwright_context,
    ):
        result = html_to_pdf(
            html="<html><head></head><body>Annual Report</body></html>",
            output_path=str(output_path),
            base_url="https://www.sec.gov/",
        )

    # Verify PDF output
    assert result == output_path
    assert output_path.is_file()
    assert output_path.read_bytes() == b"%PDF-1.4 test"

    # Verify browser interaction
    playwright.chromium.launch.assert_called_once()
    browser.new_page.assert_called_once()
    browser.close.assert_called_once()

    page.goto.assert_called_once()
    goto_url = page.goto.call_args.args[0]
    assert goto_url.startswith("file://")

    assert page.goto.call_args.kwargs == {
        "wait_until": "networkidle",
        "timeout": 120000,
    }

    page.pdf.assert_called_once_with(
        path=str(output_path),
        format="Letter",
        print_background=True,
    )

    # Verify temporary HTML was deleted
    temp_path = Path(urlparse(goto_url).path)
    assert not temp_path.exists()


def test_html_to_pdf_cleans_temp_file_when_conversion_fails(tmp_path):
    output_path = tmp_path / "reports" / "failed_report.pdf"

    playwright = MagicMock()
    browser = MagicMock()
    page = MagicMock()

    playwright.chromium.launch.return_value = browser
    browser.new_page.return_value = page

    page.pdf.side_effect = RuntimeError("PDF conversion failed")

    playwright_context = MagicMock()
    playwright_context.__enter__.return_value = playwright

    with patch(
        "app.services.pdf_service.sync_playwright",
        return_value=playwright_context,
    ):
        with pytest.raises(
            RuntimeError,
            match="PDF conversion failed",
        ):
            html_to_pdf(
                html="<html><body>Annual Report</body></html>",
                output_path=str(output_path),
                base_url="https://www.sec.gov/",
            )

    goto_url = page.goto.call_args.args[0]
    temp_path = Path(urlparse(goto_url).path)

    assert not temp_path.exists()
