"""
Validation utilities for SmartPesa
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import re

from app.models import Business

async def validate_business_access(
    business_id: int,
    user_id: int,
    db: Session
) -> Business:
    """
    Validate that a user has access to a business
    Returns the business if valid, raises HTTPException otherwise
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    if business.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this business"
        )
    
    return business

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format (Kenyan)"""
    pattern = r'^(\+254|0)[7][0-9]{8}$'
    return re.match(pattern, phone) is not None

def validate_amount(amount: float) -> bool:
    """Validate transaction amount"""
    return amount > 0 and amount < 1000000000  # Max 1 billion
