"""
Transforms test data from JSON and seeds MongoDB with restaurants and users.

Handles:
- Location: Converts lat/long to GeoJSON Point format
- Service Hours: Converts time strings to "Minutes from Midnight"
- Booleans: Ensures native boolean types
- Creates required 2dsphere index
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
import os
from pymongo import GEOSPHERE, AsyncMongoClient

# MongoDB connection string (update as needed)
MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME", "vybe")
RESTAURANTS_COLLECTION = "restaurants"
USERS_COLLECTION = "users"


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


async def seed_restaurants(collection, restaurants_data: list) -> list | None:
    """Insert restaurants and create geospatial index"""
    if not restaurants_data:
        print("⚠️  No restaurants to insert")
        return None

    print(f"\n📝 Transforming {len(restaurants_data)} restaurants...")
    transformed = [transform_restaurant(r, i) for i, r in enumerate(restaurants_data, 1)]

    print(f"📤 Inserting {len(transformed)} restaurants into MongoDB...")
    result = await collection.insert_many(transformed)
    print(f"✅ Inserted {len(result.inserted_ids)} restaurants")

    # Create 2dsphere index
    print("📍 Creating geospatial index...")
    await collection.create_index([("location", GEOSPHERE)])
    print("✅ Geospatial index created")

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


def get_mongo_uri_display(uri: str) -> str:
    """Get a safe display version of the connection string"""
    if "://" not in uri:
        return uri
    try:
        # Dynamically preserve the scheme (e.g., mongodb:// or mongodb+srv://)
        scheme, parts = uri.split("://", 1)
        if "@" in parts:
            _, host_part = parts.split("@", 1)
            return f"{scheme}://***@{host_part}"
        return f"{scheme}://{parts}"
    except (IndexError, ValueError):
        return uri  # Restored to safely return the fallback string


async def main() -> bool:
    print("=" * 60)
    print("DATABASE SEEDING")
    print("=" * 60)
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

        users_data = users_raw if isinstance(users_raw, dict) else users_raw

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