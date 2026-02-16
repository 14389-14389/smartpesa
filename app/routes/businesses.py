# app/routes/businesses.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/businesses", tags=["businesses"])

# Get current user dependency
def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# Create business
@router.post("/", response_model=schemas.Business)
def create_business(
    business: schemas.BusinessCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_business = models.Business(**business.dict(), owner_id=current_user.id)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

# Get all businesses for current user
@router.get("/", response_model=List[schemas.Business])
def get_businesses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    businesses = db.query(models.Business).filter(
        models.Business.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    return businesses

# Get single business
@router.get("/{business_id}", response_model=schemas.Business)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

# Update business
@router.put("/{business_id}", response_model=schemas.Business)
def update_business(
    business_id: int,
    business_update: schemas.BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    for key, value in business_update.dict(exclude_unset=True).items():
        setattr(business, key, value)
    
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
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    db.delete(business)
    db.commit()
    return {"message": "Business deleted successfully"}