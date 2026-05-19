"""FastAPI application for Restaurant Search Service."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from dotenv import load_dotenv

from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository
from app.repositories.mongo_user_repo import MongoUserRepository
from app.services.restaurant_service import RestaurantService
from app.model.restaurants.models import RestaurantSearchRequest, RestaurantsSearchResponse

load_dotenv()




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB client and repositories
    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("DATABASE_NAME", "vybe")

    if not mongodb_url:
        raise RuntimeError("MONGODB_URL environment variable not set")

    app.mongodb_client = AsyncMongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    app.database = app.mongodb_client[db_name]
    app.restaurant_repo = MongoRestaurantRepository(app.database["restaurants"])
    app.user_repo = MongoUserRepository(app.database["users"])
    app.restaurant_service = RestaurantService(
        app.restaurant_repo,
        app.user_repo
    )

    print("✅ Application startup: MongoDB connected, repositories initialized")

    yield

    # Shutdown: Close database connection
    await app.mongodb_client.close()
    print("✅ Application shutdown: MongoDB connection closed")




app = FastAPI(
    title="Restaurant Search API",
    description="VYBE Restaurant Discovery Service",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Postman and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/restaurants/search", response_model=list[RestaurantsSearchResponse])
async def search_restaurants(
    request: RestaurantSearchRequest,
    bypass_hours: bool = Query(False, description="Skip service hours check for testing")
) -> list[RestaurantsSearchResponse]:
    """
    Search for restaurants based on location and preferences.

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
        # Execute search with optional preference injection
        results = await app.restaurant_service.get_filtered_restaurants(request, bypass_hours=bypass_hours)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
