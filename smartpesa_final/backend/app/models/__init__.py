"""
Models package for SmartPesa
"""

from app.database import Base

# Import all existing models
from .user import User
from .business import Business
from .transaction import Transaction
from .inventory import Inventory
from .supplier import Supplier, Payment
from .notification import Notification
from .credit import CreditScore

# Import purchase and inventory movement models (if they exist)
from .purchase_batch import PurchaseBatch
from .inventory_movement import InventoryMovement

# Import sales models
from .sale import Sale
from .sale_item import SaleItem

# Import employee and expense models
from .employee_rank import EmployeeRank
from .employee import Employee
from .salary_payment import SalaryPayment
from .expense_category import ExpenseCategory
from .expense import Expense

__all__ = [
    'Base',
    'User',
    'Business',
    'Transaction',
    'Inventory',
    'Supplier',
    'Payment',
    'Notification',
    'CreditScore',
    'PurchaseBatch',
    'InventoryMovement',
    'Sale',
    'SaleItem',
    'EmployeeRank',
    'Employee',
    'SalaryPayment',
    'ExpenseCategory',
    'Expense',
]