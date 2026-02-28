"""
Credit score model for SmartPesa
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class CreditScore(Base):
    __tablename__ = "credit_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    smartpesa_score = Column(Integer, default=0)
    revenue_consistency_score = Column(Float, default=0)
    cash_buffer_ratio = Column(Float, default=0)
    debt_coverage_capacity = Column(Float, default=0)
    inventory_health_score = Column(Float, default=0)
    factors = Column(JSON, default={})
    calculated_at = Column(DateTime, server_default=func.now())
    
    # Relationships - use back_populates consistently
    business = relationship("Business", back_populates="credit_scores")
    
    def to_dict(self):
        return {
            "id": self.id,
            "business_id": self.business_id,
            "smartpesa_score": self.smartpesa_score,
            "revenue_consistency_score": self.revenue_consistency_score,
            "cash_buffer_ratio": self.cash_buffer_ratio,
            "debt_coverage_capacity": self.debt_coverage_capacity,
            "inventory_health_score": self.inventory_health_score,
            "factors": self.factors,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }
