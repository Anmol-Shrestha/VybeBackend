

from abc import ABC, abstractmethod

from app.model.restaurants.models import RestaurantEntity



class RestaurantRepository(ABC):
    @abstractmethod
    async def filter_restaurants(self, criteria: dict, bypass_hours: bool = False) -> list[RestaurantEntity]:
        pass

    @abstractmethod
    async def vector_search_by_ids(self, restaurant_ids: list[str], query_embedding: list[float], limit: int = 10, num_candidates: int = 100) -> list[RestaurantEntity]:
        pass

    
