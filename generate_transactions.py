import random
from datetime import datetime, timedelta
import requests
import time

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1

# Login to get token
response = requests.post(f"{BASE_URL}/users/login", json={
    "email": EMAIL,
    "password": PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Generate 90 days of transactions
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

income_categories = ['Sales', 'Consulting', 'Services', 'Product Revenue']
expense_categories = ['Rent', 'Utilities', 'Salaries', 'Supplies', 'Marketing']

current_date = start_date
count = 0

print("Generating 90 days of transactions...")

while current_date <= end_date:
    # Generate 2-5 transactions per day
    num_transactions = random.randint(2, 5)
    
    for _ in range(num_transactions):
        if random.random() < 0.6:  # 60% income
            tx_type = 'income'
            category = random.choice(income_categories)
            amount = random.uniform(1000, 15000)
        else:  # 40% expense
            tx_type = 'expense'
            category = random.choice(expense_categories)
            amount = random.uniform(100, 5000)
        
        # Create transaction with date in the past
        transaction = {
            "amount": round(amount, 2),
            "type": tx_type,
            "category": category,
            "description": f"{category} - {current_date.strftime('%Y-%m-%d')}",
            "business_id": BUSINESS_ID
        }
        
        response = requests.post(f"{BASE_URL}/transactions/", json=transaction, headers=headers)
        if response.status_code == 200:
            count += 1
        
        time.sleep(0.05)  # Small delay to avoid overwhelming
    
    current_date += timedelta(days=1)
    
    if count % 50 == 0:
        print(f"   Created {count} transactions...")

print(f"✅ Successfully created {count} transactions!")
