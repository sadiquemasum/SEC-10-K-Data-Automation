
from pathlib import Path
from unittest.mock import patch

from app.services.storage_service import save_filing_files


def test_save_filing_files_creates_pdf_path(tmp_path):
    filing = {
        "company": "Apple Inc.",
        "filing_date": "2026-11-03",
        "accession": "0000320193-26-000026",
        "url": "https://www.sec.gov/Archives/edgar/data/320193/example/",
    }

    html = "<html><body>Annual Report</body></html>"

    with patch(
        "app.services.storage_service.html_to_pdf"
    ) as mock_pdf:
        result = save_filing_files(
            filing,
            html,
            output_dir=str(tmp_path),
        )

    expected_path = (
        tmp_path
        / "Apple_Inc"
        / "Apple_Inc_2026-11-03_0000320193-26-000026.pdf"
    )

    assert result["pdf_path"] == str(expected_path)
    assert expected_path.parent.is_dir()
    mock_pdf.assert_called_once_with(
        html=html,
        output_path=str(expected_path),
        base_url=filing["url"],
    )
