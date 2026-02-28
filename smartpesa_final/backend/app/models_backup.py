from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    businesses = relationship("Business", back_populates="owner", cascade="all, delete-orphan")
    credit_scores = relationship("CreditScore", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="businesses")
    transactions = relationship("Transaction", back_populates="business", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="business", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="business", cascade="all, delete-orphan")
    credit_scores = relationship("CreditScore", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Business {self.name}>"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # income or expense
    category = Column(String, nullable=False)
    description = Column(String)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    business = relationship("Business", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.type}: {self.amount}>"


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, index=True)
    quantity = Column(Float, default=0)
    unit = Column(String, default="pieces")
    price_per_unit = Column(Float, default=0)
    reorder_level = Column(Float, default=10)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="inventory")
    transactions = relationship("InventoryTransaction", back_populates="item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inventory {self.name}: {self.quantity} {self.unit}>"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False)
    quantity_change = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # "purchase", "sale", "adjustment", "return"
    reference_id = Column(Integer)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    item = relationship("Inventory", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.transaction_type}: {self.quantity_change}>"


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    payment_terms = Column(String)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    business = relationship("Business", back_populates="suppliers")
    payments = relationship("SupplierPayment", back_populates="supplier", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Supplier {self.name}>"


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_date = Column(DateTime(timezone=True))
    status = Column(String, default="pending")  # "pending", "paid", "overdue"
    notes = Column(String)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="payments")
    transaction = relationship("Transaction")

    def __repr__(self):
        return f"<SupplierPayment {self.amount} due {self.due_date}>"


class CreditScore(Base):
    __tablename__ = "credit_scores"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    
    # Score components
    revenue_consistency_score = Column(Float)  # 0-100
    volatility_index = Column(Float)  # 0-100
    expense_ratio = Column(Float)  # 0-100
    cash_buffer_ratio = Column(Float)  # 0-100
    debt_coverage_capacity = Column(Float)  # 0-100
    inventory_health_score = Column(Float)  # 0-100
    business_age_score = Column(Float)  # 0-100
    transaction_volume_score = Column(Float)  # 0-100
    
    # Overall score
    smartpesa_score = Column(Integer)  # 0-1000
    
    # Raw metrics for transparency
    metrics_json = Column(JSON)  # Store all raw metrics
    
    calculation_date = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))  # Score valid for 30 days
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="credit_scores")
    business = relationship("Business", back_populates="credit_scores")

    def __repr__(self):
        return f"<CreditScore {self.smartpesa_score} for Business {self.business_id}>"
