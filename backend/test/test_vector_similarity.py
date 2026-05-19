"""
Test vector similarity by querying MongoDB Atlas for stored embeddings
and comparing them with query embeddings using cosine similarity.
"""

import asyncio
import os
import sys
import numpy as np
from pymongo import AsyncMongoClient
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")
RESTAURANTS_COLLECTION = "restaurants"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Test queries to compare against restaurants
TEST_QUERIES = [
    "open 24 hours restaurant",
    "open 24/7 food nearby",
    "late night food",
    "vegan late night restaurant",
    "vegan diner",
    "Italian restaurant nearby",
    "nice steakhouse",
    "cozy romantic dinner place",
    "family-friendly brunch",
    "gluten free options",
]



async def generate_query_embedding(client: AsyncOpenAI, query: str) -> list[float] | None:
    """Generate embedding for a query string"""
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=1536
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Failed to generate query embedding: {e}")
        return None


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


async def main() -> bool:
    print("=" * 70)
    print("VECTOR SIMILARITY TEST - MongoDB Atlas")
    print("=" * 70)

    if not MONGO_URI:
        print("❌ MONGO_URI not set. Set MONGODB_URL environment variable")
        return False

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set")
        return False

    # Connect to MongoDB
    print(f"\n🔌 Connecting to MongoDB...")
    client = AsyncMongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False

    db = client[DB_NAME]
    collection = db[RESTAURANTS_COLLECTION]

    try:
        # Fetch restaurant with embedding from MongoDB
        print(f"\n📍 Fetching restaurants with embeddings from MongoDB...")
        restaurants = await collection.find(
            {"vector_embeddings": {"$exists": True}}
        ).to_list(None)

        if not restaurants:
            print("❌ No restaurants with embeddings found in MongoDB")
            print("   Run seed_database.py first to generate embeddings")
            return False

        print(f"✅ Found {len(restaurants)} restaurant(s) with embeddings")

        # Process each restaurant
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        for restaurant in restaurants:
            name = restaurant.get("name", "Unknown")
            stored_vector = np.array(restaurant.get("vector_embeddings", []))

            if len(stored_vector) == 0:
                print(f"\n⚠️  {name} has no vector data, skipping...")
                continue

            print(f"\n{'=' * 70}")
            print(f"Restaurant: {name}")
            print(f"Stored Vector Dimensions: {len(stored_vector)}")
            print(f"{'=' * 70}")

            # Test similarity with multiple queries
            print(f"\n📊 Query Similarity Scores:\n")
            print(f"{'Query':<45} {'Similarity Score':<20}")
            print("-" * 70)

            for query in TEST_QUERIES:
                try:
                    # Generate query embedding
                    query_vector_list = await generate_query_embedding(
                        openai_client, query
                    )
                except Exception as e:
                    print(f"{query:<45} {'ERROR':<20}")
                    continue

                query_vector = np.array(query_vector_list)

                # Calculate similarity
                similarity = cosine_similarity(stored_vector, query_vector)
                score_percent = similarity * 100

                # Color coding based on score
                if score_percent > 75:
                    status = "🔥 Excellent"
                elif score_percent > 60:
                    status = "✅ Good"
                elif score_percent > 50:
                    status = "⚠️  Moderate"
                else:
                    status = "❌ Low"

                print(f"{query:<45} {score_percent:>6.2f}% {status:<15}")

        print(f"\n{'=' * 70}")
        print("✅ Vector similarity test completed!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)