"""V1 Food Search API endpoints."""

import os
from fastapi import APIRouter, HTTPException, Depends, Request
from openai import AsyncOpenAI

from app.model.food.models import (
    FoodSearchRequest,
    FoodSearchResponse,
    FoodVectorSearchRequest,
)
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.food_reranker import FoodReranker
from app.services.hybrid_search_service import HybridSearchService
from app.services.food_service import FoodService
from app.services.food_hybrid_search_service import FoodHybridSearchService

router = APIRouter(prefix="/api/v1/food", tags=["food"])


async def get_food_service(req: Request):
    """Dependency injection for manual food search service."""
    return req.app.food_service


async def get_food_vector_search_service(req: Request):
    """Dependency injection for food vector search service."""
    if not hasattr(req.app, 'food_vector_search_service'):
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        embedding_adapter = OpenAIEmbeddingAdapter(client=openai_client, model="text-embedding-3-small")
        food_repo = req.app.food_repo
        reranker_adapter = FoodReranker()

        hybrid_search = HybridSearchService(
            embedding_adapter=embedding_adapter,
            vector_repository=food_repo,
            reranker_adapter=reranker_adapter,
        )
        req.app.food_vector_search_service = FoodHybridSearchService(hybrid_search=hybrid_search)

    return req.app.food_vector_search_service


@router.post("/search", response_model=list[FoodSearchResponse])
async def search_food_manual(
    search_request: FoodSearchRequest,
    service=Depends(get_food_service),
) -> list[FoodSearchResponse]:
    """
    Manual food search based on dietary, allergens, and preferences.

    Request body:
    - restaurant_ids: Filter to specific restaurants
    - query (optional): Keyword search in name/description
    - dietary (optional): Dietary tags (e.g., ["vegan", "gluten-free"])
    - allergens (optional): Items to exclude (e.g., ["peanuts", "shellfish"])
    - category (optional): Food category (e.g., "main_course", "dessert")
    - cuisine (optional): Cuisine types (e.g., ["asian", "italian"])
    - meal_types (optional): Meal types (e.g., ["breakfast", "dinner"])
    - price (optional): Maximum price
    - spice_level (optional): Spice level (0-5)
    - max_prep_time (optional): Maximum prep time in minutes
    - limit (default: 10): Results per page
    - offset (default: 0): Pagination offset

    Returns: List of food items sorted by match score
    """
    try:
        results = await service.search_food(search_request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector-search", response_model=list[FoodSearchResponse])
async def search_food_vector(
    request: FoodVectorSearchRequest,
    service=Depends(get_food_vector_search_service),
) -> list[FoodSearchResponse]:
    """
    Vector-based semantic food search with AI-powered ranking.

    Uses OpenAI embeddings + cross-encoder reranking for intelligent discovery.

    Request body:
    - query: Natural language search query (e.g., "spicy vegetarian appetizer")
    - restaurant_ids (optional): Pre-filter to specific restaurants
    - limit: Number of final results to return (default: 10)
    - num_candidates: Number of candidates to rerank (default: 100)

    Returns: List of food items ranked by semantic relevance and reranking score.
    Only includes results with rerank_score >= -2.0 to filter out poor matches.
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