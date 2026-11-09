
from unittest.mock import Mock, patch

import pytest

from app.services.filing_service import (
    find_latest_10k,
    download_html,
    make_session,
)

def test_find_latest_10k_returns_latest_original_filing():
    """Returns the latest original 10-K and skips amendments."""

    session = Mock()

    session.get.return_value.raise_for_status.return_value = None
    session.get.return_value.json.return_value = {
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "form": ["10-K/A", "10-Q", "10-K", "10-K"],
                "accessionNumber": [
                    "amended-accession",
                    "quarterly-accession",
                    "latest-accession",
                    "older-accession",
                ],
                "primaryDocument": [
                    "amended.htm",
                    "quarterly.htm",
                    "latest.htm",
                    "older.htm",
                ],
                "filingDate": [
                    "2026-11-10",
                    "2026-10-20",
                    "2026-09-15",
                    "2025-09-15",
                ],
                "reportDate": [
                    "2026-09-26",
                    "2026-09-30",
                    "2025-09-27",
                    "2024-09-28",
                ],
            }
        },
    }

    result = find_latest_10k(session, "0000320193")

    assert result["company"] == "Apple Inc."
    assert result["cik"] == "0000320193"
    assert result["form"] == "10-K"
    assert result["accession"] == "latest-accession"
    assert result["document"] == "latest.htm"
    assert result["filing_date"] == "2026-09-15"


def test_find_latest_10k_raises_error_when_no_filing_exists():
    """Raises LookupError when no original 10-K is available."""

    session = Mock()

    session.get.return_value.raise_for_status.return_value = None
    session.get.return_value.json.return_value = {
        "name": "Example Company",
        "filings": {
            "recent": {
                "form": ["10-Q", "10-K/A"],
                "accessionNumber": ["quarterly", "amended"],
                "primaryDocument": ["quarterly.htm", "amended.htm"],
                "filingDate": ["2026-10-20", "2026-09-15"],
                "reportDate": ["2026-09-30", "2025-12-31"],
            }
        },
    }

    with pytest.raises(LookupError):
        find_latest_10k(session, "0000123456")


def test_download_html_returns_sec_document():
    """Downloads the filing HTML and records its SEC URL."""

    session = Mock()
    session.get.return_value.raise_for_status.return_value = None
    session.get.return_value.text = "<html><body>Annual Report</body></html>"

    filing = {
        "cik": "0000320193",
        "accession": "0000320193-26-000026",
        "document": "aapl-20260926.htm",
    }

    result = download_html(session, filing)

    assert result == "<html><body>Annual Report</body></html>"

    assert filing["url"] == (
        "https://www.sec.gov/Archives/edgar/data/"
        "320193/000032019326000026/aapl-20260926.htm"
    )

def test_make_session_configures_sec_headers():
    """Creates a session with the required SEC headers."""

    mock_session = Mock()

    with (
        patch(
            "app.services.filing_service.requests.Session",
            return_value=mock_session,
        ) as session_factory,
        patch(
            "app.services.filing_service.get_sec_headers",
            return_value={
                "User-Agent": "TestApplication test@example.org",
                "Accept-Encoding": "gzip, deflate",
            },
        ),
    ):
        result = make_session()

    session_factory.assert_called_once_with()

    mock_session.headers.update.assert_called_once_with({
        "User-Agent": "TestApplication test@example.org",
        "Accept-Encoding": "gzip, deflate",
    })

    assert result is mock_session