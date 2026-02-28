"""
Reports routes for SmartPesa API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import csv
from io import StringIO
from fastapi.responses import Response

from app.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.transaction import Transaction
from app.models.inventory import Inventory
from app.models.supplier import Supplier, Payment
from app.utils.auth import get_current_user
from app.utils.validators import validate_business_access

router = APIRouter()

@router.get("/profit-loss")
async def profit_loss_report(
    business_id: int = Query(...),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate profit and loss report"""
    await validate_business_access(business_id, current_user.id, db)
    
    if not end_date:
        end_date = datetime.utcnow().isoformat()
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    transactions = db.query(Transaction).filter(
        Transaction.business_id == business_id,
        Transaction.created_at >= start,
        Transaction.created_at <= end
    ).all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    
    return {
        "success": True,
        "data": {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_profit": total_income - total_expense
            }
        }
    }

@router.get("/export/csv")
async def export_to_csv(
    report_type: str = Query(..., regex="^(transactions|inventory|suppliers)$"),
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export data as CSV file"""
    await validate_business_access(business_id, current_user.id, db)
    
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'transactions':
        writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Type'])
        transactions = db.query(Transaction).filter(
            Transaction.business_id == business_id
        ).order_by(Transaction.created_at.desc()).all()
        
        for t in transactions:
            writer.writerow([
                t.created_at.strftime("%Y-%m-%d"),
                t.description,
                t.category,
                t.amount,
                t.type
            ])
        filename = f"transactions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    elif report_type == 'inventory':
        writer.writerow(['SKU', 'Name', 'Quantity', 'Unit', 'Price/Unit', 'Total Value'])
        inventory = db.query(Inventory).filter(Inventory.business_id == business_id).all()
        
        for i in inventory:
            writer.writerow([
                i.sku,
                i.name,
                i.quantity,
                i.unit,
                i.price_per_unit,
                i.quantity * i.price_per_unit
            ])
        filename = f"inventory_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    else:  # suppliers
        writer.writerow(['Supplier', 'Contact', 'Phone', 'Email', 'Payment Terms'])
        suppliers = db.query(Supplier).filter(Supplier.business_id == business_id).all()
        
        for s in suppliers:
            writer.writerow([
                s.name,
                s.contact_person,
                s.phone,
                s.email,
                s.payment_terms
            ])
        filename = f"suppliers_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
