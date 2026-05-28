"""
Integration tests for Food Hybrid Search Service.

Tests the complete end-to-end semantic search pipeline:
1. Real OpenAI embeddings (text-embedding-3-small)
2. Real MongoDB vector search with restaurant ID filtering
3. Real cross-encoder reranking
4. Score-based filtering and result ranking

Uses actual seeded food data from MongoDB Atlas.
"""

import pytest
import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from openai import AsyncOpenAI
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.restaurant_reranker import RestaurantRerankerAdapter
from app.services.hybrid_search_service import HybridSearchService
from app.services.food_hybrid_search_service import FoodHybridSearchService
from app.repositories.mongo_food_repo import MongoFoodRepository
from app.model.food.models import FoodSearchResponse

load_dotenv()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def mongodb_url():
    """Get MongoDB connection URL from environment."""
    url = os.getenv("MONGODB_URL")
    assert url, "MONGODB_URL environment variable not set"
    return url


@pytest.fixture(scope="session")
def database_name():
    """Get database name from environment."""
    return os.getenv("DATABASE_NAME", "vybe")


@pytest.fixture
async def mongodb_client(mongodb_url):
    """Create MongoDB async client."""
    client = AsyncMongoClient(mongodb_url)
    try:
        # Test connection
        await client.admin.command("ping")
        print("✅ MongoDB connected")
        yield client
    finally:
        await client.close()


@pytest.fixture
async def mongo_food_collection(mongodb_client, database_name):
    """Get MongoDB food collection."""
    db = mongodb_client[database_name]
    return db["food"]


@pytest.fixture
async def setup_food_hybrid_search(mongo_food_collection):
    """Set up FoodHybridSearchService with real dependencies."""
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embedding_adapter = OpenAIEmbeddingAdapter(client=openai_client, model="text-embedding-3-small")
    food_repo = MongoFoodRepository(mongo_food_collection)
    reranker_adapter = RestaurantRerankerAdapter()

    hybrid_search = HybridSearchService(
        embedding_adapter=embedding_adapter,
        vector_repository=food_repo,
        reranker_adapter=reranker_adapter,
    )

    food_hybrid_service = FoodHybridSearchService(
        hybrid_search=hybrid_search,
        rerank_score_threshold=-2.0
    )

    return food_hybrid_service, food_repo


# ============================================================================
# BASIC SEMANTIC SEARCH TESTS
# ============================================================================

class TestFoodHybridSearchIntegration:
    """Integration tests for food hybrid search with real data."""

    @pytest.mark.asyncio
    async def test_search_vegan_dumplings(self, setup_food_hybrid_search):
        """Test semantic search for vegan dumplings in seeded data."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        # Get available restaurant IDs
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        assert len(restaurant_ids) > 0, "No restaurants found in database"

        query = "vegan dumplings"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=50
        )

        # Should find at least one vegan dumpling
        assert len(results) > 0, f"No results found for '{query}'"
        assert all(isinstance(r, FoodSearchResponse) for r in results)

        # Top result should be relevant to dumplings
        top_result = results[0]
        assert top_result.match_score > 0.0
        assert top_result.rerank_score is not None
        print(f"✅ Found: {top_result.name} (score: {top_result.rerank_score:.2f})")

    @pytest.mark.asyncio
    async def test_search_crispy_fried_chicken(self, setup_food_hybrid_search):
        """Test semantic search for crispy fried chicken."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "crispy fried chicken"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=50
        )

        assert len(results) > 0, f"No results found for '{query}'"
        top_result = results[0]
        assert top_result.match_score > 0.0
        print(f"✅ Found: {top_result.name} (score: {top_result.rerank_score:.2f})")

    @pytest.mark.asyncio
    async def test_search_calamari(self, setup_food_hybrid_search):
        """Test semantic search for calamari appetizer."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "calamari appetizer"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=50
        )

        assert len(results) > 0, f"No results found for '{query}'"
        top_result = results[0]
        assert top_result.match_score > 0.0
        print(f"✅ Found: {top_result.name} (score: {top_result.rerank_score:.2f})")

    @pytest.mark.asyncio
    async def test_search_vegetarian_options(self, setup_food_hybrid_search):
        """Test semantic search for vegetarian options."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "vegetarian options"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=10,
            num_candidates=100
        )

        assert len(results) > 0, f"No results found for '{query}'"
        # Check that results include vegetarian items
        vegetarian_count = sum(1 for r in results if r.vegetarian_friendly)
        assert vegetarian_count > 0, "No vegetarian items in results"
        print(f"✅ Found {len(results)} vegetarian results")

    @pytest.mark.asyncio
    async def test_search_spicy_food(self, setup_food_hybrid_search):
        """Test semantic search for spicy food."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "spicy asian cuisine"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=50
        )

        assert len(results) > 0, f"No results found for '{query}'"
        top_result = results[0]
        print(f"✅ Found: {top_result.name} (spice level: {top_result.spice_level})")


# ============================================================================
# RESTAURANT-FILTERED SEARCH TESTS
# ============================================================================

class TestFoodSearchByRestaurant:
    """Test food search filtered by specific restaurants."""

    @pytest.mark.asyncio
    async def test_search_within_single_restaurant(
        self,
        setup_food_hybrid_search
    ):
        """Test search limited to a single restaurant."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        # Get first restaurant with food items
        all_food = await food_repository.filter_food(limit=100)
        if not all_food:
            pytest.skip("No food items in database")

        restaurant_id = all_food[0].entity.restaurant_id

        query = "food"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=[restaurant_id],
            limit=10,
            num_candidates=50
        )

        # All results should be from the specified restaurant
        assert len(results) > 0
        for result in results:
            assert result.restaurant_id == restaurant_id
        print(f"✅ Found {len(results)} items from restaurant {restaurant_id}")

    @pytest.mark.asyncio
    async def test_search_across_multiple_restaurants(
        self,
        setup_food_hybrid_search
    ):
        """Test search across multiple restaurants."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=200)
        if not all_food:
            pytest.skip("No food items in database")

        # Get 3 unique restaurants
        restaurants = list(set([item.entity.restaurant_id for item in all_food]))[:3]
        if len(restaurants) < 2:
            pytest.skip("Not enough restaurants in database")

        query = "appetizer"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurants,
            limit=10,
            num_candidates=50
        )

        # Results should only be from specified restaurants
        result_restaurants = set(r.restaurant_id for r in results)
        for r in result_restaurants:
            assert r in restaurants
        print(f"✅ Found {len(results)} items across {len(restaurants)} restaurants")


# ============================================================================
# SCORE FILTERING TESTS
# ============================================================================

class TestRerankerScoreFiltering:
    """Test rerank score threshold filtering."""

    @pytest.mark.asyncio
    async def test_results_above_threshold(self, setup_food_hybrid_search):
        """Test that results above threshold are included."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        food_hybrid_service.set_rerank_threshold(-2.0)

        query = "dumpling"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=10,
            num_candidates=50
        )

        # All results should have rerank_score >= -2.0
        for result in results:
            assert result.rerank_score is not None
            assert result.rerank_score >= -2.0
        print(f"✅ All {len(results)} results above threshold")

    @pytest.mark.asyncio
    async def test_strict_filtering(self, setup_food_hybrid_search):
        """Test stricter rerank threshold filters more results."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "food"

        # Get results with lenient threshold
        food_hybrid_service.set_rerank_threshold(-5.0)
        lenient_results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=100,
            num_candidates=100
        )

        # Get results with strict threshold
        food_hybrid_service.set_rerank_threshold(2.0)
        strict_results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=100,
            num_candidates=100
        )

        # Strict should have fewer or equal results
        assert len(strict_results) <= len(lenient_results)
        print(f"✅ Lenient: {len(lenient_results)} results, Strict: {len(strict_results)} results")


# ============================================================================
# RESULT QUALITY TESTS
# ============================================================================

class TestResultQuality:
    """Test quality and relevance of search results."""

    @pytest.mark.asyncio
    async def test_results_have_required_fields(
        self,
        setup_food_hybrid_search
    ):
        """Test that all results have required fields."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "appetizer"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=50
        )

        assert len(results) > 0
        for result in results:
            assert result.food_id is not None
            assert result.name is not None
            assert result.restaurant_id is not None
            assert result.match_score is not None
            assert result.rerank_score is not None
        print(f"✅ All results have required fields")

    @pytest.mark.asyncio
    async def test_results_ranked_by_score(
        self,
        setup_food_hybrid_search
    ):
        """Test that results are properly ranked by rerank score."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "crispy"
        results = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=10,
            num_candidates=50
        )

        if len(results) > 1:
            # Check that scores are in descending order (or equal)
            for i in range(len(results) - 1):
                assert results[i].rerank_score >= results[i + 1].rerank_score
            print(f"✅ Results properly ranked by rerank score")


# ============================================================================
# LIMIT AND PAGINATION TESTS
# ============================================================================

class TestLimitAndPagination:
    """Test result limiting."""

    @pytest.mark.asyncio
    async def test_limit_respected(self, setup_food_hybrid_search):
        """Test that result limit is respected."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "food"

        # Test different limits
        for limit in [1, 3, 5, 10]:
            results = await food_hybrid_service.search(
                query=query,
                restaurant_ids=restaurant_ids,
                limit=limit,
                num_candidates=100
            )
            assert len(results) <= limit

        print(f"✅ Limit respected for various values")

    @pytest.mark.asyncio
    async def test_num_candidates_affects_reranking(
        self,
        setup_food_hybrid_search
    ):
        """Test that num_candidates parameter affects reranking pool."""
        food_hybrid_service, food_repository = setup_food_hybrid_search
        all_food = await food_repository.filter_food(limit=1000)
        restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

        query = "dumpling appetizer"

        # Small candidate pool
        results_small = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=20
        )

        # Large candidate pool
        results_large = await food_hybrid_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=5,
            num_candidates=100
        )

        # Both should return results (quality may differ)
        assert len(results_small) > 0 or len(results_large) > 0
        print(f"✅ Small candidates: {len(results_small)}, Large candidates: {len(results_large)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])