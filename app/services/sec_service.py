import gzip
import json
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# SEC configuration
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Project root / downloads directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "downloads"
CACHE_FILE = CACHE_DIR / "company_tickers.json"

# Cache validity: 24 hours
CACHE_MAX_AGE = timedelta(hours=24)

# SEC request timeout
REQUEST_TIMEOUT = 30


def get_sec_headers():
    """
    Build SEC request headers using environment variables.
    """
    name = os.getenv("SEC_USER_AGENT_NAME")
    email = os.getenv("SEC_USER_AGENT_EMAIL")

    if not name or not email:
        raise ValueError(
            "SEC_USER_AGENT_NAME and SEC_USER_AGENT_EMAIL "
            "must be configured in the environment."
        )

    if "example.com" in email.lower():
        raise ValueError(
            "Please configure a real SEC contact email."
        )

    return {
        "User-Agent": f"{name} {email}",
        "Accept-Encoding": "gzip, deflate",
    }


def is_cache_valid():
    """
    Check whether the local JSON cache is less than 24 hours old.
    """

    if not CACHE_FILE.exists():
        return False

    file_age = (
        datetime.now(timezone.utc)
        - datetime.fromtimestamp(
            CACHE_FILE.stat().st_mtime,
            tz=timezone.utc
        )
    )

    return file_age < CACHE_MAX_AGE


def download_company_tickers():
    """
    Download company ticker information from the SEC
    and save it locally.
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    request = Request(
        SEC_TICKERS_URL,
        headers=get_sec_headers()
    )

    try:
        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:

            raw_data = response.read()

        # Handle GZIP-compressed SEC responses
        if raw_data.startswith(b"\x1f\x8b"):
            raw_data = gzip.decompress(raw_data)

        # Decode and validate JSON
        data = json.loads(raw_data.decode("utf-8"))

        if not isinstance(data, dict) or not data:
            raise ValueError("Invalid SEC ticker JSON response.")

        # Save atomically to avoid leaving a partial cache file
        temp_file = CACHE_FILE.with_suffix(".json.tmp")
        temp_file.write_text(
            json.dumps(data),
            encoding="utf-8"
        )
        temp_file.replace(CACHE_FILE)

        print("SEC company ticker cache updated successfully.")

        return data

    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Unable to download SEC ticker data: {error}"
        ) from error


def get_company_tickers(force_refresh=False):
    """
    Return cached SEC ticker data.

    Download a new copy when:
    - The cache does not exist.
    - The cache is older than 24 hours.
    - force_refresh is True.

    If the SEC is unavailable, use the last valid local cache.
    """

    if not force_refresh and is_cache_valid():
        return load_local_tickers()

    try:
        return download_company_tickers()

    except (HTTPError, URLError, TimeoutError, RuntimeError,
            ValueError) as error:

        if CACHE_FILE.exists():
            print(
                f"SEC refresh failed. Using existing cache: {error}"
            )
            return load_local_tickers()

        raise RuntimeError(
            "SEC ticker data unavailable and no local cache exists."
        ) from error


def load_local_tickers():
    """
    Load ticker information from the local JSON file.
    """

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict) or not data:
            raise ValueError("Invalid local ticker cache.")

        return data

    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Unable to read SEC ticker cache: {error}"
        ) from error


def search_companies(query):
    """
    Search companies by ticker or company name.

    Returns a list of matching companies.
    CIK values are normalized to 10 digits.
    """

    if not query or not query.strip():
        raise ValueError("Company search query cannot be empty.")

    query = query.strip()
    query_upper = query.upper()

    companies = get_company_tickers()

    results = []

    for company in companies.values():

        ticker = str(company.get("ticker", ""))
        name = str(company.get("title", ""))
        cik = company.get("cik_str")

        if cik is None:
            continue

        ticker_match = ticker.upper() == query_upper
        name_match = query_upper in name.upper()

        if ticker_match or name_match:
            results.append({
                "name": name,
                "ticker": ticker,
                "cik": str(cik).zfill(10)
            })

    # Put an exact ticker match first
    results.sort(
        key=lambda company: (
            company["ticker"].upper() != query_upper,
            company["name"]
        )
    )

    return results[:10]
