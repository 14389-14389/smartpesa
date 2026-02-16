import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzcxMjM2OTU2fQ.QTQMUVY7_X_svxw2qJ-Icvogk4Cz80w5zIJplPqRwiw"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
BUSINESS_ID = 1

print("=" * 60)
print("📊 MODEL ACCURACY TEST")
print("=" * 60)

# Get forecast
print("\n🔮 Fetching 30-day forecast...")
response = requests.get(f"{BASE_URL}/forecast/{BUSINESS_ID}/30days", headers=HEADERS)
forecast = response.json()

if 'error' in forecast:
    print(f"❌ Error: {forecast['error']}")
    exit()

# Display metrics
print("\n📈 MODEL PERFORMANCE METRICS")
print("-" * 40)

print("\n🔵 Baseline Prophet Model:")
print(f"   • MAE:  ±${forecast['baseline_model']['metrics']['mae']:,.2f}")
print(f"   • RMSE:  ${forecast['baseline_model']['metrics']['rmse']:,.2f}")
print(f"   • MAPE:  {forecast['baseline_model']['metrics']['mape']:.1f}%")

print("\n🟢 Hybrid Model (Prophet + Random Forest):")
print(f"   • MAE:  ±${forecast['hybrid_model']['metrics']['hybrid_mae']:,.2f}")
print(f"   • RMSE:  ${forecast['hybrid_model']['metrics']['hybrid_rmse']:,.2f}")
print(f"   • MAPE:  {forecast['hybrid_model']['metrics']['hybrid_mape']:.1f}%")

# Calculate improvement
baseline_mae = forecast['baseline_model']['metrics']['mae']
hybrid_mae = forecast['hybrid_model']['metrics']['hybrid_mae']
improvement = ((baseline_mae - hybrid_mae) / baseline_mae) * 100

print(f"\n📈 Improvement: {improvement:.1f}% better than baseline")

# Feature importance
print("\n🎯 Top 5 Important Features:")
features = forecast['hybrid_model']['feature_importance']
sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:5]
for i, (feat, imp) in enumerate(sorted_features, 1):
    print(f"   {i}. {feat}: {imp:.3f}")

# Risk analysis
print("\n⚠️  Risk Assessment:")
risk = forecast['risk_analysis']
print(f"   • Risk Score: {risk['risk_score']}/100")
print(f"   • Negative Days: {risk['negative_days_forecast']}")
print(f"   • Volatility: ±${risk['forecast_volatility']:,.2f}")

# Data summary
print("\n📊 Data Summary:")
print(f"   • Days of History: {forecast['data_summary']['total_days']}")
print(f"   • Avg Daily Net: ${forecast['data_summary']['avg_daily_net']:,.2f}")
print(f"   • Total Income: ${forecast['data_summary']['total_income']:,.2f}")
print(f"   • Total Expenses: ${forecast['data_summary']['total_expense']:,.2f}")

print("\n" + "=" * 60)
