"""
Food Service Layer: CRUD operations for food items.

Customer-facing read-only operations:
- Search food with filters (dietary, allergens, cuisine, etc.)
- Get single food item by ID
- Get all food items for a restaurant
"""

from typing import List, Optional
import logging
from app.model.food.models import (
    FoodSearchRequest,
    FoodSearchResponse,
)
from app.repositories.mongo_food_repo import MongoFoodRepository

logger = logging.getLogger(__name__)


class FoodService:
    """Service layer for food CRUD operations (customer-facing read-only)."""

    def __init__(self, food_repository: MongoFoodRepository):
        """
        Initialize with dependency-injected repository.

        Args:
            food_repository: MongoDB food repository implementation
        """
        self.food_repo = food_repository

    # ========================================================================
    # FOOD SEARCH (Filtering)
    # ========================================================================

    async def search_food(
        self,
        request: FoodSearchRequest,
    ) -> List[FoodSearchResponse]:
        """
        Execute food search with manual filtering.

        Filters available:
        - restaurant_ids: Filter to specific restaurants
        - dietary: Dietary restrictions (vegan, vegetarian, gluten-free, halal)
        - allergens: Allergen exclusions (peanuts, shellfish, dairy, etc.)
        - category: Food category (main_course, appetizer, dessert, beverage)
        - cuisine: Cuisine types (asian, italian, indian, etc.)
        - meal_types: Meal types (breakfast, lunch, dinner, late night)
        - spice_level: Spice level (0-5)
        - price: Maximum price
        - max_prep_time: Maximum prep time in minutes
        - query: Keyword search in name/description

        Args:
            request: FoodSearchRequest with filters

        Returns:
            List of FoodSearchResponse objects ranked by match_score
        """
        logger.info(
            f"🔍 Food search: dietary={request.dietary}, "
            f"allergens={request.allergens}, restaurants={len(request.restaurant_ids)}"
        )

        # Call repository with normalized filters
        results = await self.food_repo.filter_food(
            restaurant_ids=request.restaurant_ids or [],
            query=request.query,
            dietary=request.dietary or [],
            allergens=request.allergens or [],
            category=request.category,
            cuisine=request.cuisine or [],
            meal_types=request.meal_types or [],
            max_price=request.price,
            spice_level=request.spice_level,
            max_prep_time=request.max_prep_time,
            limit=request.limit,
            offset=request.offset,
        )

        logger.info(f"✅ Found {len(results)} food items")

        # Convert results to response format
        responses = [
            FoodSearchResponse.from_entity(
                result.entity,
                match_score=result.match_score,
                rerank_score=result.rerank_score
            )
            for result in results
        ]

        return responses

    # ========================================================================
    # FOOD RETRIEVAL
    # ========================================================================

    async def get_food_by_id(self, food_id: str) -> Optional[FoodSearchResponse]:
        """
        Get a single food item by ID.

        Args:
            food_id: Food ID to fetch

        Returns:
            FoodSearchResponse or None if not found
        """
        logger.debug(f"Fetching food: {food_id}")
        entity = await self.food_repo.get_by_id(food_id)
        if entity:
            return FoodSearchResponse.from_entity(entity)
        return None

    async def get_restaurant_food(
        self,
        restaurant_id: str,
        limit: int = 100,
    ) -> List[FoodSearchResponse]:
        """
        Get all food items for a restaurant.

        Args:
            restaurant_id: Restaurant ID to fetch items for
            limit: Maximum items to return (default: 100)

        Returns:
            List of FoodSearchResponse objects
        """
        logger.debug(f"Fetching all food for restaurant: {restaurant_id}")
        entities = await self.food_repo.get_by_restaurant(restaurant_id)

        # Apply limit
        entities = entities[:limit]

        return [FoodSearchResponse.from_entity(entity) for entity in entities]

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate_search_request(self, request: FoodSearchRequest) -> bool:
        """
        Validate food search request.

        Args:
            request: FoodSearchRequest to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        # Validate limit
        if not (1 <= request.limit <= 100):
            raise ValueError(f"Invalid limit: {request.limit}, must be between 1 and 100")

        # Validate offset
        if request.offset < 0:
            raise ValueError(f"Invalid offset: {request.offset}, must be >= 0")

        # Validate price
        if request.price is not None and request.price < 0:
            raise ValueError(f"Invalid price: {request.price}, must be >= 0")

        # Validate spice level
        if request.spice_level is not None and not (0 <= request.spice_level <= 5):
            raise ValueError(f"Invalid spice_level: {request.spice_level}, must be 0-5")

        return True