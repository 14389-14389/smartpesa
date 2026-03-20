from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InventoryBase(BaseModel):
    business_id: int
    name: str
    sku: Optional[str] = None
    quantity: float = 0
    unit: str = "pieces"
    price_per_unit: float = 0
    reorder_level: float = 10
    category: Optional[str] = None
    is_active: bool = True

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    reorder_level: Optional[float] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Inventory(InventoryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InventoryTransactionBase(BaseModel):
    inventory_id: int
    quantity_change: float
    transaction_type: str
    reference_id: Optional[int] = None
    notes: Optional[str] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransaction(InventoryTransactionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class StockAlert(BaseModel):
    inventory_id: int
    name: str
    sku: Optional[str] = None
    current_quantity: float
    reorder_level: float
    deficit: float
