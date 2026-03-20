from sqlalchemy import Column, Integer, String, Numeric, Date, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text)
    receipt_image = Column(String(255))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    category = relationship("ExpenseCategory")
    supplier = relationship("Supplier")
    employee = relationship("Employee")
    business = relationship("Business")