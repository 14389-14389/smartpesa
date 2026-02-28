from pydantic import BaseModel
from datetime import datetime
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
    created_at: datetime
    
    class Config:
        from_attributes = True

# Supplier Payment schemas
class SupplierPaymentBase(BaseModel):
    supplier_id: int
    amount: float
    due_date: datetime
    notes: Optional[str] = None

class SupplierPaymentCreate(SupplierPaymentBase):
    pass

class SupplierPaymentUpdate(BaseModel):
    status: Optional[str] = None
    paid_date: Optional[datetime] = None
    transaction_id: Optional[int] = None

class SupplierPayment(SupplierPaymentBase):
    id: int
    paid_date: Optional[datetime] = None
    status: str
    transaction_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Supplier with payments
class SupplierWithPayments(Supplier):
    payments: List[SupplierPayment] = []
    total_outstanding: Optional[float] = 0
    overdue_amount: Optional[float] = 0
