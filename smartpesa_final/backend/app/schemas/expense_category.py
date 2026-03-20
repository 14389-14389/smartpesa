from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
