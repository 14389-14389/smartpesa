from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Inventory schemas
class InventoryBase(BaseModel):
    name: str
    sku: Optional[str] = None
    quantity: float = 0
    unit: str = "pieces"
    price_per_unit: float = 0
    reorder_level: float = 10

class InventoryCreate(InventoryBase):
    business_id: int

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    reorder_level: Optional[float] = None

class Inventory(InventoryBase):
    id: int
    business_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Inventory Transaction schemas
class InventoryTransactionBase(BaseModel):
    inventory_id: int
    quantity_change: float
    transaction_type: str  # "purchase", "sale", "adjustment", "return"
    reference_id: Optional[int] = None
    notes: Optional[str] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransaction(InventoryTransactionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Stock alert schema
class StockAlert(BaseModel):
    inventory_id: int
    name: str
    sku: Optional[str]
    current_quantity: float
    reorder_level: float
    deficit: float
