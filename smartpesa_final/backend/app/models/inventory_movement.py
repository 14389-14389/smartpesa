from sqlalchemy import Column, Integer, Enum, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class MovementReason(enum.Enum):
    purchase = "purchase"
    sale = "sale"
    destroy = "destroy"
    adjustment = "adjustment"

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reason = Column(Enum(MovementReason), nullable=False)
    reference_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    product = relationship("Inventory", back_populates="movements")
