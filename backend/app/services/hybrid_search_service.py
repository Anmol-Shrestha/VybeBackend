import time
from app.pipeline_models.embedding_adapter import EmbeddingAdapter
from app.pipeline_models.reranker_adapter import RerankerAdapter
from app.utils.logger import get_search_logger, log_section, log_subsection


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
        self.logger = get_search_logger()

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
        start_time = time.time()

        # ===== PIPELINE START =====
        log_section(self.logger, "HYBRID SEARCH PIPELINE START")

        # Log configuration
        self.logger.info(f"Query: '{query}'")
        self.logger.info(f"Embedding Model: {self.embedding_adapter.model}")
        self.logger.info(f"Re-ranker Model: {self.reranker_adapter.model_name}")
        self.logger.info(f"Entity IDs Allowed: {len(entity_ids)} restaurants")
        self.logger.info(f"Parameters: limit={limit}, num_candidates={num_candidates}\n")

        # ===== EMBEDDING PHASE =====
        log_subsection(self.logger, "PHASE 1: Query Embedding")
        query_embedding = await self.embedding_adapter.embed_query(query)
        self.logger.info(f"✓ Query embedded to {len(query_embedding)} dimensions\n")

        # ===== VECTOR SEARCH PHASE =====
        log_subsection(self.logger, "PHASE 2: MongoDB Vector Search")
        candidates = await self.vector_repository.vector_search_by_ids(
            entity_ids,
            query_embedding,
            limit=num_candidates,
            num_candidates=num_candidates,
        )

        self.logger.info(f"✓ Retrieved {len(candidates)} candidates from vector search\n")

        log_subsection(self.logger, "PRE-RERANK CANDIDATES")
        self.logger.info(f"{'Rank':<6} {'Restaurant ID':<20} {'Name':<40}")
        self.logger.info("-" * 66)
        for idx, candidate in enumerate(candidates, 1):
            restaurant_id = candidate.entity.restaurant_id
            name = candidate.entity.name
            self.logger.info(f"{idx:<6} {restaurant_id:<20} {name:<40}")
        self.logger.info("")

        # ===== RERANKING PHASE =====
        log_subsection(self.logger, "PHASE 3: Cross-Encoder Re-ranking")
        reranked = await self.reranker_adapter.rerank(query, candidates)
        self.logger.info(f"✓ Re-ranking complete\n")

        log_subsection(self.logger, "POST-RERANK RESULTS")
        self.logger.info(f"{'Rank':<6} {'Restaurant ID':<20} {'Name':<40} {'Rerank Score':<15} {'Distance (km)':<15}")
        self.logger.info("-" * 96)
        for idx, result in enumerate(reranked, 1):
            restaurant_id = result.entity.restaurant_id
            name = result.entity.name
            rerank_score = getattr(result, "rerank_score", 0)
            distance_km = result.distance_km
            self.logger.info(f"{idx:<6} {restaurant_id:<20} {name:<40} {rerank_score:<15.4f} {distance_km:<15.2f}")
        self.logger.info("")

        # ===== PIPELINE END =====
        elapsed_ms = (time.time() - start_time) * 1000
        log_subsection(self.logger, "PIPELINE SUMMARY")
        self.logger.info(f"Total Results: {len(reranked)}")
        self.logger.info(f"Execution Time: {elapsed_ms:.2f}ms")
        log_section(self.logger, "HYBRID SEARCH PIPELINE END")

        return reranked[:limit]
