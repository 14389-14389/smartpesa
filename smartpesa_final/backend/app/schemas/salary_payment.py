from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .employee import EmployeeResponse

class SalaryPaymentBase(BaseModel):
    employee_id: int
    amount: float
    payment_date: date
    month: str
    description: Optional[str] = None
    business_id: int   # required

class SalaryPaymentCreate(SalaryPaymentBase):
    pass

class SalaryPaymentResponse(SalaryPaymentBase):
    id: int
    created_at: datetime
    employee: Optional[EmployeeResponse] = None

    class Config:
        orm_mode = True