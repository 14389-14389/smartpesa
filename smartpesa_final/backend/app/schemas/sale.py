from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    mobile = "mobile"
    credit = "credit"

class SaleItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    discount: Optional[float] = 0

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    id: int
    cost_of_goods_sold: float

    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    business_id: int
    payment_method: PaymentMethod = PaymentMethod.cash
    customer_name: Optional[str] = None
    notes: Optional[str] = None

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class Sale(SaleBase):
    id: int
    sale_date: datetime
    total_amount: float
    created_at: datetime
    items: List[SaleItem] = []

    class Config:
        from_attributes = True
