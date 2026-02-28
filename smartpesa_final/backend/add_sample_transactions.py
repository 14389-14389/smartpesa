#!/usr/bin/env python3
"""
Add sample transactions to the database
"""

from app.database import SessionLocal
from app.models.transaction import Transaction
from app.models.business import Business
from datetime import datetime, timedelta
import random
from sqlalchemy import func

def add_transactions():
    db = SessionLocal()
    
    try:
        # Get the business
        business = db.query(Business).filter(Business.id == 1).first()
        
        if not business:
            print("❌ Business with ID 1 not found")
            return False
        
        print(f"🏢 Business: {business.name} (ID: {business.id})")
        
        # Check if business already has transactions
        existing = db.query(Transaction).filter(Transaction.business_id == business.id).count()
        print(f"📊 Existing transactions: {existing}")
        
        if existing > 0:
            print(f"✅ Business already has {existing} transactions")
            # Show existing transactions
            transactions = db.query(Transaction).filter(Transaction.business_id == business.id).all()
            print("\n📋 Existing transactions:")
            for t in transactions[:5]:  # Show first 5
                print(f"   - {t.created_at.strftime('%Y-%m-%d')}: {t.type} {t.amount} ({t.category})")
            
            # Ask if user wants to add more
            response = input("\nAdd more transactions? (y/n): ")
            if response.lower() != 'y':
                return True
        
        # Categories for transactions
        categories = {
            'income': ['Sales', 'Consulting', 'Services', 'Commission', 'Product Revenue'],
            'expense': ['Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies', 'Equipment']
        }
        
        # Create 50 transactions over the last 90 days
        num_transactions = 50
        print(f"\n➕ Adding {num_transactions} new transactions...")
        
        transactions = []
        for i in range(num_transactions):
            days_ago = random.randint(0, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # 60% income, 40% expense
            is_income = random.random() < 0.6
            t_type = 'income' if is_income else 'expense'
            category = random.choice(categories[t_type])
            
            # Random amounts
            if is_income:
                amount = round(random.uniform(1000, 500000), 2)
            else:
                amount = round(random.uniform(500, 200000), 2)
            
            transaction = Transaction(
                business_id=business.id,
                amount=amount,
                type=t_type,
                category=category,
                description=f"{category} - {created_at.strftime('%b %Y')}",
                created_at=created_at
            )
            transactions.append(transaction)
        
        db.add_all(transactions)
        db.commit()
        
        print(f"✅ Added {len(transactions)} transactions successfully!")
        
        # Show summary
        summary = db.query(
            Transaction.type, 
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(Transaction.business_id == business.id).group_by(Transaction.type).all()
        
        print("\n📊 Transaction Summary:")
        total_income = 0
        total_expense = 0
        for row in summary:
            print(f"   {row.type}: {row.count} transactions, Total: KES {row.total:,.2f}")
            if row.type == 'income':
                total_income = row.total or 0
            else:
                total_expense = row.total or 0
        
        net = total_income - total_expense
        print(f"\n💰 Net Cashflow: KES {net:,.2f}")
        
        # Show recent transactions
        recent = db.query(Transaction).filter(
            Transaction.business_id == business.id
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        print("\n📋 Recent Transactions:")
        for t in recent:
            print(f"   {t.created_at.strftime('%Y-%m-%d')}: {t.type.upper()} - {t.category}: KES {t.amount:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_transactions()
