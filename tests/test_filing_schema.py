
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.filing import FilingResponse


def test_filing_response_from_attributes():
    """FilingResponse accepts an object with matching attributes."""

    class Filing:
        id = 1
        company_id = 2
        accession_number = "0000320193-26-000026"
        form = "10-K"
        document = "annual-report.htm"
        filing_date = date(2026, 10, 30)
        report_date = date(2026, 9, 27)
        pdf_path = "downloads/apple/report.pdf"
        created_at = datetime(2026, 10, 30, 12, 0, 0)

    response = FilingResponse.model_validate(Filing())

    assert response.id == 1
    assert response.company_id == 2
    assert response.accession_number == "0000320193-26-000026"
    assert response.form == "10-K"
    assert response.document == "annual-report.htm"
    assert response.filing_date == date(2026, 10, 30)
    assert response.report_date == date(2026, 9, 27)
    assert response.pdf_path == "downloads/apple/report.pdf"


def test_filing_response_allows_none_report_date():
    """Report date is optional."""

    response = FilingResponse(
        id=1,
        company_id=2,
        accession_number="0000320193-26-000026",
        form="10-K",
        document="annual-report.htm",
        filing_date=date(2026, 10, 30),
        report_date=None,
        pdf_path="downloads/apple/report.pdf",
        created_at=datetime(2026, 10, 30, 12, 0, 0),
    )

    assert response.report_date is None


def test_filing_response_rejects_missing_required_field():
    """Missing required fields raise ValidationError."""

    with pytest.raises(ValidationError):
        FilingResponse(
            id=1,
            company_id=2,
            accession_number="0000320193-26-000026",
            form="10-K",
            document="annual-report.htm",
            filing_date=date(2026, 10, 30),
            report_date=None,
            created_at=datetime(2026, 10, 30, 12, 0, 0),
        )
