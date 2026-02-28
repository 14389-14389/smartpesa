"""
Analytics routes for SmartPesa API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.business import Business
from app.utils.auth import get_current_user
from app.utils.validators import validate_business_access

router = APIRouter()

@router.get("/revenue-trends")
async def revenue_trends(
    business_id: int = Query(...),
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze revenue trends"""
    await validate_business_access(business_id, current_user.id, db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    transactions = db.query(Transaction).filter(
        Transaction.business_id == business_id,
        Transaction.type == 'income',
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date
    ).all()
    
    # Group by month
    monthly_data = {}
    for t in transactions:
        month_key = t.created_at.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += t.amount
    
    return {
        "business_id": business_id,
        "period_months": months,
        "monthly_revenue": monthly_data,
        "total_revenue": sum(monthly_data.values()),
        "average_monthly": sum(monthly_data.values()) / len(monthly_data) if monthly_data else 0
    }

@router.get("/expense-analysis")
async def expense_analysis(
    business_id: int = Query(...),
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze expense patterns"""
    await validate_business_access(business_id, current_user.id, db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    expenses = db.query(Transaction).filter(
        Transaction.business_id == business_id,
        Transaction.type == 'expense',
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date
    ).all()
    
    # By category
    by_category = {}
    for e in expenses:
        if e.category not in by_category:
            by_category[e.category] = 0
        by_category[e.category] += e.amount
    
    return {
        "business_id": business_id,
        "period_months": months,
        "by_category": by_category,
        "total_expenses": sum(by_category.values())
    }
