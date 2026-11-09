
import time
import requests

from app.services.sec_service import get_sec_headers


SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

ARCHIVE_URL = (
    "https://www.sec.gov/Archives/edgar/data/"
    "{cik_int}/{acc_nodash}/{doc}"
)

REQUEST_PAUSE = 0.2


def make_session():
    session = requests.Session()
    session.headers.update({
        **get_sec_headers(),
        "Accept-Encoding": "gzip, deflate"
    })
    return session


def get(session, url):
    time.sleep(REQUEST_PAUSE)

    response = session.get(url, timeout=60)
    response.raise_for_status()

    return response


def find_latest_10k(session, cik):
    """Find the latest original 10-K filing, excluding amendments."""

    data = get(
        session,
        SUBMISSIONS_URL.format(cik=cik)
    ).json()

    recent = data["filings"]["recent"]

    for i, form in enumerate(recent["form"]):
        if form == "10-K":
            return {
                "company": data.get("name", ""),
                "cik": str(cik).zfill(10),
                "form": form,
                "accession": recent["accessionNumber"][i],
                "document": recent["primaryDocument"][i],
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
            }

    raise LookupError(f"No 10-K found for CIK {cik}")


def download_html(session, filing):
    """Download the original SEC filing HTML."""

    url = ARCHIVE_URL.format(
        cik_int=int(filing["cik"]),
        acc_nodash=filing["accession"].replace("-", ""),
        doc=filing["document"]
    )

    response = get(session, url)

    filing["url"] = url

    return response.text
