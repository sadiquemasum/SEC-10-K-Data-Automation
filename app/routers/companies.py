
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyResponse
from app.services.sec_service import search_companies


router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


@router.get("/search", response_model=CompanyResponse)
def search_company(
    q: str = Query(
        ...,
        min_length=1,
        description="Company name or ticker symbol"
    ),
    db: Session = Depends(get_db)
):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty."
        )

    # 1. Search PostgreSQL by company name or ticker
    statement = select(Company).where(
        (Company.name.ilike(f"%{query}%")) |
        (Company.ticker.ilike(query))
    )

    existing_company = db.execute(statement).scalars().first()

    if existing_company:
        return existing_company

    # 2. Search SEC ticker JSON
    sec_results = search_companies(query)

    if not sec_results:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{query}' not found."
        )

    # 3. Select the best matching result
    company_data = sec_results[0]

    # 4. Save company in PostgreSQL
    new_company = Company(
        name=company_data["name"],
        ticker=company_data["ticker"],
        cik=company_data["cik"]
    )

    db.add(new_company)

    try:
        db.commit()
        db.refresh(new_company)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save company to database."
        )

    # 5. Return the company
    return new_company
