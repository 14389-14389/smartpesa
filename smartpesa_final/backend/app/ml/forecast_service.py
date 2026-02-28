import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.ml.data_pipeline import DataPipeline
from app.ml.baseline_model import BaselineModel
from app.ml.hybrid_model import HybridModel

class ForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = DataPipeline(db)
        self.baseline = BaselineModel()
        self.hybrid = HybridModel()
    
    def prepare_data_for_forecast(self, business_id: int, days_history: int = 365):
        """Prepare data for forecasting"""
        # Get daily aggregated data
        daily_data = self.pipeline.prepare_daily_data(business_id, days_history)
        
        if daily_data.empty:
            return None
        
        # Engineer features
        featured_data = self.pipeline.engineer_features(daily_data)
        
        return featured_data
    
    def generate_forecast(self, business_id: int, days_forward: int = 30):
        """Generate forecast for a business"""
        # Prepare data
        data = self.prepare_data_for_forecast(business_id)
        
        if data is None or len(data) < 30:
            return {
                'error': 'Insufficient data for forecasting. Need at least 30 days of data.'
            }
        
        # Define feature columns for hybrid model
        feature_cols = [
            'day_of_week', 'month', 'quarter', 'week_of_year',
            'net_lag_1', 'net_lag_2', 'net_lag_3', 'net_lag_7',
            'net_rolling_mean_7', 'net_rolling_std_7',
            'volatility_7d', 'is_weekend', 'is_month_start', 'is_month_end'
        ]
        
        # Filter to available columns
        available_features = [col for col in feature_cols if col in data.columns]
        
        # Train baseline model
        print("Training baseline Prophet model...")
        self.baseline.train(data)
        baseline_metrics = self.baseline.evaluate(data)
        
        # Train hybrid model
        print("Training hybrid Prophet+RF model...")
        hybrid_metrics = self.hybrid.train(data, available_features)
        
        # Generate future dates
        last_date = data['date'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_forward,
            freq='D'
        )
        
        # Create future dataframe with features
        future_df = pd.DataFrame({'ds': future_dates})
        
        # Add basic features for future dates
        future_df['day_of_week'] = future_df['ds'].dt.dayofweek
        future_df['month'] = future_df['ds'].dt.month
        future_df['quarter'] = future_df['ds'].dt.quarter
        future_df['week_of_year'] = future_df['ds'].dt.isocalendar().week.astype(int)
        future_df['is_weekend'] = future_df['day_of_week'].isin([5, 6]).astype(int)
        future_df['is_month_start'] = (future_df['ds'].dt.is_month_start).astype(int)
        future_df['is_month_end'] = (future_df['ds'].dt.is_month_end).astype(int)
        
        # For lag features, use last known values from data
        for lag in [1, 2, 3, 7]:
            future_df[f'net_lag_{lag}'] = data['net'].iloc[-lag] if len(data) >= lag else 0
        
        # For rolling features, use recent averages
        future_df['net_rolling_mean_7'] = data['net'].tail(7).mean()
        future_df['net_rolling_std_7'] = data['net'].tail(7).std()
        future_df['volatility_7d'] = future_df['net_rolling_std_7'] / (future_df['net_rolling_mean_7'].abs() + 1)
        
        # Generate predictions
        baseline_forecast = self.baseline.predict(periods=days_forward)
        hybrid_forecast = self.hybrid.predict(future_df, available_features)
        
        # Convert dates to string for JSON serialization
        def date_to_str(d):
            if isinstance(d, (np.datetime64, pd.Timestamp)):
                return pd.Timestamp(d).strftime('%Y-%m-%d')
            return str(d)
        
        return {
            'business_id': business_id,
            'forecast_date': datetime.utcnow().isoformat(),
            'days_forward': days_forward,
            'data_summary': {
                'total_days': len(data),
                'date_range': {
                    'start': date_to_str(data['date'].min()),
                    'end': date_to_str(data['date'].max())
                },
                'total_income': float(data['income'].sum()),
                'total_expense': float(data['expense'].sum()),
                'avg_daily_net': float(data['net'].mean())
            },
            'baseline_model': {
                'metrics': baseline_metrics,
                'forecast': [
                    {
                        'ds': date_to_str(row['ds']),
                        'yhat': float(row['yhat']),
                        'yhat_lower': float(row['yhat_lower']),
                        'yhat_upper': float(row['yhat_upper'])
                    }
                    for row in baseline_forecast.to_dict('records')
                ]
            },
            'hybrid_model': {
                'metrics': hybrid_metrics,
                'feature_importance': self.hybrid.feature_importance,
                'forecast': [
                    {
                        'date': hybrid_forecast['dates'][i],
                        'prophet_prediction': hybrid_forecast['prophet_prediction'][i],
                        'rf_correction': hybrid_forecast['rf_correction'][i],
                        'hybrid_prediction': hybrid_forecast['hybrid_prediction'][i],
                        'lower_bound': hybrid_forecast['lower_bound'][i],
                        'upper_bound': hybrid_forecast['upper_bound'][i]
                    }
                    for i in range(len(hybrid_forecast['dates']))
                ]
            },
            'risk_analysis': self.analyze_risk(hybrid_forecast, data)
        }
    
    def analyze_risk(self, forecast, historical_data):
        """Analyze risk based on forecast"""
        predictions = forecast['hybrid_prediction']
        
        # Calculate risk metrics
        negative_days = sum(1 for p in predictions if p < 0)
        volatility = float(np.std(predictions))
        avg_prediction = float(np.mean(predictions))
        
        # Compare with historical
        historical_avg = float(historical_data['net'].mean())
        historical_std = float(historical_data['net'].std())
        
        # Generate alerts
        alerts = []
        
        if negative_days > len(predictions) * 0.3:
            alerts.append({
                'level': 'HIGH',
                'message': f'High risk: {negative_days} out of {len(predictions)} forecast days show negative cash flow'
            })
        elif negative_days > 0:
            alerts.append({
                'level': 'MEDIUM',
                'message': f'Warning: {negative_days} forecast days show negative cash flow'
            })
        
        if avg_prediction < historical_avg * 0.7:
            alerts.append({
                'level': 'HIGH',
                'message': f'Forecast shows significant decline: {avg_prediction:.2f} vs historical {historical_avg:.2f}'
            })
        
        if volatility > historical_std * 1.5:
            alerts.append({
                'level': 'MEDIUM',
                'message': f'High volatility detected: {volatility:.2f} vs historical {historical_std:.2f}'
            })
        
        return {
            'risk_score': min(100, int((volatility / (historical_std + 1)) * 50 + (negative_days / len(predictions)) * 50)),
            'negative_days_forecast': negative_days,
            'forecast_volatility': volatility,
            'historical_volatility': historical_std,
            'alerts': alerts
        }
    
    def get_risk_alert(self, business_id: int):
        """Generate risk alert based on forecast"""
        forecast = self.generate_forecast(business_id, days_forward=30)
        
        if 'error' in forecast:
            return forecast
        
        return {
            'business_id': business_id,
            'timestamp': datetime.utcnow().isoformat(),
            'risk_level': self.get_risk_level(forecast['risk_analysis']['risk_score']),
            'risk_score': forecast['risk_analysis']['risk_score'],
            'alerts': forecast['risk_analysis']['alerts'],
            'summary': {
                'forecast_avg': float(np.mean([f['hybrid_prediction'] for f in forecast['hybrid_model']['forecast']])),
                'negative_days': forecast['risk_analysis']['negative_days_forecast'],
                'volatility': forecast['risk_analysis']['forecast_volatility']
            }
        }
    
    def get_risk_level(self, score):
        """Convert risk score to level"""
        if score >= 70:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
