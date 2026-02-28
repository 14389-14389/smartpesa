"""
Supplier model for SmartPesa
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    payment_terms = Column(String(100), default="Net 30")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="suppliers")
    payments = relationship("Payment", back_populates="supplier", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "payment_terms": self.payment_terms,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    method = Column(String(50), default="bank_transfer")
    reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    paid = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="payments")
    
    def to_dict(self):
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "amount": self.amount,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "method": self.method,
            "reference": self.reference,
            "notes": self.notes,
            "paid": self.paid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
