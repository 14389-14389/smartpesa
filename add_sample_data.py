import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import User, Business, Transaction
from app.auth import hash_password

db = SessionLocal()
try:
    # Get business
    business = db.query(Business).first()
    if not business:
        print("No business found. Please create a business first.")
        exit()
    
    print(f"📊 Creating sample transactions for business: {business.name}")
    
    # Generate 90 days of transactions
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    income_categories = ['Sales', 'Consulting', 'Services', 'Product Revenue']
    expense_categories = ['Rent', 'Utilities', 'Salaries', 'Supplies', 'Marketing']
    
    current_date = start_date
    transaction_count = 0
    
    while current_date <= end_date:
        # Generate 2-5 transactions per day
        num_transactions = random.randint(2, 5)
        
        for _ in range(num_transactions):
            # 60% income, 40% expense
            if random.random() < 0.6:
                tx_type = 'income'
                category = random.choice(income_categories)
                amount = random.uniform(1000, 15000)
            else:
                tx_type = 'expense'
                category = random.choice(expense_categories)
                amount = random.uniform(100, 5000)
            
            # Create transaction with date in the past
            transaction = Transaction(
                amount=round(amount, 2),
                type=tx_type,
                category=category,
                description=f"{category} - {current_date.strftime('%Y-%m-%d')}",
                business_id=business.id,
                created_at=current_date
            )
            db.add(transaction)
            transaction_count += 1
        
        current_date += timedelta(days=1)
        
        if transaction_count % 50 == 0:
            print(f"   Created {transaction_count} transactions...")
    
    db.commit()
    print(f"\n✅ Successfully created {transaction_count} transactions!")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Verify the data
    total = db.query(Transaction).filter(Transaction.business_id == business.id).count()
    print(f"📊 Total transactions in database: {total}")
    
    # Calculate summary
    from sqlalchemy import func
    summary = db.query(
        func.sum(Transaction.amount).filter(Transaction.type == 'income').label('total_income'),
        func.sum(Transaction.amount).filter(Transaction.type == 'expense').label('total_expense')
    ).filter(Transaction.business_id == business.id).first()
    
    print(f"💰 Total Income: KES {summary.total_income:,.2f}")
    print(f"💰 Total Expenses: KES {summary.total_expense:,.2f}")
    print(f"📈 Net Cashflow: KES {summary.total_income - summary.total_expense:,.2f}")
    
finally:
    db.close()
