
from services.hybrid_search_service import HybridSearchService


class CrewAIHybridSearchTool:
    def __init__(self, hybrid_search_service: HybridSearchService):
        self.hybrid_search_service = hybrid_search_service

    async def run(self, query: str, restaurant_ids: list[str]) -> list[dict]:
        return await self.hybrid_search_service.search(
            query=query,
            restaurant_ids=restaurant_ids,
            limit=10,
            num_candidates=100,
        )
