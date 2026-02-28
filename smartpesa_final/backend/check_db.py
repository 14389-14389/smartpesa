#!/usr/bin/env python3
"""
Check database contents
"""

from app.database import SessionLocal
from app.models.user import User
from app.models.business import Business
from app.models.transaction import Transaction
from app.models.inventory import Inventory
from datetime import datetime

db = SessionLocal()

try:
    print('📊 DATABASE CONTENTS')
    print('=' * 60)
    
    # Check users
    users = db.query(User).all()
    print(f'\n👤 Users: {len(users)}')
    for u in users:
        print(f'   - {u.email} (ID: {u.id}, Name: {u.full_name})')
    
    # Check businesses
    businesses = db.query(Business).all()
    print(f'\n🏢 Businesses: {len(businesses)}')
    for b in businesses:
        print(f'   - {b.name} (ID: {b.id}, Owner: {b.owner_id})')
    
    # Check transactions
    transactions = db.query(Transaction).all()
    print(f'\n💰 Transactions: {len(transactions)}')
    for t in transactions[:10]:  # Show first 10 only
        print(f'   - {t.created_at.strftime("%Y-%m-%d") if t.created_at else "N/A"}: {t.type} {t.amount} ({t.category})')
    
    if len(transactions) > 10:
        print(f'   ... and {len(transactions) - 10} more transactions')
    
    # Check inventory
    inventory = db.query(Inventory).all()
    print(f'\n📦 Inventory: {len(inventory)}')
    for i in inventory:
        print(f'   - {i.name}: {i.quantity} {i.unit} (Ksh {i.price_per_unit})')
    
    # Summary
    print('\n' + '=' * 60)
    print(f'SUMMARY:')
    print(f'   - Users: {len(users)}')
    print(f'   - Businesses: {len(businesses)}')
    print(f'   - Transactions: {len(transactions)}')
    print(f'   - Inventory Items: {len(inventory)}')

except Exception as e:
    print(f'❌ Error: {e}')
finally:
    db.close()
