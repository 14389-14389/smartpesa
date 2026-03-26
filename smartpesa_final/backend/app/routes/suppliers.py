from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.sql import text
from app.database import get_db
from app import auth, models
from app.models.transaction import Transaction
from app.schemas.supplier import (
    Supplier, SupplierCreate, SupplierUpdate,
    SupplierPayment, SupplierPaymentCreate, SupplierPaymentUpdate,
    SupplierWithPayments
)

router = APIRouter(tags=["suppliers"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# ============== SUPPLIER CRUD ==============

@router.post("/", response_model=Supplier)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == supplier.business_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(404, "Business not found")
    db_supplier = models.Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@router.get("/", response_model=List[Supplier])
def get_suppliers(
    business_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(404, "Business not found")
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.business_id == business_id
    ).offset(skip).limit(limit).all()
    return suppliers

@router.get("/{supplier_id}", response_model=SupplierWithPayments)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    payments = db.query(models.Payment).filter(
        models.Payment.supplier_id == supplier_id
    ).all()
    today = date.today()
    total_outstanding = sum(p.amount for p in payments if not p.paid)
    overdue = sum(p.amount for p in payments if not p.paid and p.due_date and p.due_date < today)
    result = SupplierWithPayments(
        **supplier.__dict__,
        payments=payments,
        total_outstanding=total_outstanding,
        overdue_amount=overdue
    )
    return result

@router.put("/{supplier_id}", response_model=Supplier)
def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    for key, value in supplier_update.dict(exclude_unset=True).items():
        setattr(supplier, key, value)
    db.commit()
    db.refresh(supplier)
    return supplier

@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}

# ============== HELPER ==============

def get_or_create_supplier_payment_category(db: Session):
    """Get or create the expense category for supplier payments."""
    try:
        from app.models.expense_category import ExpenseCategory
        category = db.query(ExpenseCategory).filter(
            ExpenseCategory.name == "Supplier Payment"
        ).first()
        if not category:
            category = ExpenseCategory(
                name="Supplier Payment",
                description="Payments made to suppliers"
            )
            db.add(category)
            db.flush()
        return category
    except ImportError:
        # Fallback using raw SQL
        result = db.execute(
            text("SELECT id FROM expense_categories WHERE name = 'Supplier Payment'")
        ).first()
        if result:
            class DummyCategory:
                def __init__(self, id):
                    self.id = id
            return DummyCategory(result[0])
        else:
            db.execute(
                text("INSERT INTO expense_categories (name, description) VALUES ('Supplier Payment', 'Payments made to suppliers')")
            )
            db.flush()
            new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            class DummyCategory:
                def __init__(self, id):
                    self.id = id
            return DummyCategory(new_id)

# ============== SUPPLIER PAYMENTS (RECORD) ==============

class PaymentRecord(BaseModel):
    amount: float
    payment_date: date
    notes: Optional[str] = None
    business_id: int

@router.post("/{supplier_id}/payments", status_code=status.HTTP_201_CREATED)
def record_supplier_payment(
    supplier_id: int,
    payment: PaymentRecord,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Record a payment to a supplier. Creates an expense, a transaction, and a payment record.
    """
    # Verify supplier belongs to user's business
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    
    # Ensure business_id matches supplier's business
    if payment.business_id != supplier.business_id:
        raise HTTPException(400, "Business ID does not match supplier")
    
    # Get or create expense category
    category = get_or_create_supplier_payment_category(db)
    
    # Convert date to string
    payment_date_str = payment.payment_date.strftime("%Y-%m-%d")
    now = datetime.utcnow()
    
    # ========== Create expense record ==========
    expense_result = db.execute(
        text("""
            INSERT INTO expenses (category_id, amount, expense_date, description, business_id, supplier_id)
            VALUES (:cat_id, :amount, :date, :desc, :bus_id, :sup_id)
        """),
        {
            "cat_id": category.id,
            "amount": payment.amount,
            "date": payment_date_str,
            "desc": payment.notes or f"Payment to supplier {supplier.name}",
            "bus_id": supplier.business_id,
            "sup_id": supplier_id
        }
    )
    expense_id = expense_result.lastrowid
    
    # ========== Create transaction record and capture its ID ==========
    trans_result = db.execute(
        text("""
            INSERT INTO transactions (business_id, amount, type, category, description, reference, created_at)
            VALUES (:bus_id, :amount, 'expense', 'Supplier Payment', :desc, :ref, :created_at)
        """),
        {
            "bus_id": supplier.business_id,
            "amount": payment.amount,
            "desc": payment.notes or f"Payment to supplier {supplier.name}",
            "ref": f"SUP-PAY-{expense_id}",
            "created_at": now
        }
    )
    transaction_id = trans_result.lastrowid   # capture the auto-increment ID
    
    # ========== Create payment record using the transaction ID ==========
    db.execute(
        text("""
            INSERT INTO payments (supplier_id, amount, payment_date, due_date, notes, paid, paid_date, transaction_id)
            VALUES (:sup_id, :amount, :payment_date, :due_date, :notes, 1, :paid_date, :trans_id)
        """),
        {
            "sup_id": supplier_id,
            "amount": payment.amount,
            "payment_date": payment_date_str,
            "due_date": payment_date_str,
            "notes": payment.notes,
            "paid_date": now,
            "trans_id": transaction_id      # use the captured transaction ID
        }
    )
    
    db.commit()
    
    return {
        "message": "Payment recorded successfully",
        "expense_id": expense_id
    }

# ============== PAYMENT LISTING ==============

@router.get("/payments/all", response_model=List[dict])
def get_all_payments(
    business_id: int,
    paid_only: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all payments for a business. Returns a list of dictionaries with supplier names.
    """
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(404, "Business not found")

    # Build query joining Payment with Supplier to get supplier name
    query = db.query(
        models.Payment,
        models.Supplier.name.label("supplier_name")
    ).join(
        models.Supplier, models.Supplier.id == models.Payment.supplier_id
    ).filter(
        models.Supplier.business_id == business_id
    )
    if paid_only is not None:
        query = query.filter(models.Payment.paid == paid_only)

    # Order by payment_date descending (most recent first)
    results = query.order_by(models.Payment.payment_date.desc()).offset(skip).limit(limit).all()

    payments_list = []
    for payment, supplier_name in results:
        # Use getattr to safely access paid_date (in case model is missing it)
        paid_date = getattr(payment, 'paid_date', None)
        payments_list.append({
            "id": payment.id,
            "supplier_id": payment.supplier_id,
            "supplier_name": supplier_name,
            "amount": payment.amount,
            "due_date": payment.payment_date,        # map payment_date to due_date for frontend
            "paid": payment.paid,
            "paid_date": paid_date,
            "notes": payment.notes,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at
        })
    return payments_list

# ============== OTHER PAYMENT ENDPOINTS ==============

@router.post("/payments", response_model=SupplierPayment)
def create_supplier_payment(
    payment: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == payment.supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    db_payment = models.Payment(**payment.dict(), paid=False)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.put("/payments/{payment_id}/pay", response_model=SupplierPayment)
def mark_payment_paid(
    payment_id: int,
    transaction_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.Payment).join(
        models.Supplier, models.Supplier.id == models.Payment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Payment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if transaction_id is None:
        supplier = payment.supplier
        new_transaction = Transaction(
            business_id=supplier.business_id,
            amount=payment.amount,
            type='expense',
            category='Supplier Payment',
            description=f"Payment to supplier {supplier.name}",
            reference=f"PAY-{payment.id}",
            created_at=datetime.utcnow()
        )
        db.add(new_transaction)
        db.flush()
        transaction_id = new_transaction.id
    else:
        transaction = db.get(Transaction, transaction_id)
        if not transaction:
            raise HTTPException(404, "Transaction not found")
    payment.paid = True
    payment.paid_date = datetime.utcnow()
    payment.transaction_id = transaction_id
    db.commit()
    db.refresh(payment)
    return payment

@router.put("/payments/{payment_id}", response_model=SupplierPayment)
def update_payment(
    payment_id: int,
    payment_update: SupplierPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.Payment).join(
        models.Supplier, models.Supplier.id == models.Payment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Payment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    for key, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, key, value)
    db.commit()
    db.refresh(payment)
    return payment

@router.delete("/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.Payment).join(
        models.Supplier, models.Supplier.id == models.Payment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Payment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}

@router.get("/outstanding/summary")
def get_outstanding_summary(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(404, "Business not found")
    payments = db.query(models.Payment).join(
        models.Supplier, models.Supplier.id == models.Payment.supplier_id
    ).filter(
        models.Supplier.business_id == business_id,
        models.Payment.paid == False
    ).all()
    today = date.today()
    total_outstanding = 0
    overdue_total = 0
    upcoming_total = 0
    for p in payments:
        total_outstanding += p.amount
        if p.due_date and p.due_date < today:
            overdue_total += p.amount
        else:
            upcoming_total += p.amount
    return {
        "total_outstanding": total_outstanding,
        "overdue_total": overdue_total,
        "upcoming_total": upcoming_total,
        "payment_count": len(payments),
        "overdue_count": len([p for p in payments if p.due_date and p.due_date < today])
    }

@router.get("/outstanding/by-supplier")
def get_outstanding_by_supplier(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(404, "Business not found")
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.business_id == business_id
    ).all()
    result = []
    today = date.today()
    for supplier in suppliers:
        payments = db.query(models.Payment).filter(
            models.Payment.supplier_id == supplier.id,
            models.Payment.paid == False
        ).all()
        total = sum(p.amount for p in payments)
        overdue = sum(p.amount for p in payments if p.due_date and p.due_date < today)
        if total > 0:
            result.append({
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "total_outstanding": total,
                "overdue_amount": overdue,
                "payment_count": len(payments)
            })
    return result