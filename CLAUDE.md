# Project: Restaurant Search MVP
## Tech Stack
- Frontend: React (Vite) + Tailwind CSS
- Backend: FastAPI (Python 3.11+)
- Database: MongoDB Atlas (PyMongo for async)
- Tooling: Pipenv

## Architecture
- Pattern: Service-Layer / Repository / Adapter
- Directory Structure:
backend/
└── app/
    ├── api/             # FastAPI Endpoints
    ├── model/           # Pydantic Models (Users/Restaurants)
    ├── repositories/    # MongoDB Async Implementations
    └── services/        # Business Logic & Preference Injection

## Guidelines
- Follow Top-Down Design
- Follow Contract First Design 
- Use Dependency Injection for repositories into services.
- Backend must have Pytest for Service-layer logic.






Context: We are building a Restaurant Discovery Service for a platform called VYBE. The goal is to implement a high-performance, personalized search using PyMongo Async and FastAPI.
1. Core Architecture

We follow a strict Service-Layer & Repository Pattern to decouple business logic from data providers.

    API Layer: Normalizes JSON into Pydantic models.

    Service Layer: Injects User Preferences (Identity) into "Incomplete" requests.

    Repository Layer: Handles MongoDB Aggregation Pipelines (Geospatial + Ranking).

2. Data Transformation Requirements

The existing JSON data must be refactored to support advanced querying:

    Location: Convert flat lat/long into GeoJSON Point format: {"type": "Point", "coordinates": [long, lat]}.

    Service Hours: Convert human-readable strings into "Minutes from Midnight" objects: {"open": int, "close": int}.

    Booleans: Ensure all toggle fields (has_parking, live_music) are native BSON booleans.

3. The "Preference Injection" Workflow

The RestaurantService must handle "Incomplete" request objects:

    If the request lacks dietary or allergens, call UserRepository.get_by_id.

    Populate the request with stored User Preferences.

    Pass the Complete Filter Object to the RestaurantRepository.

4. The Discovery Pipeline (Ranking Logic)

The MongoDB Aggregation Pipeline must execute in this order:

    $geoNear: Filter by 5km/10km radius and calculate distance_km.

    $match: Strict exclusion based on dietary and allergens.

    $addFields (Scoring): Calculate a match_score where matching optional amenities (Parking, Live Music) adds +1 to the score.

    $sort: Sort by match_score (DESC) then distance_km (ASC).

5. Tech Stack & Test Suite

    Database: MongoDB Atlas (Native Async Driver: pymongo.asynchronous).

    Testing: Pytest (Async). Use the test/ folder data to verify that "Mr. Vegan" at the Scarborough coordinates correctly ranks "Purely Vegan Hub" first.

## RAG Pipeline & Vector Embeddings (Enterprise Agentic Search)

### Overview
Implementing an enterprise-grade Agentic RAG (Retrieval-Augmented Generation) pipeline for semantic restaurant discovery using OpenAI embeddings and CrewAI orchestration.

**Architecture:** Service-Layer + Repository + Adapter patterns
- **Embedding Adapter**: Converts restaurant metadata → OpenAI vectors (text-embedding-3-small, 1536 dims)
- **Repository Layer**: MongoDB $vectorSearch queries (ID-bounded with re-ranking)
- **Orchestrator Service**: CrewAI multi-agent workflow (Intent Classification → Requirements → Answer Generation)
- **API Endpoint**: `/restaurants/chat` accepts RequirementHybridSearchRequest (query text + restaurant_ids)

### Mock Restaurant Dataset
Created 19 comprehensive test restaurants covering:
- ✅ 24-hour & late-night venues (The Night Owl Diner, 24hr Vegan Diner)
- ✅ Dietary specializations (vegan, gluten-free, halal, kosher)
- ✅ Ambiance/vibe matching (date night, work-friendly, family-oriented)
- ✅ Live music venues
- ✅ Budget & fine dining options
- ✅ Geographic diversity across Toronto area

### Embedding Strategy
**Semantic Text Composition** (`build_embedding_text()` in seed_database.py):
1. Name + description (highest weight)
2. Meal types repeated (for time-based queries: "late night", "24 hour")
3. Dietary options repeated (for dietary queries: "vegan", "gluten-free")
4. Cuisine types
5. Atmosphere & vibe tags
6. Best-for intent tags (e.g., "Perfect for: date night, group dinners")

**Important:** Must explicitly encode "24 hour" / "always open" status in embedding text for optimal semantic matching.

### Database Seeding (`backend/scripts/seed_database.py`)
- Transforms restaurant JSON → RestaurantEntity (GeoJSON location, normalized service hours)
- Generates OpenAI embeddings (1536-dim vectors)
- Stores per document:
  - `vector_embeddings`: The embedding vector
  - `embedding_model`: "text-embedding-3-small"
  - `embedding_dimensions`: 1536
  - `embedding_source`: The text that was embedded
  - `embedding_timestamp`: Creation timestamp
- Creates geospatial index for $geoNear queries
- Loads environment from `.env` file (MONGODB_URL, OPENAI_API_KEY, DATABASE_NAME)

### Vector Similarity Testing (`backend/test/test_vector_similarity.py`)
Script to validate embedding quality before full deployment:
1. Connects to MongoDB Atlas
2. Fetches stored restaurant embeddings
3. Generates embeddings for test queries
4. Calculates cosine similarity (0-100%)
5. Scores queries (🔥 >75% excellent, ✅ 60-75% good, ⚠️ 50-60% moderate, ❌ <50% low)

**Current Findings:**
- Vegan/dietary queries: 65-71% (good)
- Late night queries: 54-58% (moderate - need explicit "24 hour" emphasis)
- Unrelated queries: 27-30% (correctly low)

### Next Steps
1. Enhance `build_embedding_text()` to check service_hours and explicitly include "Open 24 hours" for 24hr restaurants
2. Implement MongoDB $vectorSearch queries (ID-bounded to passed restaurant_ids)
3. Build Re-ranker Adapter (cross-encoder for top-5 precision filtering)
4. Integrate CrewAI Orchestrator with 3-agent workflow
5. Add Pytest integration tests for end-to-end RAG pipeline

  