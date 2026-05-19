"""
Check MongoDB index types and vector embedding status.
Helps diagnose if vector search is properly configured.
"""

import asyncio
import os
from pymongo import AsyncMongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")
RESTAURANTS_COLLECTION = "restaurants"


async def main():
    print("=" * 70)
    print("INDEX AND EMBEDDING VERIFICATION")
    print("=" * 70)

    if not MONGO_URI:
        print("❌ MONGODB_URL not set")
        return

    client = AsyncMongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    db = client[DB_NAME]
    collection = db[RESTAURANTS_COLLECTION]

    # Check indexes
    print("📍 INDEXES IN COLLECTION:")
    print("-" * 70)
    try:
        # Get index info from the collection
        index_info = await collection.index_information()
        indexes = [{"name": name, "key": spec.get("key", [])} for name, spec in index_info.items()]
    except Exception as e:
        print(f"⚠️  Could not fetch indexes: {e}")
        indexes = []

    for idx in indexes:
        name = idx.get("name", "unknown")
        spec = idx.get("key", [])
        print(f"\nIndex: {name}")
        print(f"  Keys: {spec}")

        # Check if it's a problematic 2dsphere vector index
        for key, index_type in spec:
            if key == "vector_embeddings":
                print(f"  ⚠️  FOUND: vector_embeddings field")
                print(f"      Type: {index_type}")
                if index_type == "2dsphere":
                    print(f"      ❌ ISSUE: This is a GEOSPATIAL index, not a VECTOR index!")
                    print(f"      Fix: Drop this index and use Atlas Vector Search API")
                elif index_type == "vectorSearch":
                    print(f"      ✅ CORRECT: This is a proper vector search index")
            elif key == "location":
                if index_type == "2dsphere":
                    print(f"  ✅ location: 2dsphere (correct for geospatial)")

    # Check documents for vector embeddings
    print("\n\n📊 VECTOR EMBEDDINGS IN DOCUMENTS:")
    print("-" * 70)

    sample = await collection.find_one({"vector_embeddings": {"$exists": True}})

    if sample:
        vector = sample.get("vector_embeddings", [])
        print(f"✅ Found document with vector embeddings")
        print(f"   Vector length: {len(vector)}")
        print(f"   Expected length: 1536 (text-embedding-3-small)")
        print(f"   Vector type: {type(vector)}")

        if len(vector) == 1536:
            print(f"   ✅ CORRECT: 1536-dimensional vector")
        else:
            print(f"   ⚠️  MISMATCH: Expected 1536, got {len(vector)}")

        # Show first few values
        print(f"   Sample values: {vector[:3]}")

        # Check metadata
        print(f"\n   Embedding metadata:")
        print(f"   - Model: {sample.get('embedding_model', 'NOT SET')}")
        print(f"   - Dimensions: {sample.get('embedding_dimensions', 'NOT SET')}")
        print(f"   - Timestamp: {sample.get('embedding_timestamp', 'NOT SET')}")
    else:
        print("❌ No documents found with vector_embeddings field")

    # Count documents with vectors
    vector_count = await collection.count_documents({"vector_embeddings": {"$exists": True}})
    total_count = await collection.count_documents({})

    print(f"\n\n📈 DOCUMENT STATISTICS:")
    print("-" * 70)
    print(f"Total documents: {total_count}")
    print(f"Documents with vectors: {vector_count}")
    if total_count > 0:
        percent = (vector_count / total_count) * 100
        print(f"Coverage: {percent:.1f}%")
        if vector_count != total_count:
            print(f"⚠️  Some documents are missing embeddings!")

    print("\n" + "=" * 70)
    
    cursor = await collection.list_search_indexes()
    indexes = await cursor.to_list(length=None)
    for index in indexes:
        print(index)
    
    await client.close()
    


if __name__ == "__main__":
    asyncio.run(main())