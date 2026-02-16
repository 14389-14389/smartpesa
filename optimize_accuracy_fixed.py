import requests
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
from datetime import datetime, timedelta
import re
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

# Function to extract date from description
def extract_date_from_description(description):
    """Extract date from transaction description (e.g., 'Daily sales 2026-01-22')"""
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    match = re.search(date_pattern, description)
    if match:
        return match.group()
    return None

# Prepare daily data using dates from descriptions
print("\n🔄 Preparing daily aggregates using transaction dates...")
daily_data = {}

for t in transactions:
    # Try to get date from description first
    date_str = extract_date_from_description(t.get('description', ''))
    
    # If no date in description, use created_at
    if not date_str:
        date_str = t['created_at'][:10]
    
    if date_str not in daily_data:
        daily_data[date_str] = {'income': 0, 'expense': 0, 'count': 0}
    
    if t['type'] == 'income':
        daily_data[date_str]['income'] += t['amount']
    else:
        daily_data[date_str]['expense'] += t['amount']
    daily_data[date_str]['count'] += 1

# Create DataFrame
dates = []
net_cashflow = []
transaction_counts = []

for date_str, values in sorted(daily_data.items()):
    dates.append(date_str)
    net_cashflow.append(values['income'] - values['expense'])
    transaction_counts.append(values['count'])

df = pd.DataFrame({
    'date': pd.to_datetime(dates),
    'net': net_cashflow,
    'transaction_count': transaction_counts
})

print(f"📊 Daily data points: {len(df)} days")
print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"💰 Avg daily net: ${df['net'].mean():,.2f}")

if len(df) < 30:
    print(f"\n⚠️  WARNING: Only {len(df)} days of data. Need at least 30 days for meaningful forecasting.")
    print("Please generate more transaction data first.")
    exit()

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
    
    # Multiple lag features
    for lag in [1, 2, 3, 4, 5, 6, 7, 14, 21, 28, 30]:
        df[f'lag_{lag}'] = df['net'].shift(lag)
    
    # Rolling statistics with multiple windows
    for window in [3, 5, 7, 14, 21, 30]:
        df[f'rolling_mean_{window}'] = df['net'].rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['net'].rolling(window=window).std()
        df[f'rolling_min_{window}'] = df['net'].rolling(window=window).min()
        df[f'rolling_max_{window}'] = df['net'].rolling(window=window).max()
    
    # Exponential weighted features
    for span in [7, 14, 30]:
        df[f'ewm_mean_{span}'] = df['net'].ewm(span=span).mean()
    
    # Rate of change
    df['pct_change_1d'] = df['net'].pct_change() * 100
    df['pct_change_7d'] = df['net'].pct_change(periods=7) * 100
    
    # Volatility features
    df['volatility_7d'] = df['rolling_std_7'] / (df['rolling_mean_7'].abs() + 1)
    df['volatility_30d'] = df['rolling_std_30'] / (df['rolling_mean_30'].abs() + 1)
    
    # Day-of-week averages and deviations
    dow_avg = df.groupby('day_of_week')['net'].transform('mean')
    df['dow_deviation'] = df['net'] - dow_avg
    
    # Month averages and deviations
    month_avg = df.groupby('month')['net'].transform('mean')
    df['month_deviation'] = df['net'] - month_avg
    
    # Trend features
    df['trend'] = range(len(df))
    
    # Cyclical encoding
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
    
    return df

df_advanced = create_advanced_features(df)
print(f"✅ Created {len(df_advanced.columns)} features")
print(f"✅ Clean data points after dropping NA: {len(df_advanced.dropna())}")

# ============================================
# 2. MODEL TRAINING & EVALUATION
# ============================================
print("\n" + "=" * 70)
print("2️⃣ MODEL TRAINING & EVALUATION")
print("=" * 70)

# Prepare features and target
feature_cols = [col for col in df_advanced.columns if col not in ['date', 'net', 'transaction_count']]
df_clean = df_advanced.dropna()

if len(df_clean) < 30:
    print(f"\n⚠️  After dropping NA, only {len(df_clean)} days remain. Need more data.")
    exit()

X = df_clean[feature_cols].values
y = df_clean['net'].values

print(f"📊 Training samples: {len(X)}")
print(f"📊 Features: {len(feature_cols)}")

# Split data (80% train, 20% test)
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"📊 Train set: {len(X_train)} days")
print(f"📊 Test set: {len(X_test)} days")

# Train models
models = {
    'Random Forest': RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42
    )
}

results = {}
for name, model in models.items():
    print(f"\n📊 Training {name}...")
    
    # Train
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100
    
    results[name] = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'mape': mape
    }
    
    print(f"   • MAE: ±${mae:,.2f}")
    print(f"   • Error: ±{(mae / y_test.mean()) * 100:.1f}%")
    print(f"   • RMSE: ${rmse:,.2f}")
    print(f"   • R² Score: {r2:.4f}")
    
    # Feature importance
    if hasattr(model, 'feature_importances_'):
        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"   • Top Features:")
        for feat, imp in top_features:
            print(f"     - {feat}: {imp:.3f}")

# ============================================
# 3. SIMPLE ENSEMBLE
# ============================================
print("\n" + "=" * 70)
print("3️⃣ SIMPLE ENSEMBLE PREDICTION")
print("=" * 70)

# Simple average ensemble
ensemble_pred = np.zeros_like(y_test)
for model in models.values():
    ensemble_pred += model.predict(X_test)
ensemble_pred /= len(models)

ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
ensemble_r2 = r2_score(y_test, ensemble_pred)

print(f"\n🎯 Ensemble Model Performance:")
print(f"   • MAE: ±${ensemble_mae:,.2f}")
print(f"   • Error: ±{(ensemble_mae / y_test.mean()) * 100:.1f}%")
print(f"   • RMSE: ${ensemble_rmse:,.2f}")
print(f"   • R² Score: {ensemble_r2:.4f}")

# ============================================
# 4. ACCURACY ASSESSMENT
# ============================================
print("\n" + "=" * 70)
print("4️⃣ ACCURACY ASSESSMENT")
print("=" * 70)

best_model = min(results.items(), key=lambda x: x[1]['mae'])
print(f"\n🏆 Best Individual Model: {best_model[0]}")
print(f"   • MAE: ±${best_model[1]['mae']:,.2f}")
print(f"   • Error: ±{(best_model[1]['mae'] / y_test.mean()) * 100:.1f}%")

print(f"\n🎯 Ensemble Model:")
print(f"   • MAE: ±${ensemble_mae:,.2f}")
print(f"   • Error: ±{(ensemble_mae / y_test.mean()) * 100:.1f}%")

# Calculate theoretical accuracy
accuracy = 100 - ((ensemble_mae / y_test.mean()) * 100)
print(f"\n📈 Theoretical Accuracy: {accuracy:.1f}%")

# Compare with your current model
print(f"\n📊 Comparison with Current Hybrid Model:")
print(f"   • Current Hybrid MAE: $6,342")
print(f"   • New Ensemble MAE: ${ensemble_mae:,.2f}")
improvement = ((6342 - ensemble_mae) / 6342) * 100
print(f"   • Improvement: {improvement:.1f}%")

if accuracy < 90:
    print("\n⚠️  Financial forecasting has inherent uncertainty:")
    print("   • Random events (supply chain issues, customer emergencies)")
    print("   • Market changes (competitor actions, economic shifts)")
    print("   • Seasonal variations")
    print("   • Human behavior patterns")
    
    print("\n💡 To improve accuracy further:")
    print("   1. Add 5+ years of historical data")
    print("   2. Include external factors:")
    print("      - Weather data")
    print("      - Holiday calendar")
    print("      - Economic indicators (inflation, interest rates)")
    print("   3. Add business-specific features:")
    print("      - Marketing campaigns")
    print("      - New product launches")
    print("      - Customer seasonality")
    print("   4. Use deep learning (LSTM/Transformer models)")
    print("   5. Implement daily model retraining")

print("\n" + "=" * 70)
print("✅ OPTIMIZATION COMPLETE")
print("=" * 70)
