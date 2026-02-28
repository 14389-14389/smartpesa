"""
Transactions routes for SmartPesa API - MySQL Compatible
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import List, Optional
from datetime import datetime, timedelta
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["transactions"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# ─────────────────────────────────────────────────────────────
# Create transaction
@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business belongs to user
    business = db.query(models.Business).filter(
        models.Business.id == transaction.business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found or doesn't belong to you"
        )
    
    db_transaction = models.Transaction(
        amount=transaction.amount,
        type=transaction.type,
        category=transaction.category,
        description=transaction.description,
        business_id=transaction.business_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# ─────────────────────────────────────────────────────────────
# Get all transactions
@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    business_id: Optional[int] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(models.Business.owner_id == current_user.id)

    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)
    if type:
        query = query.filter(models.Transaction.type == type)
    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(models.Transaction.created_at <= end_date)

    query = query.order_by(models.Transaction.created_at.desc())
    return query.offset(skip).limit(limit).all()

# ─────────────────────────────────────────────────────────────
# Get single transaction
@router.get("/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    transaction = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Transaction.id == transaction_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# ─────────────────────────────────────────────────────────────
# Update transaction
@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction_update: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    transaction = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Transaction.id == transaction_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction_update.business_id:
        new_business = db.query(models.Business).filter(
            models.Business.id == transaction_update.business_id,
            models.Business.owner_id == current_user.id
        ).first()
        if not new_business:
            raise HTTPException(status_code=404, detail="New business not found")

    update_data = transaction_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction

# ─────────────────────────────────────────────────────────────
# Delete transaction
@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    transaction = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Transaction.id == transaction_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully", "id": transaction_id}

# ─────────────────────────────────────────────────────────────
# Transaction summary (MySQL-compatible using CASE)
@router.get("/summary/overview")
def get_transaction_summary(
    business_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # MySQL-compatible query using CASE statements
    query = db.query(
        func.sum(
            case(
                (models.Transaction.type == 'income', models.Transaction.amount),
                else_=0
            )
        ).label('total_income'),
        func.sum(
            case(
                (models.Transaction.type == 'expense', models.Transaction.amount),
                else_=0
            )
        ).label('total_expense'),
        func.count(models.Transaction.id).label('transaction_count')
    ).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id,
        models.Transaction.created_at.between(start_date, end_date)
    )
    
    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)
    
    result = query.first()
    
    total_income = result.total_income or 0
    total_expense = result.total_expense or 0
    
    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "net_cashflow": float(total_income - total_expense),
        "transaction_count": result.transaction_count or 0,
        "period": f"Last {days} days",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

# ─────────────────────────────────────────────────────────────
# Analysis by category
@router.get("/analysis/by-category")
def get_transactions_by_category(
    business_id: Optional[int] = None,
    days: int = 30,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label('total'),
        func.count(models.Transaction.id).label('count')
    ).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id,
        models.Transaction.created_at.between(start_date, end_date)
    )

    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)
    if type:
        query = query.filter(models.Transaction.type == type)

    results = query.group_by(models.Transaction.category).all()

    return [
        {
            "category": r.category,
            "total": float(r.total or 0),
            "count": r.count or 0,
            "average": float(r.total / r.count) if r.count else 0
        }
        for r in results
    ]

# ─────────────────────────────────────────────────────────────
# Daily totals (MySQL-compatible using CASE)
@router.get("/analysis/daily-totals")
def get_daily_totals(
    business_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(
        func.date(models.Transaction.created_at).label('date'),
        func.sum(
            case(
                (models.Transaction.type == 'income', models.Transaction.amount),
                else_=0
            )
        ).label('income'),
        func.sum(
            case(
                (models.Transaction.type == 'expense', models.Transaction.amount),
                else_=0
            )
        ).label('expense')
    ).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id,
        models.Transaction.created_at.between(start_date, end_date)
    )

    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)

    results = query.group_by('date').order_by('date').all()

    return [
        {
            "date": str(r.date),
            "income": float(r.income or 0),
            "expense": float(r.expense or 0),
            "net": float((r.income or 0) - (r.expense or 0))
        }
        for r in results
    ]

# Simple test endpoint
@router.get("/test")
def test_endpoint():
    """Simple test endpoint that always works"""
    return {"status": "ok", "message": "Transactions route is working"}
