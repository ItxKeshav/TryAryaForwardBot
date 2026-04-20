import asyncio
import os
import sys

# Move into AryaPremium to avoid confusion with root database.py
os.chdir(os.path.join(os.getcwd(), "AryaPremium"))
sys.path.append(os.getcwd())

from database import db

async def check():
    await db.connect()
    # Find a user with purchases
    user = await db.db.users.find_one({"purchases": {"$exists": True, "$ne": []}})
    if user:
        print(f"User ID: {user.get('id')}")
        print(f"Purchases: {user.get('purchases')}")
        
        # Check stories for these purchases
        for pid in user.get('purchases', []):
            try:
                from bson.objectid import ObjectId
                st = await db.db.premium_stories.find_one({"_id": ObjectId(pid)})
                print(f"Story ID {pid}: name_en='{st.get('story_name_en')}', name_hi='{st.get('story_name_hi')}'")
            except:
                print(f"Invalid ID format: {pid}")
    else:
        print("No users with purchases found.")
    
    # Check a story
    story = await db.db.premium_stories.find_one()
    if story:
        print(f"Story Sample: {story}")

if __name__ == "__main__":
    asyncio.run(check())
