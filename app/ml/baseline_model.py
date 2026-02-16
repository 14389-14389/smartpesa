import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class BaselineModel:
    def __init__(self):
        self.model = None
        self.metrics = {}
    
    def train(self, df: pd.DataFrame, date_col='date', target_col='net'):
        """Train Prophet model"""
        # Prepare data for Prophet
        prophet_df = df[[date_col, target_col]].rename(
            columns={date_col: 'ds', target_col: 'y'}
        )
        
        # Create and train model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05
        )
        
        # Add custom seasonalities
        self.model.add_country_holidays(country_name='KE')  # Kenya holidays
        
        self.model.fit(prophet_df)
        
        return self.model
    
    def predict(self, periods: int = 30, freq: str = 'D'):
        """Generate predictions"""
        if not self.model:
            raise ValueError("Model not trained yet")
        
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)
        
        # Return with datetime objects (not strings)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def evaluate(self, df: pd.DataFrame, target_col='net'):
        """Calculate evaluation metrics"""
        # Get predictions for historical data
        forecast = self.predict(periods=0)
        
        # Ensure both dataframes have datetime types
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        forecast['ds'] = pd.to_datetime(forecast['ds'])
        
        # Merge on date
        eval_df = pd.merge(
            df_copy[['date', target_col]],
            forecast[['ds', 'yhat']],
            left_on='date',
            right_on='ds',
            how='inner'
        )
        
        # Calculate metrics
        y_true = eval_df[target_col].values
        y_pred = eval_df['yhat'].values
        
        self.metrics = {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mape': float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100)
        }
        
        return self.metrics
    
    def get_components(self, forecast):
        """Get forecast components (trend, seasonality)"""
        if not self.model:
            raise ValueError("Model not trained yet")
        
        return self.model.plot_components(forecast)
