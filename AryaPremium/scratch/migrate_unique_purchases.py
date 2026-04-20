from database import db
import asyncio

async def migrate_users_purchases():
    await db.connect()
    users_cursor = db.db.users.find({"purchases.0": {"$exists": True}})
    async for user in users_cursor:
        purchases = user.get("purchases", [])
        if not purchases: continue
        
        # Convert all to strings and keep order but unique
        seen = set()
        unique_purchases = []
        for p in purchases:
            p_str = str(p)
            if p_str not in seen:
                unique_purchases.append(p_str) # save as strings to be safe
                seen.add(p_str)
        
        if len(unique_purchases) != len(purchases):
            print(f"User {user['id']}: Deduplicating {len(purchases)} -> {len(unique_purchases)}")
            await db.db.users.update_one({"id": user["id"]}, {"$set": {"purchases": unique_purchases}})
    print("Database deduplication migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_users_purchases())
