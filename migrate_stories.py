import asyncio
import os
import sys

# Crucial: Add AryaPremium to the START of the path so its local files are preferred
sys.path.insert(0, os.path.join(os.getcwd(), 'AryaPremium'))

# Now import the correct database and utils
from database import db
from utils import translate_to_hindi, translate_to_english

async def migrate():
    print("Starting Story Migration (using AryaPremium context)...")
    try:
        await db.connect()
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    stories = await db.db.premium_stories.find({}).to_list(length=None)
    print(f"Found {len(stories)} stories to process.")
    
    updated_count = 0
    for story in stories:
        source_name = story.get('story_name_en')
        source_desc = story.get('description')
        
        if not source_name:
            continue
            
        print(f"Processing: {source_name}")
        
        new_hi_name = translate_to_hindi(source_name)
        new_en_name = translate_to_english(source_name)
        
        upd = {
            "story_name_en": new_en_name,
            "story_name_hi": new_hi_name
        }
        
        if source_desc:
            upd["description"] = translate_to_english(source_desc)
            upd["description_hi"] = translate_to_hindi(source_desc)
            
        await db.db.premium_stories.update_one({"_id": story["_id"]}, {"$set": upd})
        # print results carefully (handle encoding if needed or just skip print)
        try:
            print(f"  Updated: {source_name}")
        except: pass
        
        updated_count += 1
        await asyncio.sleep(0.1)
        
    print(f"Migration complete. {updated_count} stories updated.")

if __name__ == "__main__":
    asyncio.run(migrate())
