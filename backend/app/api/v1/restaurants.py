"""V1 Restaurant Search API endpoints."""

import os
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from openai import AsyncOpenAI

from app.model.restaurants.models import (
    RestaurantSearchRequest,
    RestaurantsSearchResponse,
    RestaurantVectorSearchRequest,
)
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.restaurant_reranker import RestaurantRerankerAdapter
from app.services.hybrid_search_service import HybridSearchService
from app.services.restaurant_search_service import RestaurantSearchService

router = APIRouter(prefix="/api/v1/restaurants", tags=["restaurants"])


async def get_restaurant_service(req: Request):
    """Dependency injection for manual search service."""
    return req.app.restaurant_service


async def get_vector_search_service(req: Request):
    """Dependency injection for vector search service."""
    if not hasattr(req.app, 'vector_search_service'):
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        embedding_adapter = OpenAIEmbeddingAdapter(client=openai_client, model="text-embedding-3-small")
        restaurant_repo = req.app.restaurant_repo
        reranker_adapter = RestaurantRerankerAdapter()

        hybrid_search = HybridSearchService(
            embedding_adapter=embedding_adapter,
            vector_repository=restaurant_repo,
            reranker_adapter=reranker_adapter,
        )
        req.app.vector_search_service = RestaurantSearchService(hybrid_search=hybrid_search)

    return req.app.vector_search_service


@router.post("/search", response_model=list[RestaurantsSearchResponse])
async def search_restaurants_manual(
    search_request: RestaurantSearchRequest,
    bypass_hours: bool = Query(False, description="Skip service hours check for testing"),
    service=Depends(get_restaurant_service),
) -> list[RestaurantsSearchResponse]:
    """
    Manual restaurant search based on location and preferences.

    Request body:
    - userID (optional): User ID for preference injection
    - latitude: User's latitude
    - longitude: User's longitude
    - radius_km: Search radius in km (default: 5)
    - meal_types (optional): List of meal types (e.g., ["breakfast", "lunch"])
    - cuisine (optional): List of cuisines (e.g., ["italian", "vegan"])
    - dietary (optional): Dietary restrictions (e.g., ["vegan"])
    - price_max (optional): Maximum price level (1-4)
    - min_rating (optional): Minimum rating (default: 0.0)
    - min_capacity (optional): Minimum capacity (default: 1)
    - has_parking (optional): Must have parking
    - has_live_music (optional): Must have live music

    Returns: List of restaurants sorted by match score and distance
    """
    try:
        results = await service.get_filtered_restaurants(search_request, bypass_hours=bypass_hours)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector-search", response_model=list[RestaurantsSearchResponse])
async def search_restaurants_vector(
    request: RestaurantVectorSearchRequest,
    service=Depends(get_vector_search_service),
) -> list[RestaurantsSearchResponse]:
    """
    Vector-based semantic restaurant search with AI-powered ranking.

    Uses OpenAI embeddings + cross-encoder reranking for intelligent discovery.

    Request body:
    - query: Natural language search query (e.g., "looking for vegan restaurants")
    - restaurant_ids: List of restaurant IDs to search within (pre-filtered results)
    - limit: Number of final results to return (default: 10)
    - num_candidates: Number of candidates to rerank (default: 100)

    Returns: List of restaurants ranked by semantic relevance and reranking score
    """
    try:
        results = await service.search(
            query=request.query,
            restaurant_ids=request.restaurant_ids,
            limit=request.limit,
            num_candidates=request.num_candidates,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))