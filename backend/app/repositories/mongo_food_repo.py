"""MongoDB implementation of food item repository with filtering and vector search."""

from typing import List, Optional
from app.model.food.models import FoodItemEntity, FoodSearchResult


class MongoFoodRepository:
    """MongoDB repository for food items with filtering and vector search."""

    def __init__(self, collection):
        """Initialize with MongoDB food collection."""
        self.collection = collection

    async def filter_food(
        self,
        restaurant_ids: List[str] = None,
        query: Optional[str] = None,
        dietary: List[str] = None,
        allergens: List[str] = None,
        category: Optional[str] = None,
        cuisine: List[str] = None,
        meal_types: List[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        spice_level: Optional[int] = None,
        max_prep_time: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[FoodSearchResult]:
        """
        Execute MongoDB aggregation pipeline for manual food search.

        Pipeline stages:
        1. $match: Filter by restaurant_ids, dietary, allergens, category, cuisine, price, spice
        2. $addFields: Calculate match_score (dietary matches, allergen avoidance)
        3. $sort: Sort by match_score DESC, price ASC
        4. $skip/$limit: Pagination
        """
        dietary = dietary or []
        allergens = allergens or []
        cuisine = cuisine or []
        meal_types = meal_types or []
        restaurant_ids = restaurant_ids or []

        # Build match filters
        match_filters = {}

        # Filter by restaurant_ids if provided
        if restaurant_ids:
            match_filters["restaurant_id"] = {"$in": restaurant_ids}

        # Keyword search in name and description
        if query:
            match_filters["$text"] = {"$search": query}

        # Dietary restrictions (must match at least one)
        if dietary:
            match_filters["dietary"] = {"$in": dietary}

        # Allergen exclusion (must NOT contain any allergen)
        if allergens:
            match_filters["allergens"] = {"$nin": allergens}

        # Category filter
        if category:
            match_filters["category"] = category

        # Cuisine filter
        if cuisine:
            match_filters["cuisine"] = {"$in": cuisine}

        # Meal types filter
        if meal_types:
            match_filters["meal_types"] = {"$in": meal_types}

        # Price range filter
        price_filters = {}
        if max_price is not None:
            price_filters["$lte"] = max_price
        if min_price is not None:
            price_filters["$gte"] = min_price
        if price_filters:
            match_filters["price"] = price_filters

        # Spice level filter (exact or minimum)
        if spice_level is not None:
            match_filters["spice_level"] = {"$gte": spice_level}

        # Prep time filter (maximum)
        if max_prep_time is not None:
            match_filters["prep_time_minutes"] = {"$lte": max_prep_time}

        # Build aggregation pipeline
        pipeline = []

        # Stage 1: $match - Apply all filters
        if match_filters:
            pipeline.append({"$match": match_filters})

        # Stage 2: $addFields - Calculate match_score
        # Score based on:
        # - Exact dietary matches: +2 per match
        # - Allergen avoidance: +1 for avoiding allergens (implicit in $match)
        # - Is signature dish: +1
        # - Is popular: +0.5
        pipeline.append({
            "$addFields": {
                "match_score": {
                    "$add": [
                        # Count dietary matches
                        {
                            "$size": {
                                "$filter": {
                                    "input": "$dietary",
                                    "as": "d",
                                    "cond": {"$in": ["$$d", dietary]}
                                }
                            }
                        } if dietary else 0,
                        # Signature dish bonus
                        {"$cond": ["$is_signature_dish", 1, 0]},
                        # Popular dish bonus
                        {"$cond": ["$is_popular", 0.5, 0]},
                    ]
                }
            }
        })

        # Stage 3: $sort - By match_score DESC, price ASC
        pipeline.append({
            "$sort": {
                "match_score": -1,
                "price": 1
            }
        })

        # Stage 4: $skip/$limit - Pagination
        pipeline.append({"$skip": offset})
        pipeline.append({"$limit": limit})

        # Execute pipeline
        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(limit)

        # Convert to FoodSearchResult objects
        food_results = []
        for doc in results:
            entity = FoodItemEntity(**doc)
            match_score = doc.get("match_score", 0.0)
            result = FoodSearchResult(entity=entity, match_score=match_score)
            food_results.append(result)

        return food_results

    async def vector_search_by_ids(
        self,
        restaurant_ids: List[str],
        query_embedding: List[float],
        limit: int = 10,
        num_candidates: int = 100,
        allergens_to_exclude: List[str] = None,
    ) -> List[FoodSearchResult]:
        """
        Execute MongoDB $vectorSearch with hard allergen safety filtering.

        CRITICAL: Applies allergen exclusion filter WITHIN vector search (not after).
        Items containing excluded allergens are dropped at the database level.

        Args:
            restaurant_ids: List of restaurant IDs to search within
            query_embedding: OpenAI embedding of the food query
            limit: Number of final results to return
            num_candidates: Number of candidates to consider for reranking
            allergens_to_exclude: CRITICAL - items containing ANY of these allergens are EXCLUDED
                                 Applied as $nin filter inside $vectorSearch

        Pipeline stages:
        1. $vectorSearch: Vector search with hard filters (restaurant_id + allergen $nin)
        2. $project: Include similarity score and all fields
        """
        allergens_to_exclude = allergens_to_exclude or []

        # Build vector search filter - applies BEFORE vector search at database level
        vector_filter = {
            "restaurant_id": {"$in": restaurant_ids}
        }

        # CRITICAL: Add allergen exclusion to the filter
        # $nin blocks any items containing these allergens
        if allergens_to_exclude:
            vector_filter["allergens"] = {"$nin": allergens_to_exclude}

        # Build aggregation pipeline for vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "food_vector_index",
                    "path": "vector_embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": num_candidates,
                    "limit": limit,
                    "filter": vector_filter
                }
            },
            {
                "$project": {
                    "similarity_score": {"$meta": "vectorSearchScore"},
                    # Include all fields
                    "food_id": 1,
                    "restaurant_id": 1,
                    "name": 1,
                    "description": 1,
                    "category": 1,
                    "cuisine": 1,
                    "dietary": 1,
                    "allergens": 1,
                    "ingredients": 1,
                    "spice_level": 1,
                    "preparation_method": 1,
                    "meal_types": 1,
                    "price": 1,
                    "calories": 1,
                    "vegetarian_friendly": 1,
                    "vegan_friendly": 1,
                    "gluten_free": 1,
                    "is_signature_dish": 1,
                    "is_popular": 1,
                    "rating": 1,
                    "popularity_score": 1,
                    "ai_metadata": 1,
                    "vector_embeddings": 1,
                    "embedding_model": 1,
                    "embedding_dimensions": 1,
                    "embedding_source": 1,
                    "embedding_timestamp": 1,
                }
            }
        ]

        # Execute pipeline
        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(limit)

        # Convert to FoodSearchResult objects
        food_results = []
        for doc in results:
            entity = FoodItemEntity(**{k: v for k, v in doc.items() if k != "similarity_score"})
            # Use similarity_score as match_score for vector search
            similarity = doc.get("similarity_score", 0.0)
            result = FoodSearchResult(entity=entity, match_score=similarity)
            food_results.append(result)

        return food_results

    async def get_by_id(self, food_id: str) -> Optional[FoodItemEntity]:
        """Fetch a single food item by ID."""
        doc = await self.collection.find_one({"food_id": food_id})
        if doc:
            return FoodItemEntity(**doc)
        return None

    async def get_by_restaurant(self, restaurant_id: str) -> List[FoodItemEntity]:
        """Fetch all food items for a restaurant."""
        docs = await self.collection.find({"restaurant_id": restaurant_id}).to_list(None)
        return [FoodItemEntity(**doc) for doc in docs]
