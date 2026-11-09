import argparse
import os
import sys

from dotenv import load_dotenv

from app.services.filing_service import (
    make_session,
    find_latest_10k,
    download_html,
)
from app.services.storage_service import save_filing_files


load_dotenv()

COMPANIES = [
    {"name": "Apple", "cik": "0000320193"},
    {"name": "Meta", "cik": "0001326801"},
    {"name": "Alphabet", "cik": "0001652044"},
    {"name": "Amazon", "cik": "0001018724"},
    {"name": "Netflix", "cik": "0001065280"},
    {"name": "Goldman Sachs", "cik": "0000886982"},
]


def show_menu():
    print("\n=== SEC 10-K Downloader ===")

    for i, company in enumerate(COMPANIES, start=1):
        print(f"  {i}) {company['name']}")

    print(f"  {len(COMPANIES) + 1}) All of the above")
    print("  0) Quit")


def choose_companies(choice):
    choice = choice.strip().lower()

    if choice in (str(len(COMPANIES) + 1), "all", "a"):
        return COMPANIES

    if choice.isdigit() and 1 <= int(choice) <= len(COMPANIES):
        return [COMPANIES[int(choice) - 1]]

    return None


def process_company(session, company):
    name = company["name"]
    cik = company["cik"]

    print(f"\n[{name}] Looking up latest 10-K...")

    filing = find_latest_10k(session, cik)

    print(
        f"[{name}] Found: filed {filing['filing_date']}, "
        f"period ending {filing['report_date']}"
    )

    html = download_html(session, filing)

    print(f"[{name}] Converting to PDF...")

    result = save_filing_files(filing, html)

    print(f"[{name}] Saved: {result['pdf_path']}")

    return result["pdf_path"]


def run(selected, session):
    successful = []
    failed = []

    for company in selected:
        try:
            successful.append(process_company(session, company))
        except Exception as exc:
            print(f"[{company['name']}] FAILED: {exc}")
            failed.append(company["name"])

    print(f"\nDone. {len(successful)} saved, {len(failed)} failed.")

    if failed:
        print("Failed: " + ", ".join(failed))


def main():
    parser = argparse.ArgumentParser(
        description="Download latest SEC 10-K reports as PDFs."
    )

    parser.add_argument(
        "--company",
        help="1-6 for one company, 7 or 'all' for all companies",
    )

    parser.add_argument(
        "--user-agent",
        help="Override the SEC User-Agent contact information",
    )

    args = parser.parse_args()

    session = make_session()

    if args.user_agent:
        session.headers["User-Agent"] = args.user_agent

    if args.company:
        selected = choose_companies(args.company)

        if not selected:
            sys.exit("Invalid company. Use 1-6, 7, or 'all'.")

        run(selected, session)
        return

    while True:
        show_menu()
        answer = input("\nChoose an option: ").strip()

        if answer == "0":
            print("Goodbye.")
            return

        selected = choose_companies(answer)

        if not selected:
            print("Please enter a valid menu option.")
            continue

        run(selected, session)


if __name__ == "__main__":
    main()
