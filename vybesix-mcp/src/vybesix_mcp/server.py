"""MCP Server for Vybesix Restaurant Discovery API using FastMCP."""

import os
import json
import httpx
from typing import Any
from fastmcp import FastMCP
from pydantic import BaseModel, Field


# Request Models
class RestaurantSearchRequest(BaseModel):
    """Manual restaurant search request."""
    userID: str | None = None
    latitude: float
    longitude: float
    radius_km: int = 5
    meal_types: list[str] = Field(default_factory=list)
    cuisine: list[str] = Field(default_factory=list)
    dietary: list[str] = Field(default_factory=list)
    price_max: int | None = None
    min_rating: float = 0.0
    min_capacity: int = 1
    has_live_music: bool = False
    has_parking: bool = False


class RestaurantVectorSearchRequest(BaseModel):
    """Vector-based semantic search request."""
    query: str
    restaurant_ids: list[str]
    limit: int = 10
    num_candidates: int = 100


class FoodSearchRequest(BaseModel):
    """Manual food search request."""
    restaurant_ids: list[str]
    query: str = None
    dietary: list[str] = None
    allergens: list[str] = None
    category: str = None
    cuisine: list[str] = None
    meal_types: list[str] = None
    price: int = None
    spice_level: int = None
    max_prep_time: int = None
    limit: int = 10
    offset: int = 0


class FoodVectorSearchRequest(BaseModel):
    """Vector-based semantic food search request."""
    query: str
    restaurant_ids: list[str] = None
    limit: int = 10
    num_candidates: int = 100


# Initialize FastMCP Server
mcp = FastMCP("vybesix-mcp")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@mcp.tool()
async def search_restaurants_manual(
    latitude: float,
    longitude: float,
    radius_km: int = 5,
    meal_types: list[str] = None,
    cuisine: list[str] = None,
    dietary: list[str] = None,
    price_max: int = None,
    min_rating: float = 0.0,
    min_capacity: int = 1,
    has_parking: bool = False,
    has_live_music: bool = False,
    userID: str = None,
) -> str:
    """
    Search restaurants using manual filtering based on location and preferences.

    Use this for structured queries with specific location and preferences.

    Args:
        latitude: User's latitude
        longitude: User's longitude
        radius_km: Search radius in kilometers (default: 5)
        meal_types: List of meal types (e.g., breakfast, lunch, dinner)
        cuisine: List of cuisines (e.g., italian, vegan, mexican)
        dietary: Dietary restrictions (e.g., vegan, gluten-free, halal)
        price_max: Maximum price level (1-4)
        min_rating: Minimum rating (0-5, default: 0.0)
        min_capacity: Minimum seating capacity (default: 1)
        has_parking: Must have parking (default: false)
        has_live_music: Must have live music (default: false)
        userID: User ID for preference injection (optional)

    Returns:
        JSON with search results and metadata
    """
    try:
        # Build request
        request_data = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "meal_types": meal_types or [],
            "cuisine": cuisine or [],
            "dietary": dietary or [],
            "min_rating": min_rating,
            "min_capacity": min_capacity,
            "has_parking": has_parking,
            "has_live_music": has_live_music,
        }
        if price_max is not None:
            request_data["price_max"] = price_max
        if userID is not None:
            request_data["userID"] = userID

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/restaurants/search",
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()

            results = response.json()
            return json.dumps({
                "success": True,
                "count": len(results),
                "results": results
            }, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({
            "success": False,
            "error": f"API Error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Validation or request error: {str(e)}"
        })


@mcp.tool()
async def search_restaurants_vector(
    query: str,
    restaurant_ids: list[str],
    limit: int = 10,
    num_candidates: int = 100,
) -> str:
    """
    Search restaurants using semantic AI-powered search.

    Use this for natural language queries that describe dining preferences,
    atmosphere, or complex requirements.

    Args:
        query: Natural language search query (e.g., 'cozy vegan restaurant with live music')
        restaurant_ids: List of restaurant IDs to search within
        limit: Number of results to return (default: 10)
        num_candidates: Number of candidates to rerank (default: 100)

    Returns:
        JSON with ranked search results by semantic relevance
    """
    try:
        request_data = {
            "query": query,
            "restaurant_ids": restaurant_ids,
            "limit": limit,
            "num_candidates": num_candidates,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/restaurants/vector-search",
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()

            results = response.json()
            return json.dumps({
                "success": True,
                "count": len(results),
                "results": results
            }, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({
            "success": False,
            "error": f"API Error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Validation or request error: {str(e)}"
        })


@mcp.tool()
async def search_food_manual(
    restaurant_ids: list[str],
    query: str = None,
    dietary: list[str] = None,
    allergens: list[str] = None,
    category: str = None,
    cuisine: list[str] = None,
    meal_types: list[str] = None,
    price: int = None,
    spice_level: int = None,
    max_prep_time: int = None,
    limit: int = 10,
    offset: int = 0,
) -> str:
    """
    Search food items using manual filtering based on dietary, allergens, and preferences.

    Use this for structured queries with specific filters.

    Args:
        restaurant_ids: List of restaurant IDs to search within
        query: Keyword search in food name/description (optional)
        dietary: Dietary tags (e.g., ["vegan", "gluten-free"])
        allergens: Allergens to exclude (e.g., ["peanuts", "shellfish"])
        category: Food category (e.g., "main_course", "dessert")
        cuisine: Cuisine types (e.g., ["asian", "italian"])
        meal_types: Meal types (e.g., ["breakfast", "dinner"])
        price: Maximum price level
        spice_level: Spice level (0-5)
        max_prep_time: Maximum preparation time in minutes
        limit: Results per page (default: 10)
        offset: Pagination offset (default: 0)

    Returns:
        JSON with search results and metadata
    """
    try:
        # Build request
        request_data = {
            "restaurant_ids": restaurant_ids,
            "limit": limit,
            "offset": offset,
        }
        if query is not None:
            request_data["query"] = query
        if dietary:
            request_data["dietary"] = dietary
        if allergens:
            request_data["allergens"] = allergens
        if category is not None:
            request_data["category"] = category
        if cuisine:
            request_data["cuisine"] = cuisine
        if meal_types:
            request_data["meal_types"] = meal_types
        if price is not None:
            request_data["price"] = price
        if spice_level is not None:
            request_data["spice_level"] = spice_level
        if max_prep_time is not None:
            request_data["max_prep_time"] = max_prep_time

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/food/search",
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()

            results = response.json()
            return json.dumps({
                "success": True,
                "count": len(results),
                "results": results
            }, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({
            "success": False,
            "error": f"API Error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Validation or request error: {str(e)}"
        })


@mcp.tool()
async def search_food_vector(
    query: str,
    restaurant_ids: list[str] = None,
    limit: int = 10,
    num_candidates: int = 100,
) -> str:
    """
    Search food items using semantic AI-powered search.

    Use this for natural language queries that describe food preferences,
    taste profiles, or complex requirements.

    Args:
        query: Natural language search query (e.g., 'spicy vegetarian appetizer')
        restaurant_ids: List of restaurant IDs to search within (optional)
        limit: Number of results to return (default: 10)
        num_candidates: Number of candidates to rerank (default: 100)

    Returns:
        JSON with ranked search results by semantic relevance
    """
    try:
        request_data = {
            "query": query,
            "limit": limit,
            "num_candidates": num_candidates,
        }
        if restaurant_ids:
            request_data["restaurant_ids"] = restaurant_ids

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/food/vector-search",
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()

            results = response.json()
            return json.dumps({
                "success": True,
                "count": len(results),
                "results": results
            }, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({
            "success": False,
            "error": f"API Error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Validation or request error: {str(e)}"
        })