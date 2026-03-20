from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmployeeRankBase(BaseModel):
    name: str
    base_salary: float
    description: Optional[str] = None

class EmployeeRankCreate(EmployeeRankBase):
    pass

class EmployeeRankUpdate(BaseModel):
    name: Optional[str] = None
    base_salary: Optional[float] = None
    description: Optional[str] = None

class EmployeeRankResponse(EmployeeRankBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True