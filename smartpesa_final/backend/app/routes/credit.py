from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app import auth, models
from app.schemas import credit as schemas
from app.credit.scoring import CreditScoringEngine

router = APIRouter(prefix="/credit", tags=["credit"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# Get current credit score for a business
@router.get("/business/{business_id}", response_model=schemas.CreditScore)
def get_credit_score(
    business_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get the latest credit score for a business"""
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
    
    # Check for existing valid score (less than 30 days old)
    if not force_refresh:
        valid_score = db.query(models.CreditScore).filter(
            models.CreditScore.business_id == business_id,
            models.CreditScore.valid_until > datetime.utcnow()
        ).order_by(models.CreditScore.calculation_date.desc()).first()
        
        if valid_score:
            return valid_score
    
    # Calculate new score
    engine = CreditScoringEngine(db)
    new_score = engine.calculate_credit_score(business_id, current_user.id)
    
    if not new_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not calculate credit score. Insufficient data?"
        )
    
    return new_score

# Get credit score history
@router.get("/business/{business_id}/history", response_model=List[schemas.CreditScore])
def get_credit_score_history(
    business_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get credit score history for a business"""
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
    
    scores = db.query(models.CreditScore).filter(
        models.CreditScore.business_id == business_id
    ).order_by(models.CreditScore.calculation_date.desc()).limit(limit).all()
    
    return scores

# Lender API - Get risk profile (simulated authentication)
@router.get("/lender/business/{business_id}", response_model=schemas.LenderRiskProfile)
def get_lender_risk_profile(
    business_id: int,
    api_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lender API endpoint to get risk profile for a business"""
    # Simple API key check (in production, use proper authentication)
    # For demo, we'll accept any key or no key
    # if api_key != "test_lender_key":
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid API key"
    #     )
    
    # Get business
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    # Get latest credit score
    credit_score = db.query(models.CreditScore).filter(
        models.CreditScore.business_id == business_id
    ).order_by(models.CreditScore.calculation_date.desc()).first()
    
    if not credit_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No credit score available for this business"
        )
    
    # Generate lender profile
    engine = CreditScoringEngine(db)
    profile = engine.get_lender_risk_profile(business_id, credit_score)
    
    return profile

# Get all businesses with credit scores (for lenders)
@router.get("/lender/businesses")
def get_all_business_scores(
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lender API to get all businesses with credit scores"""
    query = db.query(
        models.Business.id,
        models.Business.name,
        models.User.email.label('owner_email'),
        models.CreditScore.smartpesa_score,
        models.CreditScore.calculation_date,
        models.CreditScore.valid_until
    ).join(
        models.User, models.User.id == models.Business.owner_id
    ).join(
        models.CreditScore, models.CreditScore.business_id == models.Business.id
    ).filter(
        models.CreditScore.valid_until > datetime.utcnow()
    )
    
    # Apply filters
    if min_score:
        query = query.filter(models.CreditScore.smartpesa_score >= min_score)
    if max_score:
        query = query.filter(models.CreditScore.smartpesa_score <= max_score)
    
    # Determine risk level based on score
    results = query.limit(limit).all()
    
    businesses = []
    for b in results:
        # Determine risk level
        if b.smartpesa_score >= 700:
            level = "LOW"
        elif b.smartpesa_score >= 500:
            level = "MEDIUM"
        else:
            level = "HIGH"
        
        # Filter by risk level if specified
        if risk_level and level != risk_level:
            continue
        
        businesses.append({
            "business_id": b.id,
            "business_name": b.name,
            "owner_email": b.owner_email,
            "smartpesa_score": b.smartpesa_score,
            "risk_level": level,
            "calculation_date": b.calculation_date,
            "valid_until": b.valid_until
        })
    
    return {
        "total": len(businesses),
        "businesses": businesses
    }

# Calculate credit score for all businesses (admin function)
@router.post("/calculate-all")
def calculate_all_scores(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate credit scores for all businesses belonging to the user"""
    businesses = db.query(models.Business).filter(
        models.Business.owner_id == current_user.id
    ).all()
    
    engine = CreditScoringEngine(db)
    results = []
    
    for business in businesses:
        # Delete old scores
        db.query(models.CreditScore).filter(
            models.CreditScore.business_id == business.id
        ).delete()
        
        # Calculate new score
        score = engine.calculate_credit_score(business.id, current_user.id)
        if score:
            results.append({
                "business_id": business.id,
                "business_name": business.name,
                "smartpesa_score": score.smartpesa_score
            })
    
    db.commit()
    
    return {
        "message": f"Calculated scores for {len(results)} businesses",
        "results": results
    }
