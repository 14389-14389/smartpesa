from sqlalchemy import Column, Integer, DECIMAL, DateTime, Enum, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class PaymentMethod(enum.Enum):
    cash = "cash"
    card = "card"
    mobile = "mobile"
    credit = "credit"

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    sale_date = Column(DateTime, server_default=func.current_timestamp())
    total_amount = Column(DECIMAL(10,2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.cash)
    customer_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    business = relationship("Business", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
