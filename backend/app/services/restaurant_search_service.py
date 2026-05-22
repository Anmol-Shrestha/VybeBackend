from app.services.hybrid_search_service import HybridSearchService
from app.model.restaurants.models import RestaurantsSearchResponse


class RestaurantSearchService:
    """Domain-specific restaurant search facade.

    Composes HybridSearchService for semantic restaurant discovery.
    Converts generic RestaurantSearchResult objects to RestaurantsSearchResponse.
    """

    def __init__(self, hybrid_search: HybridSearchService):
        self.hybrid_search = hybrid_search

    async def search(
        self,
        query: str,
        restaurant_ids: list[str],
        limit: int = 10,
        num_candidates: int = 100,
    ) -> list[RestaurantsSearchResponse]:
        """Search restaurants by semantic similarity.

        Args:
            query: User search query
            restaurant_ids: Pre-filtered restaurant IDs to search within
            limit: Number of final results to return
            num_candidates: Number of candidates to rerank

        Returns:
            List of RestaurantsSearchResponse objects with ranking scores
        """
        restaurant_results = await self.hybrid_search.search(query, restaurant_ids, limit, num_candidates)

        # Convert RestaurantSearchResult objects to API response format
        responses = []
        for result in restaurant_results:
            # result.entity is RestaurantEntity
            # result.distance_km is float
            # result.rerank_score is float (added by reranker)
            response = RestaurantsSearchResponse.from_entity(
                entity=result.entity,
                distance=result.distance_km,
                is_open=True  # TODO: check against service_hours
            )
            responses.append(response)

        return responses
