"""Test HybridSearchService with real OpenAI embeddings and MongoDB vector search."""

import os
from openai import AsyncOpenAI
import pytest
from app.services.hybrid_search_service import HybridSearchService
from app.services.restaurant_search_service import RestaurantSearchService
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.restaurant_reranker import RestaurantRerankerAdapter
from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository


@pytest.fixture
async def setup_hybrid_search(mongo_restaurant_collection):
    """Set up HybridSearchService with real dependencies."""
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embedding_adapter = OpenAIEmbeddingAdapter(client=openai_client, model="text-embedding-3-small")
    restaurant_repo = MongoRestaurantRepository(mongo_restaurant_collection)
    reranker_adapter = RestaurantRerankerAdapter()

    hybrid_search = HybridSearchService(
        embedding_adapter=embedding_adapter,
        vector_repository=restaurant_repo,
        reranker_adapter=reranker_adapter,
    )

    return hybrid_search


@pytest.mark.asyncio
async def test_hybrid_search_service_vegan_query(setup_hybrid_search):
    """Test HybridSearchService with a vegan restaurant query."""
    hybrid_search = setup_hybrid_search

    # Use some restaurant IDs from the seeded data
    restaurant_ids = [
        "vegan_hub_1",
        "vegan_diner_24hr",
        "mixed_cuisine_1",
        "seafood_place_1",
    ]

    results = await hybrid_search.search(
        query="looking for vegan restaurants",
        entity_ids=restaurant_ids,
        limit=5,
        num_candidates=10,
    )

    assert len(results) > 0
    assert len(results) <= 5
    assert all("name" in r or "score" in r for r in results)
    print(f"✅ Vegan query returned {len(results)} results")


@pytest.mark.asyncio
async def test_restaurant_search_service_facade(setup_hybrid_search):
    """Test RestaurantSearchService facade composition."""
    hybrid_search = setup_hybrid_search
    restaurant_search = RestaurantSearchService(hybrid_search=hybrid_search)

    restaurant_ids = [
        "vegan_hub_1",
        "vegan_diner_24hr",
        "mixed_cuisine_1",
    ]

    results = await restaurant_search.search(
        query="late night dining",
        restaurant_ids=restaurant_ids,
        limit=3,
    )

    assert len(results) > 0
    assert len(results) <= 3
    print(f"✅ RestaurantSearchService facade works: {len(results)} results")


@pytest.mark.asyncio
async def test_hybrid_search_diverse_queries(setup_hybrid_search):
    """Test HybridSearchService with various query types."""
    hybrid_search = setup_hybrid_search

    restaurant_ids = [
        "vegan_hub_1",
        "vegan_diner_24hr",
        "mixed_cuisine_1",
        "seafood_place_1",
        "italian_restaurant_1",
    ]

    queries = [
        "gluten-free options",
        "date night atmosphere",
        "family-friendly",
        "open late",
    ]

    for query in queries:
        results = await hybrid_search.search(
            query=query,
            entity_ids=restaurant_ids,
            limit=3,
        )
        assert isinstance(results, list)
        print(f"✅ Query '{query}': {len(results)} results")
