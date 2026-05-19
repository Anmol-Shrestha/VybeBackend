"""Integration tests for RestaurantService with preference injection."""

import os
import pytest
from pymongo import AsyncMongoClient
from app.services.restaurant_service import RestaurantService
from app.repositories.mongo_user_repo import MongoUserRepository
from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository
from app.model.restaurants.models import RestaurantSearchRequest


@pytest.mark.asyncio
async def test_restaurant_search_with_preference_injection():
    """
    Test that an incomplete search request (missing dietary)
    triggers preference injection from UserRepository.

    User: Mr. Vegan (ID: 123123, dietary: "vegan")
    Search location: Scarborough (43.77579, -79.20664)
    Radius: 10km

    Expected results:
    - Vegan Kitchen (Toronto, has vegan)
    - Purely Vegan Hub (Scarborough, vegan-only)

    Should exclude:
    - The Green Leaf Bistro (vegetarian only, not vegan)
    - Standard Grill & Bar (regular only)
    - Sultan's Halal Kitchen (halal only)
    - The Kosher Deli (kosher only)
    """
    # Initialize MongoDB connection
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "vybe")

    client = AsyncMongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    db = client[database_name]

    # Instantiate repositories with collections
    user_repo = MongoUserRepository(db["users"])
    restaurant_repo = MongoRestaurantRepository(db["restaurants"])
    service = RestaurantService(restaurant_repo, user_repo)

    # Create an incomplete search request (dietary is empty)
    # Increased radius to 25km to include both vegan restaurants
    request = RestaurantSearchRequest(
        userID="user_123123",
        latitude=43.77579,
        longitude=-79.20664,
        radius_km=25,
        dietary=[],
        has_parking=False,
        has_live_music=False,
    )

    # Execute search
    results = await service.get_filtered_restaurants(request, bypass_hours=True)

    # Assertions
    assert len(results) > 0, "Expected to find restaurants with vegan dietary"

    restaurant_names = {r.name for r in results}

    # Should include both vegan restaurants
    assert "Vegan Kitchen" in restaurant_names, "Should find Vegan Kitchen (has vegan dietary)"
    assert (
        "Purely Vegan Hub" in restaurant_names
    ), "Should find Purely Vegan Hub (vegan-only)"

    # Verify non-vegan restaurants are excluded
    assert (
        "The Green Leaf Bistro" not in restaurant_names
    ), "Should exclude The Green Leaf Bistro (vegetarian only)"
    assert (
        "Standard Grill & Bar" not in restaurant_names
    ), "Should exclude Standard Grill & Bar (regular only)"
    assert (
        "Sultan's Halal Kitchen" not in restaurant_names
    ), "Should exclude Sultan's Halal Kitchen (halal only)"
    assert (
        "The Kosher Deli" not in restaurant_names
    ), "Should exclude The Kosher Deli (kosher only)"

    # Verify we got the dietary requirement in the results
    for result in results:
        assert "vegan" in result.dietary, f"{result.name} should have vegan in dietary"

    # Cleanup
    await client.close()
