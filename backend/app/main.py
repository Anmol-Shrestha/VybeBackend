"""FastAPI application for Restaurant Search Service."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from dotenv import load_dotenv

from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository
from app.repositories.mongo_user_repo import MongoUserRepository
from app.repositories.mongo_food_repo import MongoFoodRepository
from app.services.restaurant_service import RestaurantService
from app.services.food_service import FoodService
from app.api.v1.restaurants import router as v1_restaurants_router
from app.api.v1.food import router as v1_food_router
from app.observability.setup import setup_phoenix

load_dotenv()




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize observability first
    setup_phoenix(app)

    # Then initialize MongoDB client and repositories
    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("DATABASE_NAME", "vybe")

    if not mongodb_url:
        raise RuntimeError("MONGODB_URL environment variable not set")

    app.mongodb_client = AsyncMongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    app.database = app.mongodb_client[db_name]
    app.restaurant_repo = MongoRestaurantRepository(app.database["restaurants"])
    app.user_repo = MongoUserRepository(app.database["users"])
    app.food_repo = MongoFoodRepository(app.database["food"])
    app.restaurant_service = RestaurantService(
        app.restaurant_repo,
        app.user_repo
    )
    app.food_service = FoodService(app.food_repo)

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

# Include V1 API routers
app.include_router(v1_restaurants_router)
app.include_router(v1_food_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
