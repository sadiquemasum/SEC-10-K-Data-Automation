
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import HTTPException

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.company import Company


class MockQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args):
        return self

    def first(self):
        return self.result


class MockDB:
    def __init__(self, company=None, filing=None):
        self.company = company
        self.filing = filing
        self.added_filing = None
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        if model == Company:
            return MockQuery(self.company)

        return MockQuery(self.filing)

    def add(self, filing):
        self.added_filing = filing

    def commit(self):
        self.committed = True

    def refresh(self, filing):
        filing.id = 1

    def rollback(self):
        self.rolled_back = True


def override_get_db(db):
    def dependency():
        yield db

    return dependency


def test_download_filing_company_not_found():
    mock_db = MockDB()

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        client = TestClient(app)
        response = client.post("/filings/download/0000320193")

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Company not found. Search for the company first."
        )
    finally:
        app.dependency_overrides.clear()


def test_download_filing_returns_existing_pdf(tmp_path):
    pdf_path = tmp_path / "apple_report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 existing test PDF")

    company = SimpleNamespace(
        id=1,
        name="Apple Inc.",
        cik="0000320193",
    )

    existing_filing = SimpleNamespace(
        pdf_path=str(pdf_path),
    )

    mock_db = MockDB(
        company=company,
        filing=existing_filing,
    )

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    filing_data = {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "form": "10-K",
        "accession": "0000320193-26-000026",
        "document": "aapl-20260926.htm",
        "filing_date": "2026-10-30",
        "report_date": "2026-09-26",
    }

    try:
        with (
            patch(
                "app.routers.filings.make_session"
            ),
            patch(
                "app.routers.filings.find_latest_10k",
                return_value=filing_data,
            ),
            patch(
                "app.routers.filings.download_html"
            ) as mock_download,
            patch(
                "app.routers.filings.save_filing_files"
            ) as mock_save,
        ):
            client = TestClient(app)
            response = client.post(
                "/filings/download/0000320193"
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == pdf_path.read_bytes()

        mock_download.assert_not_called()
        mock_save.assert_not_called()

    finally:
        app.dependency_overrides.clear()


def test_download_new_filing_returns_pdf(tmp_path):
    pdf_path = tmp_path / "apple_report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 new test PDF")

    company = SimpleNamespace(
        id=1,
        name="Apple Inc.",
        cik="0000320193",
    )

    mock_db = MockDB(company=company)

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    filing_data = {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "form": "10-K",
        "accession": "0000320193-26-000026",
        "document": "aapl-20260926.htm",
        "filing_date": "2026-10-30",
        "report_date": "2026-09-26",
    }

    try:
        with (
            patch("app.routers.filings.make_session"),
            patch(
                "app.routers.filings.find_latest_10k",
                return_value=filing_data,
            ),
            patch(
                "app.routers.filings.download_html",
                return_value="<html>Apple report</html>",
            ) as mock_download,
            patch(
                "app.routers.filings.save_filing_files",
                return_value={"pdf_path": str(pdf_path)},
            ) as mock_save,
        ):
            client = TestClient(app)
            response = client.post(
                "/filings/download/0000320193"
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == pdf_path.read_bytes()

        mock_download.assert_called_once()
        mock_save.assert_called_once()

        assert mock_db.added_filing is not None
        assert mock_db.added_filing.company_id == 1
        assert mock_db.added_filing.form == "10-K"
        assert mock_db.added_filing.pdf_path == str(pdf_path)
        assert mock_db.committed is True

    finally:
        app.dependency_overrides.clear()


def test_download_filing_returns_500_on_failure():
    company = SimpleNamespace(
        id=1,
        name="Apple Inc.",
        cik="0000320193",
    )

    mock_db = MockDB(company=company)

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        with (
            patch("app.routers.filings.make_session"),
            patch(
                "app.routers.filings.find_latest_10k",
                side_effect=RuntimeError("SEC service unavailable"),
            ),
        ):
            client = TestClient(app)
            response = client.post(
                "/filings/download/0000320193"
            )

        assert response.status_code == 500
        assert "SEC service unavailable" in response.json()["detail"]
        assert mock_db.rolled_back is True

    finally:
        app.dependency_overrides.clear()


def test_download_existing_filing_with_missing_pdf(tmp_path):
    pdf_path = tmp_path / "regenerated_apple.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 regenerated PDF")

    company = SimpleNamespace(
        id=1,
        name="Apple Inc.",
        cik="0000320193",
    )

    existing_filing = SimpleNamespace(
        pdf_path=str(tmp_path / "missing_old_report.pdf"),
    )

    mock_db = MockDB(
        company=company,
        filing=existing_filing,
    )

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    filing_data = {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "form": "10-K",
        "accession": "0000320193-26-000026",
        "document": "aapl-20260926.htm",
        "filing_date": "2026-10-30",
        "report_date": "2026-09-26",
    }

    try:
        with (
            patch("app.routers.filings.make_session"),
            patch(
                "app.routers.filings.find_latest_10k",
                return_value=filing_data,
            ),
            patch(
                "app.routers.filings.download_html",
                return_value="<html>Apple report</html>",
            ),
            patch(
                "app.routers.filings.save_filing_files",
                return_value={"pdf_path": str(pdf_path)},
            ) as mock_save,
        ):
            client = TestClient(app)
            response = client.post("/filings/download/0000320193")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == pdf_path.read_bytes()

        assert existing_filing.pdf_path == str(pdf_path)
        assert mock_db.committed is True
        mock_save.assert_called_once()

    finally:
        app.dependency_overrides.clear()



def test_download_filing_preserves_http_exception():
    company = SimpleNamespace(
        id=1,
        name="Apple Inc.",
        cik="0000320193",
    )

    mock_db = MockDB(company=company)

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        with (
            patch("app.routers.filings.make_session"),
            patch(
                "app.routers.filings.find_latest_10k",
                side_effect=HTTPException(
                    status_code=429,
                    detail="SEC rate limit exceeded",
                ),
            ),
        ):
            client = TestClient(app)
            response = client.post("/filings/download/0000320193")

        assert response.status_code == 429
        assert response.json()["detail"] == "SEC rate limit exceeded"
        assert mock_db.rolled_back is False

    finally:
        app.dependency_overrides.clear()
