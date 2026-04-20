import asyncio
import os
import sys

# Add current dir to sys.path to import database
sys.path.append(os.getcwd())

from database import db

async def check():
    await db.connect()
    # Find a user with purchases
    user = await db.db.users.find_one({"purchases": {"$exists": True, "$ne": []}})
    if user:
        print(f"User ID: {user.get('id')}")
        print(f"Purchases: {user.get('purchases')}")
    else:
        print("No users with purchases found.")
    
    # Check a story
    story = await db.db.premium_stories.find_one()
    if story:
        print(f"Story Sample: {story}")
    else:
        print("No stories found.")

if __name__ == "__main__":
    asyncio.run(check())
