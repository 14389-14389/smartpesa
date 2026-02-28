#!/usr/bin/env python3
"""
Add a test user to the database
"""

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import hash_password
from datetime import datetime

# Create database session
db = SessionLocal()

# Check if user exists
existing_user = db.query(User).filter(User.email == "test@example.com").first()

if existing_user:
    print(f"User already exists: {existing_user.email}")
    # Update password just in case
    existing_user.hashed_password = hash_password("password123")
    db.commit()
    print("Password updated")
else:
    print("Creating new test user...")
    # Create new user
    hashed = hash_password("password123")
    new_user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hashed,
        is_active=True,
        is_admin=True,
        role="admin",
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    print(f"✅ User created: test@example.com / password123")

# Verify the user was created
user = db.query(User).filter(User.email == "test@example.com").first()
if user:
    print(f"\nUser details:")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Name: {user.full_name}")
    print(f"  Role: {user.role}")
    print(f"  Active: {user.is_active}")
else:
    print("❌ Failed to create user")

db.close()
