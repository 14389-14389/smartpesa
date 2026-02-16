import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
import json

class CreditScoringEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_credit_score(self, business_id: int, user_id: int):
        """Calculate comprehensive credit score for a business"""
        
        # Get business
        business = self.db.query(models.Business).filter(
            models.Business.id == business_id,
            models.Business.owner_id == user_id
        ).first()
        
        if not business:
            return None
        
        # Calculate all component scores
        revenue_consistency = self._calculate_revenue_consistency(business_id)
        volatility = self._calculate_volatility_index(business_id)
        expense_ratio = self._calculate_expense_ratio(business_id)
        cash_buffer = self._calculate_cash_buffer_ratio(business_id)
        debt_coverage = self._calculate_debt_coverage(business_id)
        inventory_health = self._calculate_inventory_health(business_id)
        business_age = self._calculate_business_age_score(business.created_at)
        transaction_volume = self._calculate_transaction_volume_score(business_id)
        
        # Store raw metrics for transparency
        metrics_json = {
            "revenue_consistency": revenue_consistency,
            "volatility_index": volatility,
            "expense_ratio": expense_ratio,
            "cash_buffer_ratio": cash_buffer,
            "debt_coverage_capacity": debt_coverage,
            "inventory_health_score": inventory_health,
            "business_age_score": business_age,
            "transaction_volume_score": transaction_volume
        }
        
        # Calculate weighted score (0-1000)
        weights = {
            "revenue_consistency": 0.20,
            "volatility_index": 0.15,
            "expense_ratio": 0.10,
            "cash_buffer_ratio": 0.15,
            "debt_coverage_capacity": 0.15,
            "inventory_health_score": 0.10,
            "business_age_score": 0.05,
            "transaction_volume_score": 0.10
        }
        
        weighted_score = (
            revenue_consistency * weights["revenue_consistency"] +
            (100 - volatility) * weights["volatility_index"] +  # Lower volatility is better
            (100 - expense_ratio) * weights["expense_ratio"] +  # Lower expense ratio is better
            cash_buffer * weights["cash_buffer_ratio"] +
            debt_coverage * weights["debt_coverage_capacity"] +
            inventory_health * weights["inventory_health_score"] +
            business_age * weights["business_age_score"] +
            transaction_volume * weights["transaction_volume_score"]
        )
        
        # Scale to 0-1000
        smartpesa_score = int(weighted_score * 10)
        
        # Create credit score record
        credit_score = models.CreditScore(
            user_id=user_id,
            business_id=business_id,
            revenue_consistency_score=revenue_consistency,
            volatility_index=volatility,
            expense_ratio=expense_ratio,
            cash_buffer_ratio=cash_buffer,
            debt_coverage_capacity=debt_coverage,
            inventory_health_score=inventory_health,
            business_age_score=business_age,
            transaction_volume_score=transaction_volume,
            smartpesa_score=smartpesa_score,
            metrics_json=metrics_json,
            valid_until=datetime.utcnow() + timedelta(days=30)  # Score valid for 30 days
        )
        
        self.db.add(credit_score)
        self.db.commit()
        self.db.refresh(credit_score)
        
        return credit_score
    
    def _calculate_revenue_consistency(self, business_id: int) -> float:
        """Calculate revenue consistency score (0-100)"""
        # Get monthly revenue for last 12 months
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        monthly_revenue = self.db.query(
            func.strftime('%Y-%m', models.Transaction.created_at).label('month'),
            func.sum(models.Transaction.amount).label('revenue')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.type == 'income',
            models.Transaction.created_at.between(start_date, end_date)
        ).group_by('month').all()
        
        if len(monthly_revenue) < 3:
            return 50  # Default for insufficient data
        
        revenues = [r.revenue for r in monthly_revenue]
        
        # Calculate coefficient of variation (CV)
        mean_rev = np.mean(revenues)
        if mean_rev == 0:
            return 50
        
        std_rev = np.std(revenues)
        cv = std_rev / mean_rev
        
        # Convert CV to score (lower CV = higher score)
        # CV of 0 = 100, CV of 1 = 0
        score = max(0, min(100, 100 * (1 - cv)))
        
        return score
    
    def _calculate_volatility_index(self, business_id: int) -> float:
        """Calculate volatility index (0-100, higher = more volatile)"""
        # Get daily net cash flow for last 90 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        daily_net = self.db.query(
            func.date(models.Transaction.created_at).label('date'),
            func.sum(models.Transaction.amount).label('net')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).group_by('date').all()
        
        if len(daily_net) < 30:
            return 50  # Default for insufficient data
        
        net_values = [d.net for d in daily_net]
        
        # Calculate volatility as standard deviation / mean
        mean_net = np.mean(net_values)
        if mean_net == 0:
            return 50
        
        std_net = np.std(net_values)
        volatility = std_net / abs(mean_net)
        
        # Scale to 0-100 (higher volatility = higher score)
        score = min(100, volatility * 50)
        
        return score
    
    def _calculate_expense_ratio(self, business_id: int) -> float:
        """Calculate expense ratio (0-100, higher = higher expenses)"""
        # Get last 3 months
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        # Sum income and expenses
        result = self.db.query(
            func.sum(models.Transaction.amount).filter(models.Transaction.type == 'income').label('income'),
            func.sum(models.Transaction.amount).filter(models.Transaction.type == 'expense').label('expense')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).first()
        
        income = result.income or 0
        expense = result.expense or 0
        
        if income == 0:
            return 100  # All expenses, no income
        
        ratio = (expense / income) * 100
        return min(100, ratio)
    
    def _calculate_cash_buffer_ratio(self, business_id: int) -> float:
        """Calculate cash buffer ratio (0-100, higher = better)"""
        # Get last 3 months of net cash flow
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        net_cashflow = self.db.query(
            func.sum(models.Transaction.amount).label('net')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).first()[0] or 0
        
        if net_cashflow <= 0:
            return 0
        
        # Calculate average monthly expense
        monthly_expense = self.db.query(
            func.sum(models.Transaction.amount).label('expense')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.type == 'expense',
            models.Transaction.created_at.between(start_date, end_date)
        ).first()[0] or 1
        
        avg_monthly_expense = monthly_expense / 3
        
        if avg_monthly_expense == 0:
            return 100
        
        # Cash buffer in months
        buffer_months = net_cashflow / avg_monthly_expense
        
        # Score: 0 months = 0, 6+ months = 100
        score = min(100, buffer_months * 16.67)
        
        return score
    
    def _calculate_debt_coverage(self, business_id: int) -> float:
        """Calculate debt coverage capacity (0-100)"""
        # For now, use expense ratio as proxy
        expense_ratio = self._calculate_expense_ratio(business_id)
        
        # Lower expense ratio = higher debt coverage capacity
        score = 100 - expense_ratio
        return max(0, score)
    
    def _calculate_inventory_health(self, business_id: int) -> float:
        """Calculate inventory health score (0-100)"""
        inventory_items = self.db.query(models.Inventory).filter(
            models.Inventory.business_id == business_id
        ).all()
        
        if not inventory_items:
            return 50  # No inventory = neutral score
        
        # Calculate percentage of items above reorder level
        healthy_items = sum(1 for item in inventory_items if item.quantity > item.reorder_level)
        health_percentage = (healthy_items / len(inventory_items)) * 100
        
        # Calculate inventory value
        total_value = sum(item.quantity * item.price_per_unit for item in inventory_items)
        
        # Combine metrics
        score = health_percentage * 0.7 + min(100, total_value / 100000) * 0.3
        
        return min(100, score)
    
    def _calculate_business_age_score(self, created_at: datetime) -> float:
        """Calculate business age score (0-100)"""
        age_days = (datetime.utcnow() - created_at).days
        age_months = age_days / 30
        
        # Score: <3 months = 25, 3-6 months = 50, 6-12 months = 75, 1-2 years = 90, 2+ years = 100
        if age_months < 3:
            return 25
        elif age_months < 6:
            return 50
        elif age_months < 12:
            return 75
        elif age_months < 24:
            return 90
        else:
            return 100
    
    def _calculate_transaction_volume_score(self, business_id: int) -> float:
        """Calculate transaction volume score (0-100)"""
        # Count transactions in last 12 months
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        tx_count = self.db.query(models.Transaction).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).count()
        
        # Score: 0-50 tx = 0-50, 50-200 tx = 50-100, 200+ tx = 100
        if tx_count < 50:
            return (tx_count / 50) * 50
        elif tx_count < 200:
            return 50 + ((tx_count - 50) / 150) * 50
        else:
            return 100
    
    def get_lender_risk_profile(self, business_id: int, credit_score: models.CreditScore):
        """Generate risk profile for lenders"""
        business = self.db.query(models.Business).filter(
            models.Business.id == business_id
        ).first()
        
        if not business:
            return None
        
        # Get user
        user = self.db.query(models.User).filter(
            models.User.id == business.owner_id
        ).first()
        
        # Determine risk level
        if credit_score.smartpesa_score >= 700:
            risk_level = "LOW"
        elif credit_score.smartpesa_score >= 500:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Calculate additional metrics for lenders
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)
        
        # Avg monthly revenue
        monthly_revenue = self.db.query(
            func.avg(models.Transaction.amount).label('avg_revenue')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.type == 'income',
            models.Transaction.created_at.between(start_date, end_date)
        ).first()[0] or 0
        
        # Revenue stability
        monthly_revenues = self.db.query(
            func.strftime('%Y-%m', models.Transaction.created_at).label('month'),
            func.sum(models.Transaction.amount).label('revenue')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.type == 'income',
            models.Transaction.created_at.between(start_date, end_date)
        ).group_by('month').all()
        
        if len(monthly_revenues) > 1:
            revenues = [r.revenue for r in monthly_revenues]
            mean_rev = np.mean(revenues)
            std_rev = np.std(revenues)
            revenue_stability = std_rev / mean_rev if mean_rev > 0 else 1
        else:
            revenue_stability = 1
        
        # Cash buffer in months
        avg_monthly_expense = self.db.query(
            func.avg(models.Transaction.amount).label('avg_expense')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.type == 'expense',
            models.Transaction.created_at.between(start_date, end_date)
        ).first()[0] or 1
        
        total_cash = self.db.query(
            func.sum(models.Transaction.amount).label('total_net')
        ).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).first()[0] or 0
        
        cash_buffer_months = total_cash / avg_monthly_expense if avg_monthly_expense > 0 else 0
        
        # Total inventory value
        inventory_value = self.db.query(
            func.sum(models.Inventory.quantity * models.Inventory.price_per_unit)
        ).filter(
            models.Inventory.business_id == business_id
        ).first()[0] or 0
        
        # Business age in months
        business_age_months = int((datetime.utcnow() - business.created_at).days / 30)
        
        # Transaction volume
        tx_count_12m = self.db.query(models.Transaction).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at.between(start_date, end_date)
        ).count()
        
        return {
            "business_id": business_id,
            "business_name": business.name,
            "owner_email": user.email if user else "unknown",
            "smartpesa_score": credit_score.smartpesa_score,
            "risk_level": risk_level,
            "calculation_date": credit_score.calculation_date,
            "valid_until": credit_score.valid_until,
            "avg_monthly_revenue": monthly_revenue,
            "revenue_stability": revenue_stability,
            "expense_ratio": credit_score.expense_ratio,
            "cash_buffer_months": cash_buffer_months,
            "inventory_value": inventory_value,
            "business_age_months": business_age_months,
            "transaction_volume_12m": tx_count_12m
        }
