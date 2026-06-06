"""
Check MongoDB Atlas connection and verify collections are initialized.

Usage:
    uv run python scripts/check_mongo_connection.py
"""

import asyncio
import os
from pymongo import AsyncMongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")


async def main():
    """Check MongoDB connection and display collection info."""
    if not MONGO_URI:
        print("❌ MONGODB_URL not set in backend/.env")
        return

    try:
        print("=" * 100)
        print("MongoDB Connection Check")
        print("=" * 100)
        print(f"Database: {DB_NAME}")
        print(f"Connecting...")

        # Create client with timeout
        client = AsyncMongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

        # Test connection with admin ping
        await client.admin.command("ping")
        print("✅ Connection successful!")

        # Get database and list collections
        db = client[DB_NAME]
        collections = await db.list_collection_names()

        print(f"\n✅ Collections ({len(collections)}):")
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            print(f"   - {collection_name}: {count} documents")

        # Check for vector search indexes
        print("\n📊 Vector Search Indexes:")
        if "restaurants" in collections:
            try:
                restaurant_collection = db["restaurants"]
                indexes = await restaurant_collection.list_search_indexes()
                indexes_list = [idx async for idx in indexes]
                if indexes_list:
                    for idx in indexes_list:
                        print(f"   ✅ restaurants.{idx.get('name', 'unknown')}")
                else:
                    print("   ⚠️  No vector search indexes on restaurants collection")
            except Exception as e:
                print(f"   ⚠️  Could not check restaurant indexes: {e}")

        if "food" in collections:
            try:
                food_collection = db["food"]
                indexes = await food_collection.list_search_indexes()
                indexes_list = [idx async for idx in indexes]
                if indexes_list:
                    for idx in indexes_list:
                        print(f"   ✅ food.{idx.get('name', 'unknown')}")
                else:
                    print("   ⚠️  No vector search indexes on food collection")
            except Exception as e:
                print(f"   ⚠️  Could not check food indexes: {e}")

        print("\n" + "=" * 100)
        print("✅ All checks passed! MongoDB is ready for development.")
        print("=" * 100)

        await client.close()

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("=" * 100)
        print("Troubleshooting:")
        print("1. Verify MONGODB_URL is set in backend/.env")
        print("2. Check your MongoDB Atlas IP whitelist includes your current IP")
        print("3. Verify database name matches (default: 'vybe')")
        print("4. Run: uv run python scripts/seed_database.py (if collections don't exist)")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())