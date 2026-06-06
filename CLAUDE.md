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

