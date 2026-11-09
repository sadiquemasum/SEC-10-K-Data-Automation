
import gzip
import json
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from unittest.mock import Mock, patch

import pytest

import app.services.sec_service as sec


@pytest.fixture
def cache_location(tmp_path, monkeypatch):
    cache_dir = tmp_path / "downloads"
    cache_file = cache_dir / "company_tickers.json"

    monkeypatch.setattr(sec, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(sec, "CACHE_FILE", cache_file)

    return cache_file


@pytest.fixture
def ticker_data():
    return {
        "0": {
            "cik_str": 320193,
            "ticker": "AAPL",
            "title": "Apple Inc.",
        },
        "1": {
            "cik_str": 789019,
            "ticker": "MSFT",
            "title": "Microsoft Corporation",
        },
        "2": {
            "ticker": "INVALID",
            "title": "Missing CIK Company",
        },
    }


def write_cache(cache_file, data):
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data), encoding="utf-8")


def test_get_sec_headers_returns_configured_headers(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT_NAME", "TestApplication")
    monkeypatch.setenv("SEC_USER_AGENT_EMAIL", "developer@example.org")

    headers = sec.get_sec_headers()

    assert headers["User-Agent"] == "TestApplication developer@example.org"
    assert headers["Accept-Encoding"] == "gzip, deflate"


def test_get_sec_headers_requires_configuration(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT_NAME", raising=False)
    monkeypatch.delenv("SEC_USER_AGENT_EMAIL", raising=False)

    with pytest.raises(ValueError, match="must be configured"):
        sec.get_sec_headers()


def test_get_sec_headers_rejects_example_email(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT_NAME", "TestApplication")
    monkeypatch.setenv("SEC_USER_AGENT_EMAIL", "test@example.com")

    with pytest.raises(ValueError, match="real SEC contact email"):
        sec.get_sec_headers()


def test_is_cache_valid_returns_false_when_missing(cache_location):
    assert sec.is_cache_valid() is False


def test_is_cache_valid_returns_true_for_fresh_cache(cache_location):
    write_cache(cache_location, {"0": {"ticker": "AAPL"}})

    assert sec.is_cache_valid() is True


def test_is_cache_valid_returns_false_for_expired_cache(cache_location):
    write_cache(cache_location, {"0": {"ticker": "AAPL"}})

    old_timestamp = (
        datetime.now(timezone.utc) - timedelta(hours=25)
    ).timestamp()

    import os
    os.utime(cache_location, (old_timestamp, old_timestamp))

    assert sec.is_cache_valid() is False


@pytest.mark.parametrize("compressed", [False, True])
def test_download_company_tickers_saves_cache(
    cache_location,
    ticker_data,
    monkeypatch,
    compressed,
):
    raw_data = json.dumps(ticker_data).encode("utf-8")

    if compressed:
        raw_data = gzip.compress(raw_data)

    response = Mock()
    response.read.return_value = raw_data

    mock_urlopen = Mock()
    mock_urlopen.return_value.__enter__ = Mock(return_value=response)
    mock_urlopen.return_value.__exit__ = Mock(return_value=False)

    monkeypatch.setattr(sec, "urlopen", mock_urlopen)
    monkeypatch.setattr(
        sec,
        "get_sec_headers",
        lambda: {"User-Agent": "Test"},
    )

    result = sec.download_company_tickers()

    assert result == ticker_data
    assert json.loads(cache_location.read_text()) == ticker_data
    mock_urlopen.assert_called_once()


def test_download_company_tickers_rejects_invalid_json(
    cache_location,
    monkeypatch,
):
    response = Mock()
    response.read.return_value = b"not valid json"

    mock_urlopen = Mock()
    mock_urlopen.return_value.__enter__ = Mock(return_value=response)
    mock_urlopen.return_value.__exit__ = Mock(return_value=False)

    monkeypatch.setattr(sec, "urlopen", mock_urlopen)
    monkeypatch.setattr(
        sec,
        "get_sec_headers",
        lambda: {"User-Agent": "Test"},
    )

    with pytest.raises(json.JSONDecodeError):
        sec.download_company_tickers()


def test_get_company_tickers_uses_fresh_cache(
    cache_location,
    ticker_data,
    monkeypatch,
):
    write_cache(cache_location, ticker_data)

    monkeypatch.setattr(sec, "is_cache_valid", lambda: True)

    with patch.object(sec, "download_company_tickers") as mock_download:
        result = sec.get_company_tickers()

    assert result == ticker_data
    mock_download.assert_not_called()


def test_get_company_tickers_uses_cache_when_sec_fails(
    cache_location,
    ticker_data,
    monkeypatch,
):
    write_cache(cache_location, ticker_data)

    monkeypatch.setattr(sec, "is_cache_valid", lambda: False)

    with patch.object(
        sec,
        "download_company_tickers",
        side_effect=RuntimeError("SEC unavailable"),
    ):
        result = sec.get_company_tickers()

    assert result == ticker_data


def test_get_company_tickers_fails_without_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(sec, "is_cache_valid", lambda: False)
    monkeypatch.setattr(
        sec,
        "CACHE_FILE",
        tmp_path / "company_tickers.json",
    )

    with patch.object(
        sec,
        "download_company_tickers",
        side_effect=RuntimeError("SEC unavailable"),
    ):
        with pytest.raises(
            RuntimeError,
            match="no local cache exists",
        ):
            sec.get_company_tickers()


def test_load_local_tickers_rejects_invalid_json(cache_location):
    cache_location.parent.mkdir(parents=True, exist_ok=True)
    cache_location.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Unable to read SEC ticker cache"):
        sec.load_local_tickers()


def test_search_companies_finds_exact_ticker(
    ticker_data,
    monkeypatch,
):
    monkeypatch.setattr(
        sec,
        "get_company_tickers",
        lambda: ticker_data,
    )

    results = sec.search_companies("AAPL")

    assert len(results) == 1
    assert results[0] == {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "cik": "0000320193",
    }


def test_search_companies_finds_company_by_name(
    ticker_data,
    monkeypatch,
):
    monkeypatch.setattr(
        sec,
        "get_company_tickers",
        lambda: ticker_data,
    )

    results = sec.search_companies("microsoft")

    assert len(results) == 1
    assert results[0]["name"] == "Microsoft Corporation"
    assert results[0]["ticker"] == "MSFT"


def test_search_companies_rejects_empty_query():
    with pytest.raises(ValueError, match="cannot be empty"):
        sec.search_companies("   ")


def test_search_companies_prioritizes_exact_ticker(
    monkeypatch,
):
    data = {
        "0": {
            "cik_str": 1,
            "ticker": "ABC",
            "title": "ABC Corporation",
        },
        "1": {
            "cik_str": 2,
            "ticker": "XYZ",
            "title": "ABC Technologies",
        },
    }

    monkeypatch.setattr(
        sec,
        "get_company_tickers",
        lambda: data,
    )

    results = sec.search_companies("ABC")

    assert results[0]["ticker"] == "ABC"
    assert results[0]["cik"] == "0000000001"

def test_download_company_tickers_rejects_empty_data(
    cache_location,
    monkeypatch,
):
    response = Mock()
    response.read.return_value = b"{}"

    mock_urlopen = Mock()
    mock_urlopen.return_value.__enter__ = Mock(return_value=response)
    mock_urlopen.return_value.__exit__ = Mock(return_value=False)

    monkeypatch.setattr(sec, "urlopen", mock_urlopen)
    monkeypatch.setattr(
        sec,
        "get_sec_headers",
        lambda: {"User-Agent": "Test"},
    )

    with pytest.raises(ValueError, match="Invalid SEC ticker JSON"):
        sec.download_company_tickers()


def test_download_company_tickers_handles_network_error(
    cache_location,
    monkeypatch,
):
    monkeypatch.setattr(
        sec,
        "get_sec_headers",
        lambda: {"User-Agent": "Test"},
    )

    with patch.object(
        sec,
        "urlopen",
        side_effect=URLError("Connection failed"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Unable to download SEC ticker data",
        ):
            sec.download_company_tickers()

def test_load_local_tickers_rejects_empty_cache(cache_location):
    cache_location.parent.mkdir(parents=True, exist_ok=True)
    cache_location.write_text("{}", encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match="Invalid local ticker cache",
    ):
        sec.load_local_tickers()