import requests
import random
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1  # Change this to your business ID

# Login to get token
response = requests.post(f"{BASE_URL}/users/login", json={
    "email": EMAIL,
    "password": PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Generate 90 days of historical data
print("Generating 90 days of transaction data...")
start_date = datetime.utcnow() - timedelta(days=90)

for i in range(90):
    date = start_date + timedelta(days=i)
    
    # Income (more on weekdays)
    if date.weekday() < 5:  # Weekday
        income = random.uniform(4000, 6000)
    else:  # Weekend
        income = random.uniform(2000, 3500)
    
    # Create income transaction
    requests.post(f"{BASE_URL}/transactions/", 
                  json={
                      "amount": round(income, 2),
                      "type": "income",
                      "category": "Sales",
                      "description": f"Daily sales {date.strftime('%Y-%m-%d')}",
                      "business_id": BUSINESS_ID
                  }, headers=headers)
    
    # Expenses (rent monthly, utilities weekly, etc.)
    if i % 30 == 0:  # Monthly rent
        requests.post(f"{BASE_URL}/transactions/", 
                      json={
                          "amount": 1200,
                          "type": "expense",
                          "category": "Rent",
                          "description": f"Monthly rent {date.strftime('%Y-%m')}",
                          "business_id": BUSINESS_ID
                      }, headers=headers)
    
    if i % 7 == 0:  # Weekly utilities
        requests.post(f"{BASE_URL}/transactions/", 
                      json={
                          "amount": random.uniform(300, 400),
                          "type": "expense",
                          "category": "Utilities",
                          "description": f"Weekly utilities {date.strftime('%Y-%m-%d')}",
                          "business_id": BUSINESS_ID
                      }, headers=headers)
    
    # Daily expenses
    if random.random() < 0.3:  # 30% chance of daily expense
        requests.post(f"{BASE_URL}/transactions/", 
                      json={
                          "amount": random.uniform(50, 200),
                          "type": "expense",
                          "category": "Supplies",
                          "description": f"Daily supplies {date.strftime('%Y-%m-%d')}",
                          "business_id": BUSINESS_ID
                      }, headers=headers)
    
    if i % 10 == 0:
        print(f"Generated {i+1} days of data...")

print("Sample data generation complete!")
