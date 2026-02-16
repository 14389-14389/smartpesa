import requests
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1

print("=" * 70)
print("🔬 ADVANCED MODEL OPTIMIZATION FOR MAXIMUM ACCURACY")
print("=" * 70)

# Login
response = requests.post(f"{BASE_URL}/users/login", json={
    "email": EMAIL,
    "password": PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get all transactions
print("\n📥 Fetching transaction data...")
transactions = requests.get(
    f"{BASE_URL}/transactions/?business_id={BUSINESS_ID}&limit=5000",
    headers=headers
).json()

print(f"✅ Loaded {len(transactions)} transactions")

# Prepare daily data
print("\n🔄 Preparing daily aggregates...")
daily_data = {}
for t in transactions:
    date = t['created_at'][:10]
    if date not in daily_data:
        daily_data[date] = {'income': 0, 'expense': 0}
    if t['type'] == 'income':
        daily_data[date]['income'] += t['amount']
    else:
        daily_data[date]['expense'] += t['amount']

# Create DataFrame
dates = []
net_cashflow = []
for date, values in sorted(daily_data.items()):
    dates.append(date)
    net_cashflow.append(values['income'] - values['expense'])

df = pd.DataFrame({
    'date': pd.to_datetime(dates),
    'net': net_cashflow
})

print(f"📊 Daily data points: {len(df)} days")

# ============================================
# 1. ADVANCED FEATURE ENGINEERING
# ============================================
print("\n" + "=" * 70)
print("1️⃣ ADVANCED FEATURE ENGINEERING")
print("=" * 70)

def create_advanced_features(df):
    df = df.copy()
    
    # Time features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
    df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
    df['is_year_start'] = df['date'].dt.is_year_start.astype(int)
    df['is_year_end'] = df['date'].dt.is_year_end.astype(int)
    
    # Multiple lag features
    for lag in [1, 2, 3, 4, 5, 6, 7, 14, 21, 28, 30, 60, 90]:
        df[f'lag_{lag}'] = df['net'].shift(lag)
    
    # Rolling statistics with multiple windows
    for window in [3, 5, 7, 14, 21, 30, 60, 90]:
        df[f'rolling_mean_{window}'] = df['net'].rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['net'].rolling(window=window).std()
        df[f'rolling_min_{window}'] = df['net'].rolling(window=window).min()
        df[f'rolling_max_{window}'] = df['net'].rolling(window=window).max()
        df[f'rolling_skew_{window}'] = df['net'].rolling(window=window).skew()
        df[f'rolling_kurt_{window}'] = df['net'].rolling(window=window).kurt()
    
    # Exponential weighted features
    for span in [7, 14, 30]:
        df[f'ewm_mean_{span}'] = df['net'].ewm(span=span).mean()
        df[f'ewm_std_{span}'] = df['net'].ewm(span=span).std()
    
    # Rate of change
    df['pct_change_1d'] = df['net'].pct_change() * 100
    df['pct_change_7d'] = df['net'].pct_change(periods=7) * 100
    df['pct_change_30d'] = df['net'].pct_change(periods=30) * 100
    
    # Volatility features
    df['volatility_7d'] = df['rolling_std_7'] / (df['rolling_mean_7'].abs() + 1)
    df['volatility_30d'] = df['rolling_std_30'] / (df['rolling_mean_30'].abs() + 1)
    
    # Range features
    df['range_7d'] = df['rolling_max_7'] - df['rolling_min_7']
    df['range_30d'] = df['rolling_max_30'] - df['rolling_min_30']
    
    # Day-of-week averages and deviations
    dow_avg = df.groupby('day_of_week')['net'].transform('mean')
    df['dow_avg'] = dow_avg
    df['dow_deviation'] = df['net'] - dow_avg
    
    # Month averages and deviations
    month_avg = df.groupby('month')['net'].transform('mean')
    df['month_avg'] = month_avg
    df['month_deviation'] = df['net'] - month_avg
    
    # Trend features
    df['trend'] = range(len(df))
    df['trend_squared'] = df['trend'] ** 2
    
    # Cyclical encoding
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
    
    return df

df_advanced = create_advanced_features(df)
print(f"✅ Created {len(df_advanced.columns)} features")

# ============================================
# 2. MULTIPLE MODEL COMPARISON
# ============================================
print("\n" + "=" * 70)
print("2️⃣ MODEL COMPARISON & SELECTION")
print("=" * 70)

# Prepare features and target
feature_cols = [col for col in df_advanced.columns if col not in ['date', 'net']]
df_clean = df_advanced.dropna()

X = df_clean[feature_cols].values
y = df_clean['net'].values

# Time series cross-validation
tscv = TimeSeriesSplit(n_splits=5)

models = {
    'Random Forest': RandomForestRegressor(
        n_estimators=300,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.01,
        subsample=0.8,
        random_state=42
    ),
    'XGBoost': None  # Would need to install xgboost
}

results = {}
for name, model in models.items():
    if model is None:
        continue
    
    # Cross-validation scores
    cv_scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_absolute_error')
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()
    
    # Train on full data
    model.fit(X, y)
    
    # Feature importance
    if hasattr(model, 'feature_importances_'):
        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
    else:
        top_features = []
    
    results[name] = {
        'cv_mae': cv_mae,
        'cv_std': cv_std,
        'cv_mae_pct': (cv_mae / y.mean()) * 100,
        'top_features': top_features
    }
    
    print(f"\n📊 {name}:")
    print(f"   • CV MAE: ±${cv_mae:,.2f}")
    print(f"   • Error Range: ±{cv_mae / y.mean() * 100:.1f}%")
    print(f"   • Stability: ±${cv_std:,.2f}")
    if top_features:
        print(f"   • Top Features:")
        for feat, imp in top_features[:5]:
            print(f"     - {feat}: {imp:.3f}")

# ============================================
# 3. ENSEMBLE METHODS
# ============================================
print("\n" + "=" * 70)
print("3️⃣ ENSEMBLE METHODS FOR MAXIMUM ACCURACY")
print("=" * 70)

# Create ensemble predictions
class EnsembleModel:
    def __init__(self, models):
        self.models = models
        self.weights = None
    
    def fit(self, X, y):
        # Train all models
        for model in self.models:
            model.fit(X, y)
        
        # Optimize weights using validation
        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        predictions = []
        for model in self.models:
            model.fit(X_train, y_train)
            pred = model.predict(X_val)
            predictions.append(pred)
        
        # Find optimal weights
        from scipy.optimize import minimize
        
        def objective(weights):
            weights = weights / weights.sum()
            ensemble_pred = np.zeros_like(predictions[0])
            for w, pred in zip(weights, predictions):
                ensemble_pred += w * pred
            return mean_absolute_error(y_val, ensemble_pred)
        
        # Optimize
        n_models = len(self.models)
        result = minimize(
            objective,
            x0=np.ones(n_models) / n_models,
            bounds=[(0, 1)] * n_models,
            constraints={'type': 'eq', 'fun': lambda w: 1 - w.sum()}
        )
        
        self.weights = result.x / result.x.sum()
        return self
    
    def predict(self, X):
        predictions = []
        for w, model in zip(self.weights, self.models):
            predictions.append(w * model.predict(X))
        return np.sum(predictions, axis=0)

# Create ensemble
ensemble = EnsembleModel([
    RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
    GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)
])

# Evaluate ensemble
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

ensemble.fit(X_train, y_train)
ensemble_pred = ensemble.predict(X_test)

ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
ensemble_r2 = r2_score(y_test, ensemble_pred)

print(f"\n🎯 Ensemble Model Performance:")
print(f"   • MAE: ±${ensemble_mae:,.2f}")
print(f"   • Error Range: ±{(ensemble_mae / y_test.mean()) * 100:.1f}%")
print(f"   • RMSE: ${ensemble_rmse:,.2f}")
print(f"   • R² Score: {ensemble_r2:.4f}")
print(f"   • Model Weights: {ensemble.weights}")

# ============================================
# 4. FINAL ACCURACY ASSESSMENT
# ============================================
print("\n" + "=" * 70)
print("4️⃣ FINAL ACCURACY ASSESSMENT")
print("=" * 70)

best_mae = min([results[m]['cv_mae'] for m in results])
best_model = [m for m in results if results[m]['cv_mae'] == best_mae][0]

print(f"\n🏆 Best Individual Model: {best_model}")
print(f"   • MAE: ±${best_mae:,.2f}")
print(f"   • Error: ±{(best_mae / y.mean()) * 100:.1f}%")

print(f"\n🎯 Ensemble Model:")
print(f"   • MAE: ±${ensemble_mae:,.2f}")
print(f"   • Error: ±{(ensemble_mae / y_test.mean()) * 100:.1f}%")

# Calculate theoretical maximum accuracy
theoretical_max = 100 - ((ensemble_mae / y_test.mean()) * 100)
print(f"\n📈 Theoretical Accuracy: {theoretical_max:.1f}%")

if theoretical_max < 90:
    print("\n⚠️  Note: Financial forecasting has inherent uncertainty")
    print("   • Random events can't be predicted")
    print("   • Market conditions change")
    print("   • Human behavior is variable")
    print("\n💡 To get closer to 99% you would need:")
    print("   • 10+ years of daily data")
    print("   • External factors (weather, holidays, events)")
    print("   • Real-time market data")
    print("   • Competitor information")
    print("   • Customer behavior data")

# ============================================
# 5. ACCURACY IMPROVEMENT RECOMMENDATIONS
# ============================================
print("\n" + "=" * 70)
print("5️⃣ RECOMMENDATIONS FOR HIGHER ACCURACY")
print("=" * 70)

print("\n📋 To improve accuracy further:")
print("   1. Add more historical data (5-10 years minimum)")
print("   2. Include external features:")
print("      - Weather data")
print("      - Holiday calendar")
print("      - Economic indicators")
print("      - Industry trends")
print("   3. Use deep learning (LSTM networks)")
print("   4. Add real-time data feeds")
print("   5. Implement online learning (update model daily)")
print("   6. Add customer/client specific features")
print("   7. Include marketing campaign data")
print("   8. Add competitor pricing information")
