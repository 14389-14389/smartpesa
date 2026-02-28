from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import auth, models
from app.schemas.supplier import (
    Supplier, SupplierCreate, SupplierUpdate,
    SupplierPayment, SupplierPaymentCreate, SupplierPaymentUpdate,
    SupplierWithPayments
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# ============== SUPPLIER CRUD ==============

# Create supplier
@router.post("/", response_model=Supplier)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == supplier.business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    db_supplier = models.Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# Get all suppliers for a business
@router.get("/", response_model=List[Supplier])
def get_suppliers(
    business_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.business_id == business_id
    ).offset(skip).limit(limit).all()
    
    return suppliers

# Get single supplier
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Get payments
    payments = db.query(models.SupplierPayment).filter(
        models.SupplierPayment.supplier_id == supplier_id
    ).all()
    
    # Calculate totals
    total_outstanding = sum(p.amount for p in payments if p.status == "pending")
    overdue = sum(p.amount for p in payments if p.status == "pending" and p.due_date < datetime.utcnow())
    
    # Convert to dict and add extra fields
    result = {
        **supplier.__dict__,
        "payments": payments,
        "total_outstanding": total_outstanding,
        "overdue_amount": overdue
    }
    
    return result

# Update supplier
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    for key, value in supplier_update.dict(exclude_unset=True).items():
        setattr(supplier, key, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier

# Delete supplier
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}

# ============== SUPPLIER PAYMENTS ==============

# Create supplier payment
@router.post("/payments", response_model=SupplierPayment)
def create_supplier_payment(
    payment: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify supplier belongs to user's business
    supplier = db.query(models.Supplier).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.Supplier.id == payment.supplier_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    db_payment = models.SupplierPayment(
        **payment.dict(),
        status="pending"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

# Get all payments for a business
@router.get("/payments/all", response_model=List[SupplierPayment])
def get_all_payments(
    business_id: int,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    query = db.query(models.SupplierPayment).join(
        models.Supplier, models.Supplier.id == models.SupplierPayment.supplier_id
    ).filter(
        models.Supplier.business_id == business_id
    )
    
    if status:
        query = query.filter(models.SupplierPayment.status == status)
    
    return query.order_by(models.SupplierPayment.due_date).offset(skip).limit(limit).all()

# Mark payment as paid
@router.put("/payments/{payment_id}/pay", response_model=SupplierPayment)
def mark_payment_paid(
    payment_id: int,
    transaction_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.SupplierPayment).join(
        models.Supplier, models.Supplier.id == models.SupplierPayment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.SupplierPayment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment.status = "paid"
    payment.paid_date = datetime.utcnow()
    payment.transaction_id = transaction_id
    
    db.commit()
    db.refresh(payment)
    return payment

# Update payment
@router.put("/payments/{payment_id}", response_model=SupplierPayment)
def update_payment(
    payment_id: int,
    payment_update: SupplierPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.SupplierPayment).join(
        models.Supplier, models.Supplier.id == models.SupplierPayment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.SupplierPayment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    for key, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, key, value)
    
    db.commit()
    db.refresh(payment)
    return payment

# Delete payment
@router.delete("/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment = db.query(models.SupplierPayment).join(
        models.Supplier, models.Supplier.id == models.SupplierPayment.supplier_id
    ).join(
        models.Business, models.Business.id == models.Supplier.business_id
    ).filter(
        models.SupplierPayment.id == payment_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}

# ============== OUTSTANDING BALANCES ==============

# Get outstanding balances summary
@router.get("/outstanding/summary")
def get_outstanding_summary(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    # Get all pending payments
    payments = db.query(models.SupplierPayment).join(
        models.Supplier, models.Supplier.id == models.SupplierPayment.supplier_id
    ).filter(
        models.Supplier.business_id == business_id,
        models.SupplierPayment.status == "pending"
    ).all()
    
    now = datetime.utcnow()
    total_outstanding = 0
    overdue_total = 0
    upcoming_total = 0
    
    for p in payments:
        total_outstanding += p.amount
        if p.due_date < now:
            overdue_total += p.amount
        else:
            upcoming_total += p.amount
    
    return {
        "total_outstanding": total_outstanding,
        "overdue_total": overdue_total,
        "upcoming_total": upcoming_total,
        "payment_count": len(payments),
        "overdue_count": len([p for p in payments if p.due_date < now])
    }

# Get outstanding by supplier
@router.get("/outstanding/by-supplier")
def get_outstanding_by_supplier(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.business_id == business_id
    ).all()
    
    result = []
    now = datetime.utcnow()
    
    for supplier in suppliers:
        payments = db.query(models.SupplierPayment).filter(
            models.SupplierPayment.supplier_id == supplier.id,
            models.SupplierPayment.status == "pending"
        ).all()
        
        total = sum(p.amount for p in payments)
        overdue = sum(p.amount for p in payments if p.due_date < now)
        
        if total > 0:
            result.append({
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "total_outstanding": total,
                "overdue_amount": overdue,
                "payment_count": len(payments)
            })
    
    return result
