from app.pipeline_models.embedding_adapter import EmbeddingAdapter
from app.pipeline_models.reranker_adapter import RerankerAdapter


class HybridSearchService:
    """Generic hybrid search orchestrator for vector similarity + reranking.

    Works with any repository that implements vector_search_by_ids().
    Entity-agnostic: can search restaurants, food items, menus, etc.
    """

    def __init__(
        self,
        embedding_adapter: EmbeddingAdapter,
        vector_repository,
        reranker_adapter: RerankerAdapter,
    ):
        self.embedding_adapter = embedding_adapter
        self.vector_repository = vector_repository
        self.reranker_adapter = reranker_adapter

    async def search(
        self,
        query: str,
        entity_ids: list[str],
        limit: int = 10,
        num_candidates: int = 100,
    ) -> list[dict]:
        """Search entities by semantic similarity and rerank results.

        Args:
            query: User search query
            entity_ids: Pre-filtered entity IDs to search within
            limit: Number of final results to return
            num_candidates: Number of candidates to rerank

        Returns:
            List of reranked entities
        """
        query_embedding = await self.embedding_adapter.embed_query(query)

        candidates = await self.vector_repository.vector_search_by_ids(
            entity_ids=entity_ids,
            query_embedding=query_embedding,
            limit=limit,
            num_candidates=num_candidates,
        )

        reranked = await self.reranker_adapter.rerank(query, candidates)

        return reranked
