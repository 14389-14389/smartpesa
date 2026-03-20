from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rank_id = Column(Integer, ForeignKey("employee_ranks.id"), nullable=False)
    monthly_salary = Column(Numeric(10,2), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, onupdate=func.current_timestamp())

    rank = relationship("EmployeeRank")
    salary_payments = relationship("SalaryPayment", back_populates="employee")
