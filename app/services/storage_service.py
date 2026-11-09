
import re
from pathlib import Path

from app.services.pdf_service import html_to_pdf


def safe_filename(value: str) -> str:
    """Convert a company name into a safe filename."""
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value)
    return value.strip("_")


def save_filing_files(
    filing: dict,
    html: str,
    output_dir: str = "downloads/10k_reports",
) -> dict:
    """Generate and save the SEC filing PDF."""

    company = safe_filename(filing["company"])
    filing_date = filing["filing_date"]
    accession = filing["accession"]

    company_dir = Path(output_dir) / company
    company_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{company}_{filing_date}_{accession}"
    pdf_path = company_dir / f"{filename}.pdf"

    html_to_pdf(
        html=html,
        output_path=str(pdf_path),
        base_url=filing["url"],
    )

    return {
        **filing,
        "pdf_path": str(pdf_path),
    }
