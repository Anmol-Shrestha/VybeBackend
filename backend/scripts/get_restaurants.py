"""
Fetch all restaurants with their ID, name, and description from MongoDB.
"""

import asyncio
import os
from pymongo import AsyncMongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")

async def main():
    """Fetch and display all restaurants"""
    client = AsyncMongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["restaurants"]

    print("=" * 100)
    print("ALL RESTAURANTS")
    print("=" * 100)

    restaurants = await collection.find(
        {},
        {"restaurant_id": 1, "name": 1, "description": 1}
    ).sort("restaurant_id", 1).to_list(None)

    for r in restaurants:
        print(f"\nID: {r.get('restaurant_id')}")
        print(f"Name: {r.get('name')}")
        print(f"Description: {r.get('description')}")
        print("-" * 100)

    print(f"\nTotal: {len(restaurants)} restaurants")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())