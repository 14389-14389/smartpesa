#!/usr/bin/env python3
"""
Create a test user in the database
"""

from app.database import SessionLocal
from app.models.user import User
from app.auth import hash_password
from datetime import datetime

# Create session
db = SessionLocal()

# Check if test user exists
test_user = db.query(User).filter(User.email == "test@example.com").first()

if not test_user:
    print("Creating test user...")
    hashed_password = hash_password("password123")
    test_user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True,
        role="user",
        created_at=datetime.utcnow()
    )
    db.add(test_user)
    db.commit()
    print("✅ Test user created: test@example.com / password123")
else:
    print("✅ Test user already exists")

# Verify user
user = db.query(User).filter(User.email == "test@example.com").first()
if user:
    print(f"\n📋 User details:")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.full_name}")
    print(f"   Role: {user.role}")
    print(f"   Active: {user.is_active}")

db.close()
