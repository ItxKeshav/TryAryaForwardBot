from database import db
import asyncio
import utils

async def migrate_stories():
    await db.connect()
    stories_cursor = db.db.premium_stories.find({})
    async for story in stories_cursor:
        update = {}
        
        # 1. Name translation if hi missing
        en_name = story.get("story_name_en", "Story")
        hi_name = story.get("story_name_hi")
        if not hi_name or hi_name == en_name:
             print(f"Translating name: {en_name}...")
             update["story_name_hi"] = utils.translate_to_hindi(en_name)
        
        # 2. Description translation if hi missing
        en_desc = story.get("description", "None")
        hi_desc = story.get("description_hi")
        if not hi_desc and en_desc and en_desc.lower() != "none":
             print(f"Translating description for {en_name}...")
             update["description_hi"] = utils.translate_to_hindi(en_desc)
             
        if update:
            await db.db.premium_stories.update_one({"_id": story["_id"]}, {"$set": update})
    print("Story translation migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_stories())
