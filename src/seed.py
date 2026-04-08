import asyncio
import argparse
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.database import AsyncSessionLocal
from core.models import User
from core.auth import get_password_hash
from sqlalchemy import select


async def seed(username: str, email: str, password: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User '{email}' already exists.")
            return

        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"✓ Admin user '{username}' ({email}) created successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the first admin user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    asyncio.run(seed(args.username, args.email, args.password))