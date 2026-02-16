from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class CreditScoreBase(BaseModel):
    user_id: int
    business_id: int
    revenue_consistency_score: float
    volatility_index: float
    expense_ratio: float
    cash_buffer_ratio: float
    debt_coverage_capacity: float
    inventory_health_score: float
    business_age_score: float
    transaction_volume_score: float
    smartpesa_score: int
    metrics_json: Optional[Dict[str, Any]] = None

class CreditScoreCreate(CreditScoreBase):
    pass

class CreditScore(CreditScoreBase):
    id: int
    calculation_date: datetime
    valid_until: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Lender API schemas
class LenderRiskProfile(BaseModel):
    business_id: int
    business_name: str
    owner_email: str
    smartpesa_score: int
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    calculation_date: datetime
    valid_until: datetime
    
    # Key metrics for lenders
    avg_monthly_revenue: float
    revenue_stability: float  # coefficient of variation
    expense_ratio: float
    cash_buffer_months: float
    inventory_value: float
    business_age_months: int
    transaction_volume_12m: int
    
    class Config:
        from_attributes = True

class LenderScoreResponse(BaseModel):
    status: str
    message: str
    data: Optional[LenderRiskProfile] = None
