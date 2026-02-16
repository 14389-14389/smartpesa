from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import auth, models
from app.ml.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

@router.get("/{business_id}/7days")
def forecast_7_days(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get 7-day cash flow forecast"""
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
    
    # Generate forecast
    service = ForecastService(db)
    forecast = service.generate_forecast(business_id, days_forward=7)
    
    return forecast

@router.get("/{business_id}/30days")
def forecast_30_days(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get 30-day cash flow forecast"""
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
    
    # Generate forecast
    service = ForecastService(db)
    forecast = service.generate_forecast(business_id, days_forward=30)
    
    return forecast

@router.get("/{business_id}/risk-alert")
def get_risk_alert(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get risk alert for business"""
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
    
    # Generate risk alert
    service = ForecastService(db)
    alert = service.get_risk_alert(business_id)
    
    return alert

@router.get("/{business_id}/health")
def forecast_health(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check if business has enough data for forecasting"""
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
    
    # Check data sufficiency
    from app.ml.data_pipeline import DataPipeline
    pipeline = DataPipeline(db)
    data = pipeline.prepare_daily_data(business_id, days=365)
    
    if data.empty:
        return {
            'ready': False,
            'message': 'No transaction data found',
            'days_of_data': 0,
            'required_days': 30
        }
    
    days_of_data = len(data)
    ready = days_of_data >= 30
    
    return {
        'ready': ready,
        'message': 'Sufficient data for forecasting' if ready else f'Need {30 - days_of_data} more days of data',
        'days_of_data': days_of_data,
        'required_days': 30,
        'date_range': {
            'start': data['date'].min().isoformat(),
            'end': data['date'].max().isoformat()
        }
    }
