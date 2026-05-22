"""Restaurant service with optional preference injection and search orchestration."""

from app.repositories.restaurant_repo import RestaurantRepository
from app.repositories.user_repo import UserRepository
from app.model.restaurants.models import RestaurantSearchRequest, RestaurantsSearchResponse


class RestaurantService:
    def __init__(self, repo_restaurant: RestaurantRepository, repo_user: UserRepository):
        self.repo_restaurant = repo_restaurant
        self.repo_user = repo_user

    async def get_filtered_restaurants(
        self, request: RestaurantSearchRequest, bypass_hours: bool = False
    ) -> list[RestaurantsSearchResponse]:
        """
        Orchestrates restaurant search with optional preference injection.

        Flow:
        1. If userID is provided and dietary is empty:
           - Fetch user preferences from UserRepository
           - Inject dietary preference into the filter for personalized results
        2. If userID is provided but dietary is explicitly set:
           - Use the provided dietary (user preference override)
        3. If no userID (anonymous):
           - Search with provided filters only
           - No dietary preference injection

        Args:
            request: RestaurantSearchRequest with search criteria
            bypass_hours: If True, skips stage 4 (temporal/service hours check) in aggregation pipeline.
                         Useful for testing. Defaults to False.

        Returns list of RestaurantsSearchResponse sorted by match_score and distance.
        """
        filters = request.model_dump()

        # Preference injection: if userID exists and dietary is empty, fetch from user profile
        if request.userID and not filters.get("dietary"):
            user = await self.repo_user.get_by_id(request.userID)
            if user:
                filters["dietary"] = [user.dietary]

        # Call the repository to execute the aggregation pipeline
        # - Authenticated users with injected preferences: personalized results
        # - Authenticated users with explicit dietary: respects their choice
        # - Anonymous users: results based on provided cuisine/meal_types filters
        search_results = await self.repo_restaurant.filter_restaurants(filters, bypass_hours=bypass_hours)

        # Transform search results to response format
        responses = []
        for result in search_results:
            response = RestaurantsSearchResponse.from_entity(
                result.entity,
                distance=result.distance_km,
                is_open=True
            )
            responses.append(response)

        return responses