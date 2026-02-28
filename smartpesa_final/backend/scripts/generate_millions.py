#!/usr/bin/env python3
"""
SmartPesa Massive Data Generator
Generates millions of realistic transactions for testing and demonstration
"""

import random
import requests
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import concurrent.futures
import threading
from queue import Queue
import json

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "test@example.com"
PASSWORD = "password123"
BUSINESS_ID = 1

# Categories
INCOME_CATEGORIES = [
    'Sales', 'Consulting', 'Services', 'Product Revenue', 
    'Subscription Fees', 'Licensing', 'Royalties', 'Interest Income',
    'Dividends', 'Rental Income', 'Commission', 'Affiliate Revenue',
    'Digital Products', 'Course Sales', 'Membership Fees', 'Sponsorships',
    'Advertising', 'Merchandise', 'Event Tickets', 'Grants'
]

EXPENSE_CATEGORIES = [
    'Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies',
    'Insurance', 'Maintenance', 'Travel', 'Software', 'Training',
    'Taxes', 'Equipment', 'Transport', 'Advertising', 'Legal Fees',
    'Consulting Fees', 'Office Supplies', 'Phone/Internet', 'Printing',
    'Postage', 'Bank Fees', 'Interest Expense', 'Depreciation',
    'Research & Development', 'Employee Benefits', 'Recruiting',
    'Uniforms', 'Cleaning Services', 'Security', 'Waste Management'
]

# Kenyan towns for location-based data
TOWNS = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika',
    'Malindi', 'Kitale', 'Garissa', 'Kakamega', 'Bungoma', 'Busia',
    'Migori', 'Homa Bay', 'Kisii', 'Nyamira', 'Kericho', 'Bomet',
    'Narok', 'Kajiado', 'Machakos', 'Makueni', 'Kitui', 'Mwingi',
    'Meru', 'Chuka', 'Embu', 'Nyeri', 'Othaya', 'Karatina',
    'Muranga', 'Thika', 'Kiambu', 'Limuru', 'Naivasha', 'Gilgil'
]

# Business types
BUSINESS_TYPES = [
    'Retail Shop', 'Restaurant', 'Hardware Store', 'Pharmacy',
    'Supermarket', 'Electronics Store', 'Clothing Boutique',
    'Furniture Store', 'Car Wash', 'Salon', 'Gym', 'Hotel',
    'Guest House', 'Cafe', 'Baker', 'Butchery', 'Greengrocer',
    'Bookshop', 'Stationery Store', 'Toy Store', 'Pet Shop'
]

# Payment methods
PAYMENT_METHODS = ['Cash', 'M-Pesa', 'Bank Transfer', 'Credit Card', 'Debit Card']

class ProgressBar:
    def __init__(self, total, desc="Progress"):
        self.pbar = tqdm(total=total, desc=desc, unit="tx")
        self.lock = threading.Lock()
    
    def update(self, n=1):
        with self.lock:
            self.pbar.update(n)
    
    def close(self):
        self.pbar.close()

def login():
    """Login and get token"""
    response = requests.post(f"{BASE_URL}/users/login", 
        json={"email": EMAIL, "password": PASSWORD})
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        exit(1)
    return response.json()["access_token"]

def generate_transaction(date, business_id):
    """Generate a single transaction"""
    # 60% chance of income, 40% chance of expense
    is_income = random.random() < 0.6
    
    if is_income:
        category = random.choice(INCOME_CATEGORIES)
        # Income amounts vary widely
        if category in ['Sales', 'Services']:
            amount = random.uniform(1000, 500000)
        elif category in ['Consulting', 'Licensing']:
            amount = random.uniform(50000, 2000000)
        elif category in ['Subscription Fees', 'Membership Fees']:
            amount = random.uniform(500, 50000)
        else:
            amount = random.uniform(1000, 100000)
        
        # Round to 2 decimal places
        amount = round(amount, 2)
        
        return {
            "amount": amount,
            "type": "income",
            "category": category,
            "description": f"{category} - {date.strftime('%Y-%m-%d')} - {random.choice(TOWNS)}",
            "business_id": business_id
        }
    else:
        category = random.choice(EXPENSE_CATEGORIES)
        # Expense amounts vary by category
        if category in ['Salaries']:
            amount = random.uniform(50000, 500000)
        elif category in ['Rent']:
            amount = random.uniform(20000, 200000)
        elif category in ['Marketing', 'Advertising']:
            amount = random.uniform(5000, 100000)
        elif category in ['Utilities']:
            amount = random.uniform(2000, 50000)
        else:
            amount = random.uniform(500, 50000)
        
        amount = round(amount, 2)
        
        return {
            "amount": amount,
            "type": "expense",
            "category": category,
            "description": f"{category} - {date.strftime('%Y-%m-%d')}",
            "business_id": business_id
        }

def worker(token, tx_queue, progress):
    """Worker thread to send transactions"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    while True:
        try:
            tx = tx_queue.get(timeout=5)
            if tx is None:  # Poison pill
                break
            
            response = requests.post(f"{BASE_URL}/transactions/", 
                                    json=tx, headers=headers)
            
            if response.status_code == 200:
                progress.update()
            else:
                print(f"\n❌ Error: {response.status_code} - {response.text[:100]}")
            
            tx_queue.task_done()
        except Exception as e:
            print(f"\n❌ Worker error: {e}")
            break

def generate_massive_data(num_transactions=1000000):
    """Generate massive amount of transaction data"""
    print("=" * 60)
    print(f"🚀 SmartPesa Massive Data Generator")
    print("=" * 60)
    print(f"Target: {num_transactions:,} transactions")
    print()
    
    # Login
    print("🔐 Logging in...")
    token = login()
    print("✅ Login successful")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)  # 5 years of data
    
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"⏱️  Generating data...")
    print()
    
    # Create queue for transactions
    tx_queue = Queue(maxsize=10000)
    progress = ProgressBar(num_transactions, "Creating transactions")
    
    # Start worker threads
    num_workers = 10
    workers = []
    for _ in range(num_workers):
        t = threading.Thread(target=worker, args=(token, tx_queue, progress))
        t.daemon = True
        t.start()
        workers.append(t)
    
    # Generate transactions
    current_date = start_date
    transactions_created = 0
    
    # Calculate transactions per day to meet target
    total_days = (end_date - start_date).days
    tx_per_day = num_transactions // total_days
    
    with tqdm(total=total_days, desc="Generating days", unit="day") as day_pbar:
        while current_date <= end_date and transactions_created < num_transactions:
            # Determine how many transactions for this day
            # Add some randomness: 70-130% of average
            daily_target = int(tx_per_day * random.uniform(0.7, 1.3))
            daily_target = min(daily_target, num_transactions - transactions_created)
            
            # Add some pattern: weekends have fewer transactions
            if current_date.weekday() >= 5:  # Weekend
                daily_target = int(daily_target * 0.6)
            
            # Add monthly patterns
            if current_date.month == 12:  # December - more sales
                daily_target = int(daily_target * 1.5)
            elif current_date.month == 1:  # January - post-holiday slow
                daily_target = int(daily_target * 0.8)
            
            # Generate transactions for this day
            for _ in range(daily_target):
                tx = generate_transaction(current_date, BUSINESS_ID)
                tx_queue.put(tx)
                transactions_created += 1
                
                if transactions_created >= num_transactions:
                    break
            
            current_date += timedelta(days=1)
            day_pbar.update(1)
            
            # Update description every 100 days
            if day_pbar.n % 100 == 0:
                day_pbar.set_description(f"Day {day_pbar.n}/{total_days}")
    
    # Wait for all transactions to be processed
    print("\n⏳ Waiting for all transactions to be saved...")
    tx_queue.join()
    
    # Stop workers
    for _ in range(num_workers):
        tx_queue.put(None)
    
    for t in workers:
        t.join(timeout=5)
    
    progress.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully created {transactions_created:,} transactions!")
    print("=" * 60)
    
    # Verify the data
    print("\n📊 Verifying data...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get summary
    summary = requests.get(
        f"{BASE_URL}/transactions/summary/overview?business_id={BUSINESS_ID}&days=3650",
        headers=headers
    ).json()
    
    print(f"\n📈 Final Statistics:")
    print(f"   Total Income: KES {summary.get('total_income', 0):,.2f}")
    print(f"   Total Expenses: KES {summary.get('total_expense', 0):,.2f}")
    print(f"   Net Cashflow: KES {summary.get('net_cashflow', 0):,.2f}")
    print(f"   Transaction Count: {summary.get('transaction_count', 0):,}")
    print(f"   Income/Expense Ratio: {summary.get('income_expense_ratio', 0):.2f}")
    
    print("\n🎉 Your dashboard will now show rich, realistic data!")

if __name__ == "__main__":
    import sys
    
    # Get number of transactions from command line or default
    num_tx = 1000000  # Default 1 million
    if len(sys.argv) > 1:
        try:
            num_tx = int(sys.argv[1])
        except:
            pass
    
    generate_massive_data(num_tx)
