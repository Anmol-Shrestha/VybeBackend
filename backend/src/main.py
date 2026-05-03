import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncClient, AsyncDatabase
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "restaurant_search")

mongo_client: AsyncClient = None
db: AsyncDatabase = None


async def connect_to_mongo():
    global mongo_client, db
    mongo_client = AsyncClient(MONGODB_URL)
    db = mongo_client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")


async def close_mongo_connection():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Disconnected from MongoDB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(title="Restaurant Search API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Welcome to Restaurant Search API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
