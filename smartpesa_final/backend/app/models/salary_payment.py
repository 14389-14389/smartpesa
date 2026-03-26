from sqlalchemy import Column, Integer, String, Numeric, Date, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class SalaryPayment(Base):
    __tablename__ = "salary_payments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    payment_date = Column(Date, nullable=False)
    month = Column(String(7), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    employee = relationship("Employee", back_populates="salary_payments")
    # business relationship removed to avoid missing property in Business model