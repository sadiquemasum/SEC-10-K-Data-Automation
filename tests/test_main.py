import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app, lifespan


def test_root_endpoint():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to SEC 10-K Downloader FastAPI!",
        "python": "3.14.3",
        "status": "running",
    }


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_database_health_connected():
    client = TestClient(app)

    with patch("app.main.check_database_connection", return_value=True):
        response = client.get("/db-health")

    assert response.status_code == 200
    assert response.json() == {
        "database": "PostgreSQL",
        "status": "connected",
    }


def test_database_health_failed():
    client = TestClient(app)

    with patch("app.main.check_database_connection", return_value=False):
        response = client.get("/db-health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database connection failed"
    }



def test_lifespan_creates_database_tables():
    async def run_lifespan():
        with patch("app.main.Base.metadata.create_all") as create_all:
            async with lifespan(app):
                create_all.assert_called_once_with(
                    bind=__import__(
                        "app.main", fromlist=["engine"]
                    ).engine
                )

    asyncio.run(run_lifespan())
