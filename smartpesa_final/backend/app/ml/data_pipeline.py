import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models
import re

class DataPipeline:
    def __init__(self, db: Session):
        self.db = db
    
    def extract_date_from_description(self, description):
        """Extract date from transaction description"""
        # Look for YYYY-MM-DD pattern in description
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(date_pattern, description)
        if match:
            return datetime.strptime(match.group(), '%Y-%m-%d').date()
        return None
    
    def fetch_transactions(self, business_id: int, days: int = 365):
        """Fetch transactions for a business"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        transactions = self.db.query(models.Transaction).filter(
            models.Transaction.business_id == business_id,
            models.Transaction.created_at >= cutoff_date
        ).order_by(models.Transaction.created_at).all()
        
        return transactions
    
    def prepare_daily_data(self, business_id: int, days: int = 365):
        """Convert transactions to daily aggregated data using actual transaction dates"""
        transactions = self.fetch_transactions(business_id, days)
        
        if not transactions:
            return pd.DataFrame()
        
        # Convert to DataFrame with extracted dates
        data = []
        for t in transactions:
            # Try to extract date from description
            transaction_date = self.extract_date_from_description(t.description)
            
            # If no date in description, use created_at date
            if not transaction_date:
                transaction_date = t.created_at.date()
            
            data.append({
                'date': transaction_date,
                'amount': t.amount,
                'type': t.type,
                'category': t.category,
                'created_at': t.created_at.date()  # Keep original for reference
            })
        
        df = pd.DataFrame(data)
        
        # Pivot to get daily income and expense
        daily = df.pivot_table(
            index='date',
            columns='type',
            values='amount',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Ensure columns exist
        if 'income' not in daily.columns:
            daily['income'] = 0
        if 'expense' not in daily.columns:
            daily['expense'] = 0
        
        # Calculate net cash flow
        daily['net'] = daily['income'] - daily['expense']
        daily['date'] = pd.to_datetime(daily['date'])
        
        return daily.sort_values('date')
    
    def engineer_features(self, df: pd.DataFrame):
        """Add feature engineering for ML models"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_month'] = df['date'].dt.day
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        
        # Lag features (previous days)
        for lag in [1, 2, 3, 7, 14, 30]:
            df[f'net_lag_{lag}'] = df['net'].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'net_rolling_mean_{window}'] = df['net'].rolling(window=window).mean()
            df[f'net_rolling_std_{window}'] = df['net'].rolling(window=window).std()
            df[f'income_rolling_mean_{window}'] = df['income'].rolling(window=window).mean()
            df[f'expense_rolling_mean_{window}'] = df['expense'].rolling(window=window).mean()
        
        # Revenue volatility (7-day standard deviation / mean)
        df['volatility_7d'] = df['net'].rolling(7).std() / (df['net'].rolling(7).mean().abs() + 1)
        
        # Day of week averages
        dow_avg = df.groupby('day_of_week')['net'].transform('mean')
        df['dow_avg_deviation'] = df['net'] - dow_avg
        
        # Month averages
        month_avg = df.groupby('month')['net'].transform('mean')
        df['month_avg_deviation'] = df['net'] - month_avg
        
        # Weekend indicator
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Month start/end indicators
        df['is_month_start'] = (df['date'].dt.is_month_start).astype(int)
        df['is_month_end'] = (df['date'].dt.is_month_end).astype(int)
        
        # Holiday indicator (simplified - you can expand this)
        df['is_holiday'] = 0
        
        return df.dropna()
