"""
Pytest configuration: Load environment variables and set up Python paths before tests run.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
from pymongo import AsyncMongoClient


def pytest_configure(config):
    """
    Load .env file at the start of the test session.
    This runs before any tests are collected.
    """
    # Add backend directory to Python path so 'app' module is discoverable
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Find the .env file in the backend directory (parent of test)
    env_file = backend_dir / ".env"

    if not env_file.exists():
        raise RuntimeError(
            f"❌ .env file not found at {env_file}\n"
            "Please create a .env file with MONGODB_URL and DATABASE_NAME"
        )

    # Load environment variables from .env
    load_dotenv(env_file)

    # Validate required environment variables
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise RuntimeError(
            "❌ MONGODB_URL environment variable is not set.\n"
            "Please add MONGODB_URL=your_connection_string to your .env file"
        )

    database_name = os.getenv("DATABASE_NAME", "vybe")

    print(f"\n✅ Test environment loaded:")
    print(f"   Database: {database_name}")
    print(f"   MongoDB: Connected to Atlas cluster")


@pytest.fixture
async def mongo_restaurant_collection():
    """Fixture to provide MongoDB restaurant collection for testing."""
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "vybe")

    # Connect to MongoDB
    client = AsyncMongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    db = client[database_name]
    collection = db["restaurants"]

    yield collection

    # Cleanup
    await client.close()


@pytest.fixture
async def setup_hybrid_search(mongo_restaurant_collection):
    """Set up HybridSearchService with real dependencies for testing."""
    from openai import AsyncOpenAI
    from app.services.hybrid_search_service import HybridSearchService
    from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
    from app.pipeline_models.restaurant_reranker import RestaurantRerankerAdapter
    from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository

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
