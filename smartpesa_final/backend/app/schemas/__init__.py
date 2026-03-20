from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List

# ========== EXISTING SCHEMAS (keep as is) ==========

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: Optional[str] = "user"
    
    class Config:
        from_attributes = True

class User(UserResponse):
    hashed_password: str

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Business schemas
class BusinessBase(BaseModel):
    name: str

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    name: Optional[str] = None

class Business(BusinessBase):
    id: int
    owner_id: int
    created_at: Optional[datetime] = None
    transactions: List["Transaction"] = []
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    type: str  # "income" or "expense"
    category: str
    description: Optional[str] = None
    business_id: int

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    business_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== NEW SCHEMAS ==========

# Employee Rank schemas
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
        from_attributes = True

# Employee schemas
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
        from_attributes = True

# Salary Payment schemas
class SalaryPaymentBase(BaseModel):
    employee_id: int
    amount: float
    payment_date: date
    month: str
    description: Optional[str] = None

class SalaryPaymentCreate(SalaryPaymentBase):
    pass

class SalaryPaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    month: Optional[str] = None
    description: Optional[str] = None

class SalaryPaymentResponse(SalaryPaymentBase):
    id: int
    created_at: datetime
    employee: Optional[EmployeeResponse] = None

    class Config:
        from_attributes = True

# Expense Category schemas
class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Supplier Response (minimal – add more fields if needed)
class SupplierResponse(BaseModel):
    id: int
    name: str
    # add other fields as required

    class Config:
        from_attributes = True

# Expense schemas
class ExpenseBase(BaseModel):
    category_id: int
    amount: float
    expense_date: date
    description: Optional[str] = None
    receipt_image: Optional[str] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None

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

class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    category: Optional[ExpenseCategoryResponse] = None
    supplier: Optional[SupplierResponse] = None
    employee: Optional[EmployeeResponse] = None

    class Config:
        from_attributes = True

# Import existing inventory schemas (if they exist as separate module)
# from app.schemas.inventory import *

# Rebuild models to resolve forward references
Business.model_rebuild()
Transaction.model_rebuild()
EmployeeResponse.model_rebuild()
ExpenseResponse.model_rebuild()