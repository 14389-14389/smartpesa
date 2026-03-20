from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class MovementReason(str, Enum):
    purchase = "purchase"
    sale = "sale"
    destroy = "destroy"
    adjustment = "adjustment"

class InventoryMovementBase(BaseModel):
    product_id: int
    quantity_change: int
    reason: MovementReason
    reference_id: Optional[int] = None
    notes: Optional[str] = None

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovement(InventoryMovementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
