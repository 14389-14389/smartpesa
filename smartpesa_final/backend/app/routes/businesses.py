# app/routes/businesses.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app import models, auth
from app.database import get_db
from app.utils.auth import get_current_user

# IMPORTANT: No prefix here - prefix will be added in main.py
router = APIRouter(tags=["businesses"])

# Pydantic schemas
class BusinessBase(BaseModel):
    name: str
    type: Optional[str] = "retail"
    currency: Optional[str] = "KES"

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    pass

class Business(BusinessBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Create business
@router.post("/", response_model=Business, status_code=201)
def create_business(
    business: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new business"""
    db_business = models.Business(
        name=business.name,
        type=business.type,
        currency=business.currency,
        owner_id=current_user.id
    )
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

# Get all businesses for current user
@router.get("/", response_model=List[Business])
def get_businesses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all businesses for current user"""
    businesses = db.query(models.Business).filter(
        models.Business.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    return businesses

# Get single business
@router.get("/{business_id}", response_model=Business)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific business"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

# Update business
@router.put("/{business_id}", response_model=Business)
def update_business(
    business_id: int,
    business_update: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a business"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if business_update.name is not None:
        business.name = business_update.name
    if business_update.type is not None:
        business.type = business_update.type
    if business_update.currency is not None:
        business.currency = business_update.currency
    
    db.commit()
    db.refresh(business)
    return business

# Delete business
@router.delete("/{business_id}")
def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a business"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    db.delete(business)
    db.commit()
    return {"message": "Business deleted successfully"}
