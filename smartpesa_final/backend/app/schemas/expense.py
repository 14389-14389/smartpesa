from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class ExpenseBase(BaseModel):
    category_id: int
    amount: float
    expense_date: date
    description: Optional[str] = None
    receipt_image: Optional[str] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    business_id: int   # <-- added

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[float] = None
    expense_date: Optional[date] = None
    description: Optional[str] = None
    receipt_image: Optional[str] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    # business_id is usually not updated; if you need to move expense to another business, handle separately
    # business_id: Optional[int] = None

class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True