from sqlalchemy import Column, Integer, DECIMAL, Date, ForeignKey, TIMESTAMP, Text, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PurchaseBatch(Base):
    __tablename__ = "purchase_batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    cost_per_unit = Column(DECIMAL(10,2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    product = relationship("Inventory", back_populates="purchase_batches")
    supplier = relationship("Supplier", back_populates="purchase_batches")
