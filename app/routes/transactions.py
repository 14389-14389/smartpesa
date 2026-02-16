from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Get current user dependency
def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# Create transaction
@router.post("/", response_model=schemas.Transaction)
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
    
    # Create transaction
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

# Get all transactions for user's businesses
@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    business_id: Optional[int] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Base query - only transactions from user's businesses
    query = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id
    )
    
    # Apply filters
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
    
    # Order by most recent first
    query = query.order_by(models.Transaction.created_at.desc())
    
    return query.offset(skip).limit(limit).all()

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

# Update transaction
@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction_update: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get transaction and verify ownership
    transaction = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Transaction.id == transaction_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # If business_id is being updated, verify new business belongs to user
    if transaction_update.business_id:
        new_business = db.query(models.Business).filter(
            models.Business.id == transaction_update.business_id,
            models.Business.owner_id == current_user.id
        ).first()
        
        if not new_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New business not found or doesn't belong to you"
            )
    
    # Update only provided fields
    update_data = transaction_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transaction, key, value)
    
    db.commit()
    db.refresh(transaction)
    return transaction

# Delete transaction
@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get transaction and verify ownership
    transaction = db.query(models.Transaction).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Transaction.id == transaction_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully", "id": transaction_id}

# Get transaction summary/stats
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
    
    # Base query
    query = db.query(
        func.sum(models.Transaction.amount).filter(models.Transaction.type == 'income').label('total_income'),
        func.sum(models.Transaction.amount).filter(models.Transaction.type == 'expense').label('total_expense'),
        func.count(models.Transaction.id).label('transaction_count'),
        func.count(models.Transaction.id).filter(models.Transaction.type == 'income').label('income_count'),
        func.count(models.Transaction.id).filter(models.Transaction.type == 'expense').label('expense_count')
    ).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id,
        models.Transaction.created_at.between(start_date, end_date)
    )
    
    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)
    
    result = query.first()
    
    # Calculate values (handle None)
    total_income = result.total_income or 0
    total_expense = result.total_expense or 0
    net_cashflow = total_income - total_expense
    
    return {
        "period": f"Last {days} days",
        "start_date": start_date,
        "end_date": end_date,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_cashflow": net_cashflow,
        "transaction_count": result.transaction_count or 0,
        "income_count": result.income_count or 0,
        "expense_count": result.expense_count or 0,
        "income_expense_ratio": round(total_income / total_expense, 2) if total_expense > 0 else None
    }

# Get transactions by category
@router.get("/analysis/by-category")
def get_transactions_by_category(
    business_id: Optional[int] = None,
    days: int = 30,
    type: Optional[str] = None,  # income or expense
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Base query
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
    
    query = query.group_by(models.Transaction.category)
    
    results = query.all()
    
    return [
        {
            "category": r.category,
            "total": r.total or 0,
            "count": r.count or 0,
            "average": (r.total / r.count) if r.count else 0
        }
        for r in results
    ]

# Get daily totals for charts
@router.get("/analysis/daily-totals")
def get_daily_totals(
    business_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query daily totals
    query = db.query(
        func.date(models.Transaction.created_at).label('date'),
        func.sum(models.Transaction.amount).filter(models.Transaction.type == 'income').label('income'),
        func.sum(models.Transaction.amount).filter(models.Transaction.type == 'expense').label('expense')
    ).join(
        models.Business, models.Business.id == models.Transaction.business_id
    ).filter(
        models.Business.owner_id == current_user.id,
        models.Transaction.created_at.between(start_date, end_date)
    )
    
    if business_id:
        query = query.filter(models.Transaction.business_id == business_id)
    
    query = query.group_by('date').order_by('date')
    
    results = query.all()
    
    return [
        {
            "date": r.date,
            "income": r.income or 0,
            "expense": r.expense or 0,
            "net": (r.income or 0) - (r.expense or 0)
        }
        for r in results
    ]