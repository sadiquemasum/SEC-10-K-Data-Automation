
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class FilingResponse(BaseModel):
    id: int
    company_id: int
    accession_number: str
    form: str
    document: str
    filing_date: date
    report_date: date | None
    pdf_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
