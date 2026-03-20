from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .employee_rank import EmployeeRankResponse

class EmployeeBase(BaseModel):
    name: str
    rank_id: int
    monthly_salary: float
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: date
    termination_date: Optional[date] = None
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    rank_id: Optional[int] = None
    monthly_salary: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    rank: Optional[EmployeeRankResponse] = None

    class Config:
        orm_mode = True
