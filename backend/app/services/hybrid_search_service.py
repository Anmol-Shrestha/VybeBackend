from app.pipeline_models.embedding_adapter import EmbeddingAdapter
from app.pipeline_models.reranker_adapter import RerankerAdapter
from app.utils.logger import get_search_logger, log_section, log_subsection
from app.observability.tracer import tracer


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
        allergens_to_exclude: list[str] = None,
    ) -> list[dict]:
        """Search entities by semantic similarity and rerank results.

        Args:
            query: User search query
            entity_ids: Pre-filtered entity IDs to search within
            limit: Number of final results to return
            num_candidates: Number of candidates to rerank
            allergens_to_exclude: Optional - hard filter to exclude items with these allergens
                                 (food-specific, ignored by restaurant repositories)

        Returns:
            List of reranked entities
        """
        allergens_to_exclude = allergens_to_exclude or []

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
        with tracer.start_as_current_span("hybrid_search.embed_query") as span:
            span.set_attribute("embedding.model", self.embedding_adapter.model)
            span.set_attribute("query.length", len(query))
            query_embedding = await self.embedding_adapter.embed_query(query)
            span.set_attribute("embedding.dimensions", len(query_embedding))
        self.logger.info(f"✓ Query embedded to {len(query_embedding)} dimensions\n")

        # ===== VECTOR SEARCH PHASE =====
        log_subsection(self.logger, "PHASE 2: MongoDB Vector Search")

        # Build search kwargs - allergens_to_exclude is optional (food-specific)
        search_kwargs = {
            "limit": num_candidates,
            "num_candidates": num_candidates,
        }
        if allergens_to_exclude:
            search_kwargs["allergens_to_exclude"] = allergens_to_exclude

        with tracer.start_as_current_span("hybrid_search.vector_search") as span:
            span.set_attribute("db.collection", "food")
            span.set_attribute("restaurant_ids.count", len(entity_ids))
            span.set_attribute("allergens_excluded.count", len(allergens_to_exclude))
            span.set_attribute("num_candidates", num_candidates)
            candidates = await self.vector_repository.vector_search_by_ids(
                entity_ids,
                query_embedding,
                **search_kwargs
            )
            span.set_attribute("candidates.returned", len(candidates))

            # Add span events for each candidate result
            for idx, candidate in enumerate(candidates, 1):
                entity_id = getattr(candidate.entity, "restaurant_id", getattr(candidate.entity, "food_id", "unknown"))
                name = candidate.entity.name
                match_score = getattr(candidate, "match_score", 0)
                span.add_event(
                    "vector_search_result",
                    attributes={
                        "rank": idx,
                        "entity_id": entity_id,
                        "name": name,
                        "similarity_score": match_score,
                    }
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
        with tracer.start_as_current_span("hybrid_search.rerank") as span:
            span.set_attribute("reranker.model", self.reranker_adapter.model_name)
            span.set_attribute("candidates.input_count", len(candidates))
            reranked = await self.reranker_adapter.rerank(query, candidates)
            span.set_attribute("candidates.output_count", len(reranked))

            # Add span events for each reranked result
            for idx, result in enumerate(reranked, 1):
                entity_id = getattr(result.entity, "restaurant_id", getattr(result.entity, "food_id", "unknown"))
                name = result.entity.name
                rerank_score = getattr(result, "rerank_score", 0)
                span.add_event(
                    "reranked_result",
                    attributes={
                        "rank": idx,
                        "entity_id": entity_id,
                        "name": name,
                        "rerank_score": float(rerank_score),
                    }
                )

        self.logger.info(f"✓ Re-ranking complete\n")

        log_subsection(self.logger, "POST-RERANK RESULTS")
        self.logger.info(f"{'Rank':<6} {'Entity ID':<20} {'Name':<40} {'Rerank Score':<15}")
        self.logger.info("-" * 80)
        for idx, result in enumerate(reranked, 1):
            entity_id = getattr(result.entity, "restaurant_id", getattr(result.entity, "food_id", "unknown"))
            name = result.entity.name
            rerank_score = getattr(result, "rerank_score", 0)
            self.logger.info(f"{idx:<6} {entity_id:<20} {name:<40} {rerank_score:<15.4f}")
        self.logger.info("")

        # ===== PIPELINE END =====
        log_subsection(self.logger, "PIPELINE SUMMARY")
        self.logger.info(f"Total Results: {len(reranked)}")
        log_section(self.logger, "HYBRID SEARCH PIPELINE END")

        return reranked[:limit]
