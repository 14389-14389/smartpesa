"""
Inventory model for SmartPesa
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, nullable=True)
    quantity = Column(Float, default=0)
    unit = Column(String(50), default="pieces")
    price_per_unit = Column(Float, default=0)
    reorder_level = Column(Float, default=10)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="inventory_items")
    
    def to_dict(self):
        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "sku": self.sku,
            "quantity": self.quantity,
            "unit": self.unit,
            "price_per_unit": self.price_per_unit,
            "reorder_level": self.reorder_level,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
