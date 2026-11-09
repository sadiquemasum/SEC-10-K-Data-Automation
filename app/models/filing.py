
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    func,
)

from app.database import Base


class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    accession_number = Column(String(30), unique=True, nullable=False)
    form = Column(String(10), nullable=False, default="10-K")

    document = Column(String(255), nullable=False)
    filing_date = Column(Date, nullable=False)
    report_date = Column(Date, nullable=True)

    pdf_path = Column(String(500), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
