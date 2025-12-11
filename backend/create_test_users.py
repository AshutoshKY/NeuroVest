#!/usr/bin/env python3
"""Create test users for development"""

import sys
import os
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()

# Create test users
test_users = [
    {
        "email": "demo@neurovest.com",
        "password": "Demo@12345",
        "full_name": "Demo User",
        "role": UserRole.USER
    },
    {
        "email": "demouser2@testing.com",
        "password": "Test@1234",
        "full_name": "Demo User 2",
        "role": UserRole.USER
    },
    {
        "email": "admin@neurovest.com",
        "password": "Admin@12345",
        "full_name": "Admin User",
        "role": UserRole.ADMIN
    }
]

for user_data in test_users:
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    
    if existing:
        print(f"✅ User already exists: {user_data['email']}")
        continue
    
    # Create new user
    user = User(
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
        full_name=user_data["full_name"],
        role=user_data["role"],
        is_verified=True,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    print(f"✅ Created user: {user_data['email']} (password: {user_data['password']})")

db.close()
print("\n🎉 Test users ready for login!")
