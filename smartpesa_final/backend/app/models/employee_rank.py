from sqlalchemy import Column, Integer, String, Numeric, Text, TIMESTAMP, func
from app.database import Base

class EmployeeRank(Base):
    __tablename__ = "employee_ranks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    base_salary = Column(Numeric(10,2), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
