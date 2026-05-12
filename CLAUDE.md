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

📁 Folder Structure Reference for Claude
Plaintext

backend/
└── app/
    ├── api/             # FastAPI Endpoints
    ├── model/           # Pydantic Models (Users/Restaurants)
    ├── repositories/    # MongoDB Async Implementations
    └── services/        # Business Logic & Preference Injection

🧪 Instructions for Claude:

    "Using the provided summary and the sample files in the /test directory, please implement the RestaurantRepository and RestaurantService.

        Start by refactoring restaurants.json into the GeoJSON/Integer-hour format.

        Implement the Async MongoDB connection.

        Write the Aggregation Pipeline that supports the 'Complete Filter Object' logic.

        Ensure the service layer correctly 'fills the gaps' for incomplete requests using the UserRepo."



  