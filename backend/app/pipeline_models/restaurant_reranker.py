from reranker_adapter import RerankerAdapter

class RestaurantRerankerAdapter(RerankerAdapter):
    async def rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        # Replace with your actual reranker logic
        # Returns candidates in reranked order
        return sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
