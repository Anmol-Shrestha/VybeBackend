from app.services.hybrid_search_service import HybridSearchService


class RestaurantSearchService:
    """Domain-specific restaurant search facade.

    Composes HybridSearchService for semantic restaurant discovery.
    THe Hybrid Search service is basically a fill in the blank.
    And the Blanks which must be filled is:
    1. Embeddings Model : That turns the query into a vector
    2. Repository : Repository that has the search_vector_by_ids method
    3. Re-ranker model : A model that take sin the query and 
    """

    def __init__(self, hybrid_search: HybridSearchService):
        self.hybrid_search = hybrid_search

    async def search(
        self,
        query: str,
        restaurant_ids: list[str],
        limit: int = 10,
        num_candidates: int = 100,
    ) -> list[dict]:
        """Search restaurants by semantic similarity.

        Args:
            query: User search query
            restaurant_ids: Pre-filtered restaurant IDs to search within
            limit: Number of final results to return
            num_candidates: Number of candidates to rerank

        Returns:
            List of reranked restaurants
        """
        return await self.hybrid_search.search(query, restaurant_ids, limit, num_candidates)
