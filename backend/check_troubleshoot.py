
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def check_user_model():
    print("--- Checking User Model ---")
    async with AsyncSessionLocal() as session:
        # Fetch any user
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User Found: {user.email}")
            print(f"Has is_superuser: {hasattr(user, 'is_superuser')}")
            print(f"is_superuser value: {user.is_superuser}")
            print(f"Has role: {hasattr(user, 'role')}")
            print(f"Role value: {user.role}")
        else:
            print("No users found in DB.")

if __name__ == "__main__":
    try:
        asyncio.run(check_user_model())
        print("Check Complete.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
