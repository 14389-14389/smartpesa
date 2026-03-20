from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

# Supplier schemas
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None

class SupplierCreate(SupplierBase):
    business_id: int

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None

class Supplier(SupplierBase):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Supplier Payment schemas (matches the Payment model)
class SupplierPaymentBase(BaseModel):
    supplier_id: int
    amount: float
    payment_date: date
    due_date: Optional[date] = None
    method: Optional[str] = "bank_transfer"
    reference: Optional[str] = None
    notes: Optional[str] = None

class SupplierPaymentCreate(SupplierPaymentBase):
    pass

class SupplierPaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    paid: Optional[bool] = None
    transaction_id: Optional[int] = None

class SupplierPayment(SupplierPaymentBase):
    id: int
    paid: bool
    paid_date: Optional[datetime] = None
    transaction_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Supplier with payments and calculated fields
class SupplierWithPayments(Supplier):
    payments: List[SupplierPayment] = []
    total_outstanding: Optional[float] = 0
    overdue_amount: Optional[float] = 0