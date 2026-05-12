"""Concrete MongoDB implementation of UserRepository."""

from typing import Optional
from app.repositories.user_repo import UserRepository
from app.model.users.models import UserEntity
from app.db.client import db


class MongoUserRepository(UserRepository):
    def __init__(self):
        self.collection = db["users"]

    async def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        """
        Fetches the complete User Profile by user_id.
        Used by RestaurantService to inject preferences into search requests.
        """
        doc = await self.collection.find_one({"user_id": user_id})
        if not doc:
            return None

        return UserEntity(**doc)

    async def update_preferences(self, user_id: str, updates: dict) -> bool:
        """
        Updates dietary, allergens, or other persistent user settings.
        Returns True if update was successful.
        """
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0