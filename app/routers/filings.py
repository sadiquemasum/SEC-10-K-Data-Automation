
from pathlib import Path
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.filing import Filing
from app.services.filing_service import (
    make_session,
    find_latest_10k,
    download_html,
)
from app.services.storage_service import save_filing_files


router = APIRouter(prefix="/filings", tags=["Filings"])


def return_pdf(pdf_path: str):
    return FileResponse(
        path=pdf_path,
        filename=Path(pdf_path).name,
        media_type="application/pdf",
    )


@router.post("/download/{cik}", response_class=FileResponse)
def download_company_filing(
    cik: str,
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.cik == cik.zfill(10))
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Search for the company first.",
        )

    try:
        session = make_session()
        filing_data = find_latest_10k(session, company.cik)

        existing = (
            db.query(Filing)
            .filter(
                Filing.accession_number == filing_data["accession"]
            )
            .first()
        )

        # Return the existing PDF if it is already available
        if existing and Path(existing.pdf_path).is_file():
            return return_pdf(existing.pdf_path)

        # Download SEC HTML and convert it to PDF
        html = download_html(session, filing_data)
        result = save_filing_files(filing_data, html)

        if existing:
            existing.pdf_path = result["pdf_path"]
            db.commit()
            db.refresh(existing)
            return return_pdf(existing.pdf_path)

        # Save filing metadata in PostgreSQL
        new_filing = Filing(
            company_id=company.id,
            accession_number=filing_data["accession"],
            form=filing_data["form"],
            document=filing_data["document"],
            filing_date=date.fromisoformat(
                filing_data["filing_date"]
            ),
            report_date=(
                date.fromisoformat(filing_data["report_date"])
                if filing_data.get("report_date")
                else None
            ),
            pdf_path=result["pdf_path"],
        )

        db.add(new_filing)
        db.commit()
        db.refresh(new_filing)

        # Return the actual PDF file
        return return_pdf(new_filing.pdf_path)

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Filing download failed: {str(exc)}",
        ) from exc
