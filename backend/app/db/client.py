"""MongoDB client singleton for async operations."""

import os
from pymongo import AsyncMongoClient

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "vybe")

client = AsyncMongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
