
from pydantic import BaseModel, ConfigDict


class CompanyResponse(BaseModel):
    name: str
    ticker: str
    cik: str

    model_config = ConfigDict(from_attributes=True)
