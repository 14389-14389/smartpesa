import requests
import random
import numpy as np
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import math

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1
TARGET_TRANSACTIONS = 100000  # 100K is plenty!

print("=" * 70)
print(f"📊 GENERATING {TARGET_TRANSACTIONS:,} TRANSACTIONS (10 years)")
print("=" * 70)

# Login
print("\n🔐 Logging in...")
response = requests.post(f"{BASE_URL}/users/login", json={
    "email": EMAIL,
    "password": PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Delete old transactions
print("\n🧹 Cleaning up old transactions...")
try:
    transactions = requests.get(
        f"{BASE_URL}/transactions/?business_id={BUSINESS_ID}&limit=10000",
        headers=headers
    ).json()
    
    if transactions:
        for t in tqdm(transactions, desc="Deleting old transactions"):
            requests.delete(f"{BASE_URL}/transactions/{t['id']}", headers=headers)
            time.sleep(0.01)
    print(f"✅ Deleted {len(transactions)} old transactions")
except:
    print("No existing transactions to delete")

# ============================================
# BUSINESS PARAMETERS
# ============================================
print("\n📈 Configuring business parameters...")

# Growth curve (exponential then linear)
def growth_multiplier(year):
    years_from_start = year - 2016
    if years_from_start < 0:
        return 0.3
    elif years_from_start < 3:
        return 0.5 + years_from_start * 0.3
    elif years_from_start < 6:
        return 1.4 + (years_from_start - 3) * 0.4
    else:
        return 2.6 + (years_from_start - 6) * 0.1

# Seasonal patterns
seasonal_multiplier = {
    1: 0.70, 2: 0.75, 3: 0.85, 4: 0.95,
    5: 1.05, 6: 1.15, 7: 1.25, 8: 1.20,
    9: 1.10, 10: 1.00, 11: 0.95, 12: 1.35
}

# Day of week patterns
dow_multiplier = {
    0: 1.20, 1: 1.15, 2: 1.10, 3: 1.15, 4: 1.25, 5: 0.55, 6: 0.50
}

# Categories
income_cats = ['Sales', 'Services', 'Subscriptions', 'Consulting', 'Licensing']
expense_cats = ['Salaries', 'Rent', 'Utilities', 'Marketing', 'Supplies', 
                'Insurance', 'Maintenance', 'Software', 'Travel', 'Taxes']

# ============================================
# GENERATE IN BATCHES
# ============================================
print(f"\n🔄 Generating {TARGET_TRANSACTIONS:,} transactions...")

start_date = datetime(2016, 1, 1)
end_date = datetime(2026, 2, 15)
current_date = start_date

transactions_created = 0
batch_size = 100
total_income = 0
total_expense = 0

pbar = tqdm(total=TARGET_TRANSACTIONS, desc="Creating transactions", unit="tx")

while transactions_created < TARGET_TRANSACTIONS and current_date <= end_date:
    year = current_date.year
    month = current_date.month
    day = current_date.day
    weekday = current_date.weekday()
    
    # Calculate multipliers
    growth = growth_multiplier(year)
    seasonal = seasonal_multiplier.get(month, 1.0)
    dow = dow_multiplier.get(weekday, 1.0)
    
    # Base value for this day
    base_value = 5000 * growth * seasonal * dow
    
    # Number of transactions today (more on busy days)
    if weekday >= 5:  # Weekend
        tx_today = random.randint(3, 8)
    elif weekday == 4:  # Friday
        tx_today = random.randint(15, 25)
    else:  # Weekday
        tx_today = random.randint(8, 15)
    
    # Cap to avoid exceeding target
    tx_today = min(tx_today, TARGET_TRANSACTIONS - transactions_created)
    
    # Generate transactions for this day
    for i in range(tx_today):
        # 60% income, 40% expense
        is_income = random.random() < 0.6
        
        if is_income:
            category = random.choice(income_cats)
            # Income varies more
            amount = base_value * random.uniform(0.3, 2.5)
            tx_type = 'income'
            total_income += amount
        else:
            category = random.choice(expense_cats)
            # Expenses more stable
            if category in ['Rent', 'Insurance']:
                amount = base_value * 0.3 * random.uniform(0.9, 1.1)
            elif category == 'Salaries':
                amount = base_value * 0.5 * random.uniform(0.95, 1.05)
            else:
                amount = base_value * random.uniform(0.1, 0.4)
            tx_type = 'expense'
            total_expense += amount
        
        # Round to 2 decimals
        amount = round(amount, 2)
        
        # Create transaction
        date_str = current_date.strftime('%Y-%m-%d')
        desc = f"{category} - {date_str}"
        
        # Add some variation in descriptions
        if random.random() < 0.1:
            desc += f" (Ref: TX-{transactions_created+i})"
        
        response = requests.post(
            f"{BASE_URL}/transactions/",
            json={
                "amount": amount,
                "type": tx_type,
                "category": category,
                "description": desc,
                "business_id": BUSINESS_ID
            },
            headers=headers
        )
        
        if response.status_code == 200:
            pbar.update(1)
        
        # Small delay to avoid overwhelming
        if i % 10 == 0:
            time.sleep(0.01)
    
    transactions_created += tx_today
    current_date += timedelta(days=1)
    
    # Progress update
    if current_date.day == 1:
        tqdm.write(f"📅 Entering {current_date.strftime('%B %Y')}")

pbar.close()

# ============================================
# FINAL STATISTICS
# ============================================
print("\n" + "=" * 70)
print("📊 GENERATION COMPLETE!")
print("=" * 70)

print(f"\n✅ Created {transactions_created:,} transactions")
print(f"📅 Date range: 2016-01-01 to {current_date.strftime('%Y-%m-%d')}")
print(f"💰 Total Income: ${total_income:,.2f}")
print(f"💰 Total Expenses: ${total_expense:,.2f}")
print(f"📈 Net Profit: ${total_income - total_expense:,.2f}")

# Get forecast health
print("\n🔮 Checking forecast readiness...")
health = requests.get(
    f"{BASE_URL}/forecast/{BUSINESS_ID}/health",
    headers=headers
).json()

print(f"📊 Days of data: {health.get('days_of_data', 0)}")
print(f"✅ Ready for forecasting: {health.get('ready', False)}")

# Get transaction summary
summary = requests.get(
    f"{BASE_URL}/transactions/summary/overview?business_id={BUSINESS_ID}&days=3650",
    headers=headers
).json()

print(f"\n📈 10-Year Summary:")
print(f"   • Total Transactions: {summary.get('transaction_count', 0)}")
print(f"   • Total Income: ${summary.get('total_income', 0):,.2f}")
print(f"   • Total Expenses: ${summary.get('total_expense', 0):,.2f}")
print(f"   • Net Cashflow: ${summary.get('net_cashflow', 0):,.2f}")

print("\n" + "=" * 70)
print("✅ DATASET GENERATION COMPLETE!")
print("=" * 70)
