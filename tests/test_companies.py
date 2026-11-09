
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


class MockResult:
    def __init__(self, company=None):
        self.company = company

    def scalars(self):
        return self

    def first(self):
        return self.company


class MockDB:
    def __init__(self, company=None):
        self.company = company
        self.added_company = None

    def execute(self, statement):
        return MockResult(self.company)

    def add(self, company):
        self.added_company = company

    def commit(self):
        pass

    def refresh(self, company):
        company.id = 1

    def rollback(self):
        pass


def override_get_db(db):
    def dependency():
        yield db

    return dependency


def test_search_company_existing_in_database():
    existing_company = type(
        "CompanyMock",
        (),
        {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "cik": "0000320193",
        },
    )()

    mock_db = MockDB(company=existing_company)
    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        client = TestClient(app)
        response = client.get("/companies/search?q=AAPL")

        assert response.status_code == 200
        assert response.json() == {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "cik": "0000320193",
        }
    finally:
        app.dependency_overrides.clear()


def test_search_company_found_in_sec():
    mock_db = MockDB()

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    sec_result = [
        {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "cik": "0000320193",
        }
    ]

    try:
        with patch(
            "app.routers.companies.search_companies",
            return_value=sec_result,
        ) as mock_search:

            client = TestClient(app)
            response = client.get("/companies/search?q=AAPL")

        assert response.status_code == 200
        assert response.json()["ticker"] == "AAPL"
        assert mock_db.added_company.name == "Apple Inc."
        mock_search.assert_called_once_with("AAPL")

    finally:
        app.dependency_overrides.clear()


def test_search_company_not_found():
    mock_db = MockDB()

    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        with patch(
            "app.routers.companies.search_companies",
            return_value=[],
        ):
            client = TestClient(app)
            response = client.get("/companies/search?q=UNKNOWN")

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Company 'UNKNOWN' not found."
        )

    finally:
        app.dependency_overrides.clear()


def test_search_company_rejects_whitespace_query():
    mock_db = MockDB()
    app.dependency_overrides[get_db] = override_get_db(mock_db)

    try:
        client = TestClient(app)
        response = client.get("/companies/search?q=%20%20%20")

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Search query cannot be empty."
        )
    finally:
        app.dependency_overrides.clear()



def test_search_company_database_commit_failure():
    mock_db = MockDB()
    app.dependency_overrides[get_db] = override_get_db(mock_db)

    sec_result = [
        {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "cik": "0000320193",
        }
    ]

    try:
        with (
            patch(
                "app.routers.companies.search_companies",
                return_value=sec_result,
            ),
            patch.object(
                mock_db,
                "commit",
                side_effect=Exception("Database unavailable"),
            ),
        ):
            client = TestClient(app)
            response = client.get("/companies/search?q=AAPL")

        assert response.status_code == 500
        assert response.json()["detail"] == (
            "Unable to save company to database."
        )
    finally:
        app.dependency_overrides.clear()
