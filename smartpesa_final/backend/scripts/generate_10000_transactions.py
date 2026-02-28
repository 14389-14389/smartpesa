import requests
import random
from datetime import datetime, timedelta
import time
import numpy as np
from tqdm import tqdm  # For progress bar

# Install tqdm if not already installed
try:
    from tqdm import tqdm
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'tqdm'])
    from tqdm import tqdm

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1
TARGET_TRANSACTIONS = 10000

# Login to get token
print("🔐 Logging in...")
response = requests.post(f"{BASE_URL}/users/login", json={
    "email": EMAIL,
    "password": PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# First, delete existing transactions to avoid duplicates
print("🧹 Cleaning up old transactions...")
transactions = requests.get(f"{BASE_URL}/transactions/?business_id={BUSINESS_ID}&limit=1000", 
                           headers=headers).json()
if transactions:
    for t in tqdm(transactions, desc="Deleting old transactions"):
        requests.delete(f"{BASE_URL}/transactions/{t['id']}", headers=headers)
        time.sleep(0.01)  # Small delay to avoid overwhelming
print(f"✅ Deleted {len(transactions)} old transactions")

# Generate 5 years of historical data (2021-2026)
print(f"\n📊 Generating {TARGET_TRANSACTIONS} transactions (2021-2026)...")

end_date = datetime.now() - timedelta(days=1)  # Yesterday
start_date = datetime(2021, 1, 1)  # Start from Jan 2021

current_date = start_date
transaction_count = 0

# Business patterns
income_categories = ['Sales', 'Consulting', 'Product Revenue', 'Service Fees', 
                     'Interest Income', 'Online Sales', 'Wholesale', 'Retail']
expense_categories = ['Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies', 
                      'Insurance', 'Maintenance', 'Travel', 'Software', 'Training',
                      'Taxes', 'Equipment', 'Transport', 'Advertising']

# Seasonal patterns
monthly_multipliers = {
    1: 0.85,   # January - post-holiday slow
    2: 0.90,   # February
    3: 1.0,    # March
    4: 1.05,   # April
    5: 1.10,   # May
    6: 1.15,   # June
    7: 1.20,   # July - peak summer
    8: 1.15,   # August
    9: 1.10,   # September
    10: 1.0,   # October
    11: 0.95,  # November
    12: 1.30   # December - holiday season
}

# Growth trend (business growing over time)
def get_growth_factor(date):
    days_from_start = (date - start_date).days
    years_from_start = days_from_start / 365
    # Exponential growth: 20% annual growth
    return 1 + (years_from_start * 0.2) + (years_from_start ** 2 * 0.02)

# Add some random events (economic shocks, etc.)
def get_event_multiplier(date):
    # COVID impact in 2020-2021
    if date.year == 2021 and date.month <= 6:
        return random.uniform(0.6, 0.8)
    # Recovery in late 2021
    elif date.year == 2021 and date.month > 6:
        return random.uniform(0.9, 1.1)
    # Normal years
    else:
        return 1.0

print("🔄 Generating transactions with progress bar:")
with tqdm(total=TARGET_TRANSACTIONS, desc="Transactions created") as pbar:
    while transaction_count < TARGET_TRANSACTIONS and current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Get multipliers
        season_factor = monthly_multipliers.get(current_date.month, 1.0)
        growth_factor = get_growth_factor(current_date)
        event_factor = get_event_multiplier(current_date)
        
        # Base income for the day
        base_daily_income = 5000 * season_factor * growth_factor * event_factor
        
        # Day of week patterns
        is_weekend = current_date.weekday() >= 5
        is_monday = current_date.weekday() == 0
        is_friday = current_date.weekday() == 4
        
        # More transactions on busy days
        if is_weekend:
            transactions_today = random.randint(1, 3)
            weekend_factor = 0.6
        elif is_friday:
            transactions_today = random.randint(3, 6)
            weekend_factor = 1.2
        elif is_monday:
            transactions_today = random.randint(2, 4)
            weekend_factor = 0.9
        else:
            transactions_today = random.randint(2, 5)
            weekend_factor = 1.0
        
        # Generate multiple transactions per day
        for i in range(transactions_today):
            if transaction_count >= TARGET_TRANSACTIONS:
                break
            
            # Decide if income or expense (70% income, 30% expense)
            is_income = random.random() < 0.7
            
            if is_income:
                amount = round(base_daily_income * random.uniform(0.3, 1.8) * weekend_factor, 2)
                category = random.choice(income_categories)
                transaction_type = "income"
            else:
                amount = round(base_daily_income * random.uniform(0.1, 0.4), 2)
                category = random.choice(expense_categories)
                transaction_type = "expense"
            
            # Add some variance based on category
            if category in ['Rent', 'Insurance']:
                amount = round(amount * 2, 2)  # Larger fixed expenses
            elif category in ['Salaries']:
                amount = round(amount * 3, 2)  # Biggest expense
            
            # Create transaction
            response = requests.post(f"{BASE_URL}/transactions/", 
                          json={
                              "amount": amount,
                              "type": transaction_type,
                              "category": category,
                              "description": f"{category} - {date_str} ({i+1}/{transactions_today})",
                              "business_id": BUSINESS_ID
                          }, headers=headers)
            
            if response.status_code == 200:
                transaction_count += 1
                pbar.update(1)
            
            # Small delay to avoid rate limiting
            time.sleep(0.02)
        
        current_date += timedelta(days=1)
        
        # Progress update every 100 days
        if current_date.day == 1 and current_date.month == 1:
            print(f"\n📅 Entering year {current_date.year}...")

print(f"\n✅ Successfully created {transaction_count} transactions!")

# Verify the data
print("\n📈 Verifying data...")
summary = requests.get(f"{BASE_URL}/transactions/summary/overview?business_id={BUSINESS_ID}&days=2000", 
                      headers=headers).json()
print(f"📊 Transaction Summary:")
print(f"   • Total transactions: {summary.get('transaction_count', 0)}")
print(f"   • Total Income: ${summary.get('total_income', 0):,.2f}")
print(f"   • Total Expenses: ${summary.get('total_expense', 0):,.2f}")
print(f"   • Net Cashflow: ${summary.get('net_cashflow', 0):,.2f}")
print(f"   • Income/Expense Ratio: {summary.get('income_expense_ratio', 0):.2f}")

# Get forecast health
health = requests.get(f"{BASE_URL}/forecast/{BUSINESS_ID}/health", 
                     headers=headers).json()
print(f"\n🔮 Forecast Readiness:")
print(f"   • Days of data: {health.get('days_of_data', 0)}")
print(f"   • Ready for forecasting: {health.get('ready', False)}")

print("\n🎉 Dataset generation complete! You can now run forecasts with rich historical data.")
