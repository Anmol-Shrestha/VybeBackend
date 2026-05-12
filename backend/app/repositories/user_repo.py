from abc import ABC, abstractmethod
from typing import Optional
from app.model.users.models import UserEntity

class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        """
        Fetches the complete User Profile (Identity + Preferences).
        Used by RestaurantService to 'Inject' preferences into search requests.
        """
        pass

    @abstractmethod
    async def update_preferences(self, user_id: str, updates: dict) -> bool:
        """
        Updates dietary, allergens, or other persistent user settings.
        """
        pass