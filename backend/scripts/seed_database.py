"""
Transforms test data from JSON and seeds MongoDB with restaurants and users.

Handles:
- Location: Converts lat/long to GeoJSON Point format
- Service Hours: Converts time strings to "Minutes from Midnight"
- Booleans: Ensures native boolean types
- Embeddings: Generates OpenAI vector embeddings for RAG pipeline
- Creates required 2dsphere and vector search indexes
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
import os
from pymongo import GEOSPHERE, AsyncMongoClient
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection string (update as needed)
MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")
RESTAURANTS_COLLECTION = "restaurants"
USERS_COLLECTION = "users"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def time_to_minutes(time_str: str) -> int:
    """Convert time string like '12:00 PM' to minutes from midnight"""
    try:
        time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
        return time_obj.hour * 60 + time_obj.minute
    except ValueError:
        # Handle 24-hour format fallback
        try:
            time_obj = datetime.strptime(time_str.strip(), "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except ValueError:
            raise ValueError(f"Cannot parse time: {time_str}")


def normalize_service_hours(hours: dict) -> dict:
    """
    Normalize service_hours to minutes-from-midnight format.
    Handles both string format and already-normalized format.
    """
    normalized = {}

    for day, times in hours.items():
        if isinstance(times, dict) and "open" in times and "close" in times:
            # Already in minutes format
            normalized[day] = times
        elif isinstance(times, str):
            if times.lower() == "closed":
                normalized[day] = None
            else:
                # Parse string format like "12:00 PM – 7:00 PM" or "12:00 PM - 7:00 PM"
                parts = times.split("–") if "–" in times else times.split("-")
                if len(parts) == 2:
                    open_time = time_to_minutes(parts[0])
                    close_time = time_to_minutes(parts[1])
                    normalized[day] = {"open": open_time, "close": close_time}
                else:
                    raise ValueError(f"Cannot parse service hours: {times}")
        else:
            raise ValueError(f"Unknown service_hours format: {times}")

    return normalized


def transform_restaurant(raw: dict, index: int) -> dict:
    """Transform raw restaurant data to match RestaurantEntity model"""
    return {
        "restaurant_id": f"restaurant_{index}",
        "name": raw["name"],
        "slug": raw["name"].lower().replace(" ", "-"),
        "address_display": raw["address_display"],
        "description": raw.get("description", ""),
        # Convert to GeoJSON Point format
        "location": {
            "type": "Point",
            "coordinates": [raw["longitude"], raw["latitude"]]  # [long, lat]
        },
        "rating": raw.get("rating", 4.5),  # Default rating
        "cuisine": raw.get("cuisine", []),
        "dietary": raw.get("dietary", []),
        "meal_types": raw.get("meal_types", []),
        "max_capacity": raw.get("max_capacity", 0),
        "has_parking": bool(raw.get("has_parking", False)),
        "has_live_music": bool(raw.get("has_live_music", False)),
        "buffet": bool(raw.get("buffet", False)),
        "price_max": raw.get("price_max", 0),
        "service_hours": normalize_service_hours(raw.get("service_hours", {})),
        "ai_metadata": raw.get("ai_metadata", {}),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def transform_user(raw: dict) -> dict:
    """Transform raw user data to match UserEntity model"""
    # Parse allergens if it's a string
    allergens = raw.get("allergen", [])
    if isinstance(allergens, str):
        # Split by comma and strip whitespace
        allergens = [a.strip() for a in allergens.split(",")]

    return {
        "user_id": f"user_{raw['userID']}",
        "name": raw["name"],
        "latitude": raw.get("latitude", 0),
        "longitude": raw.get("longitude", 0),
        "dietary": raw.get("dietary", "").lower(),  # e.g., "vegan"
        "allergens": allergens,
        "requires_wheelchair_access": raw.get("requires_wheelchair_access", False),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


async def load_json_file(filepath: Path) -> dict | list:
    """Load JSON file"""
    with open(filepath) as f:
        return json.load(f)


async def generate_embedding(client: AsyncOpenAI, text: str) -> list[float] | None:
    """Generate OpenAI embedding for given text"""
    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"⚠️  Failed to generate embedding: {e}")
        return None


def build_embedding_text(doc: dict) -> str:
    """
    Build optimized embedding text with key attributes repeated for semantic emphasis.
    Prioritizes searchable characteristics for better RAG retrieval.
    """
    # 1. Pull out core metadata
    name = doc.get("name", "")
    description = doc.get("description", "")
    cuisine_list = doc.get("cuisine", [])
    dietary_list = doc.get("dietary", [])
    meal_types = doc.get("meal_types", [])

    # 2. Extract AI Metadata
    ai_meta = doc.get("ai_metadata", {})
    atmosphere_tags = ai_meta.get("atmosphere", [])
    vibe_tags = ai_meta.get("vibe_tags", [])
    best_for = ai_meta.get("best_for", [])

    # 3. Build semantic-rich embedding text with keyword emphasis
    # Start with name and description (most important)
    text_to_embed = f"{name}. {description}. "

    # Add meal types early (searchable time-based queries)
    if meal_types:
        meal_str = ', '.join(meal_types)
        text_to_embed += f"Open for: {meal_str}. Serves: {meal_str}. "

    # Add dietary preferences (highly searchable)
    if dietary_list:
        diet_str = ', '.join(dietary_list)
        text_to_embed += f"Offers: {diet_str}. Dietary options: {diet_str}. "

    # Add cuisine types
    if cuisine_list:
        text_to_embed += f"Cuisine: {', '.join(cuisine_list)}. "

    # Add vibe/atmosphere tags (searchable for ambiance queries)
    if atmosphere_tags:
        atmos_str = ', '.join(atmosphere_tags)
        text_to_embed += f"Atmosphere: {atmos_str}. Feel: {atmos_str}. "

    if vibe_tags:
        text_to_embed += f"Vibes: {', '.join(vibe_tags)}. "

    # Add best_for tags (intent-based search)
    if best_for:
        text_to_embed += f"Perfect for: {', '.join(best_for)}. "

    return text_to_embed


async def seed_restaurants(collection, restaurants_data: list) -> list | None:
    """Insert restaurants, generate embeddings, and create indexes"""
    if not restaurants_data:
        print("⚠️  No restaurants to insert")
        return None

    print(f"\n📝 Transforming {len(restaurants_data)} restaurants...")
    transformed = [transform_restaurant(r, i) for i, r in enumerate(restaurants_data, 1)]

    print(f"📤 Inserting {len(transformed)} restaurants into MongoDB...")
    result = await collection.insert_many(transformed)
    print(f"✅ Inserted {len(result.inserted_ids)} restaurants")

    # Generate embeddings for each restaurant
    print(f"\n🧠 Generating OpenAI embeddings for {len(transformed)} restaurants...")

    if not OPENAI_API_KEY:
        print("⚠️  OPENAI_API_KEY not set - skipping embedding generation")
    else:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        for i, doc in enumerate(transformed, 1):
            try:
                # Build comprehensive text for embedding
                text_to_embed = build_embedding_text(doc)
                print(f"   [{i}/{len(transformed)}] Generating embedding for: {doc.get('name')}...")

                # Generate embedding vector
                vector = await generate_embedding(client, text_to_embed)

                if vector:
                    # Store embedding and metadata in MongoDB
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                "vector_embeddings": vector,
                                "embedding_model": EMBEDDING_MODEL,
                                "embedding_dimensions": EMBEDDING_DIMENSIONS,
                                "embedding_source": text_to_embed,
                                "embedding_timestamp": datetime.now(timezone.utc)
                            }
                        }
                    )
                    print(f"      ✅ Embedding stored ({len(vector)} dimensions)")
                else:
                    print(f"      ⚠️  Skipped embedding for {doc.get('name')}")

            except Exception as e:
                print(f"      ❌ Error processing {doc.get('name')}: {e}")

        print(f"\n✅ Embedding generation completed")

    # Create indexes
    print("📍 Creating geospatial index...")
    await collection.create_index([("location", GEOSPHERE)])
    print("✅ Geospatial index created")

    print("📍 Creating vector search index...")
    try:
        await collection.create_index([("vector_embeddings", "2dsphere")])
        print("✅ Vector index created")
    except Exception as e:
        print(f"⚠️  Vector index creation note: {e}")

    return transformed


async def seed_users(collection, users_data: dict) -> dict | None:
    """Insert users"""
    if not users_data:
        print("⚠️  No users to insert")
        return None

    print(f"\n👤 Transforming user data...")
    transformed = transform_user(users_data)
    print(f"   User: {transformed['name']}")

    print(f"📤 Inserting user into MongoDB...")
    result = await collection.insert_one(transformed)
    print(f"✅ Inserted user with ID: {result.inserted_id}")

    return transformed


def get_mongo_uri_display(uri: str | None) -> str:
    """Get a safe display version of the connection string"""
    if not uri or "://" not in uri:
        return uri or "NOT SET"
    try:
        # Dynamically preserve the scheme (e.g., mongodb:// or mongodb+srv://)
        scheme, parts = uri.split("://", 1)
        if "@" in parts:
            _, host_part = parts.split("@", 1)
            return f"{scheme}://***@{host_part}"
        return f"{scheme}://{parts}"
    except (IndexError, ValueError):
        return uri


async def main() -> bool:
    print("=" * 60)
    print("DATABASE SEEDING")
    print("=" * 60)

    if not MONGO_URI:
        print("❌ MONGO_URI not set")
        print("   Set MONGODB_URL environment variable")
        return False

    print(f"\n🔌 Connecting to MongoDB: {get_mongo_uri_display(MONGO_URI)}...")

    client = AsyncMongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        # Test connection
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\n📝 Make sure MongoDB is running:")
        print("   Local: brew services start mongodb-community")
        print("   Atlas: Set MONGO_URI environment variable")
        return False

    db = client[DB_NAME]

    try:
        # Load JSON files
        test_dir = Path(__file__).parent.parent / "test"
        restaurants_raw = await load_json_file(test_dir / "restaurants.json")
        users_raw = await load_json_file(test_dir / "users.json")

        # Type check and ensure correct types
        if isinstance(restaurants_raw, dict):
            restaurants_data = [restaurants_raw]
        else:
            restaurants_data = restaurants_raw

        # Handle users data - take first item if list
        users_data: dict = users_raw if isinstance(users_raw, dict) else (users_raw[0] if isinstance(users_raw, list) and users_raw else {})

        # Clear existing data
        print("\n🗑️  Clearing existing collections...")
        await db[RESTAURANTS_COLLECTION].delete_many({})
        print(f"   Cleared {RESTAURANTS_COLLECTION}")
        await db[USERS_COLLECTION].delete_many({})
        print(f"   Cleared {USERS_COLLECTION}")

        # Seed data
        await seed_restaurants(db[RESTAURANTS_COLLECTION], restaurants_data)
        await seed_users(db[USERS_COLLECTION], users_data)

        # Verify
        print("\n✨ Verifying data...")
        restaurant_count = await db[RESTAURANTS_COLLECTION].count_documents({})
        user_count = await db[USERS_COLLECTION].count_documents({})
        print(f"   Restaurants in DB: {restaurant_count}")
        print(f"   Users in DB: {user_count}")

        print("\n" + "=" * 60)
        print("✅ Database seeding completed successfully!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)