import asyncio, sys, os
from dotenv import load_dotenv
load_dotenv('AryaPremium/.env')
sys.path.insert(0, os.path.abspath('AryaPremium'))
from config import Config
from database import db
from bson.objectid import ObjectId

async def main():
    await db.connect()
    
    stories = await db.db.premium_stories.find().sort([('_id', -1)]).limit(3).to_list(length=3)
    for s in stories:
        id_val = s.get('_id')
        sid_val = s.get('story_id')
        print(f"_id: {id_val} (type {type(id_val)})")
        print(f"story_id: {sid_val} (type {type(sid_val)})")
        print("---")

asyncio.run(main())
