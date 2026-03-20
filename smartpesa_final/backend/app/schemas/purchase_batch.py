from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class PurchaseBatchBase(BaseModel):
    product_id: int
    quantity: int
    cost_per_unit: float
    purchase_date: date
    remaining_quantity: int
    supplier_id: Optional[int] = None
    notes: Optional[str] = None

class PurchaseBatchCreate(PurchaseBatchBase):
    pass

class PurchaseBatch(PurchaseBatchBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
