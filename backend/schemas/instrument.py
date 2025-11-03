from pydantic import BaseModel
from typing import Optional

class InstrumentRead(BaseModel):
    id: int
    isin: Optional[str]
    ticker: Optional[str]
    name: str
    currency: Optional[str]

    class Config:
        orm_mode = True
