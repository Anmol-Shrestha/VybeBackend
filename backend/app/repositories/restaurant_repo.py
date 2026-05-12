

from abc import ABC, abstractmethod

from app.model.restaurants.models import RestaurantEntity



class RestaurantRepository(ABC):
    @abstractmethod
    async def filter_restaurants(self, criteria: dict, bypass_hours: bool = False) -> list[RestaurantEntity]:
        pass

    
