from sqlalchemy import Column, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10,2), nullable=False)
    cost_of_goods_sold = Column(DECIMAL(10,2), nullable=False)
    discount = Column(DECIMAL(10,2), default=0)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Inventory", back_populates="sale_items")
