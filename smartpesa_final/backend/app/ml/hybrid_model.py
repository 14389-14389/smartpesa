import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class HybridModel:
    def __init__(self):
        self.prophet_model = None
        self.rf_model = None
        self.metrics = {}
        self.feature_importance = None
    
    def train_prophet(self, df: pd.DataFrame, date_col='date', target_col='net'):
        """Train Prophet model and get residuals"""
        # Prepare data for Prophet
        prophet_df = df[[date_col, target_col]].rename(
            columns={date_col: 'ds', target_col: 'y'}
        )
        
        # Train Prophet
        self.prophet_model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        self.prophet_model.add_country_holidays(country_name='KE')
        self.prophet_model.fit(prophet_df)
        
        # Get predictions and calculate residuals
        forecast = self.prophet_model.predict(prophet_df[['ds']])
        residuals = prophet_df['y'].values - forecast['yhat'].values
        
        return residuals, forecast
    
    def train_rf(self, df: pd.DataFrame, residuals, feature_cols):
        """Train Random Forest on residuals"""
        # Prepare features
        X = df[feature_cols].values
        y = residuals
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.rf_model.fit(X_train, y_train)
        
        # Feature importance
        self.feature_importance = dict(zip(feature_cols, self.rf_model.feature_importances_))
        
        # Evaluate
        y_pred = self.rf_model.predict(X_test)
        rf_metrics = {
            'rf_mae': float(mean_absolute_error(y_test, y_pred)),
            'rf_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
        }
        
        return rf_metrics
    
    def train(self, df: pd.DataFrame, feature_cols):
        """Complete hybrid training"""
        # Train Prophet and get residuals
        residuals, prophet_forecast = self.train_prophet(df)
        
        # Train Random Forest on residuals
        rf_metrics = self.train_rf(df, residuals, feature_cols)
        
        # Calculate overall metrics
        prophet_pred = prophet_forecast['yhat'].values[-len(df):]
        rf_pred = self.rf_model.predict(df[feature_cols].values)
        hybrid_pred = prophet_pred + rf_pred
        
        y_true = df['net'].values[-len(hybrid_pred):]
        
        self.metrics = {
            'hybrid_mae': float(mean_absolute_error(y_true, hybrid_pred)),
            'hybrid_rmse': float(np.sqrt(mean_squared_error(y_true, hybrid_pred))),
            'hybrid_mape': float(np.mean(np.abs((y_true - hybrid_pred) / (y_true + 1e-10))) * 100),
            **rf_metrics
        }
        
        return self.metrics
    
    def predict(self, future_df: pd.DataFrame, feature_cols):
        """Generate hybrid predictions"""
        if not self.prophet_model or not self.rf_model:
            raise ValueError("Models not trained yet")
        
        # Prophet predictions
        prophet_pred = self.prophet_model.predict(future_df[['ds']])
        
        # Random Forest predictions for residuals
        rf_pred = self.rf_model.predict(future_df[feature_cols].values)
        
        # Combine predictions
        hybrid_pred = prophet_pred['yhat'].values + rf_pred
        
        # Convert dates to string format for JSON serialization
        dates = []
        for d in future_df['ds'].values:
            if isinstance(d, (np.datetime64, pd.Timestamp)):
                dates.append(pd.Timestamp(d).isoformat())
            else:
                dates.append(str(d))
        
        return {
            'dates': dates,
            'prophet_prediction': [float(x) for x in prophet_pred['yhat'].values],
            'rf_correction': [float(x) for x in rf_pred],
            'hybrid_prediction': [float(x) for x in hybrid_pred],
            'lower_bound': [float(x) for x in (prophet_pred['yhat_lower'].values + rf_pred)],
            'upper_bound': [float(x) for x in (prophet_pred['yhat_upper'].values + rf_pred)]
        }
