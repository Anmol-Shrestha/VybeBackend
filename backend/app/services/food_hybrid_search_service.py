"""
Food Hybrid Search Service: Domain-specific facade for semantic food discovery.

Composes HybridSearchService for vector-based food search.
Converts generic search results to FoodSearchResponse with:
- Query embedding via OpenAI
- MongoDB vector search by restaurant IDs
- Cross-encoder reranking
- Rerank score filtering
"""

from typing import List
import logging
from app.services.hybrid_search_service import HybridSearchService
from app.model.food.models import FoodSearchResponse, FoodSearchResult
from app.observability.tracer import tracer

logger = logging.getLogger(__name__)


class FoodHybridSearchService:
    """Domain-specific food search facade using hybrid search pipeline.

    Orchestrates:
    1. Query embedding (OpenAI text-embedding-3-small)
    2. MongoDB vector search (ID-bounded to restaurant_ids)
    3. Cross-encoder reranking (refines top candidates)
    4. Score-based filtering (removes poor matches)
    """

    def __init__(
        self,
        hybrid_search: HybridSearchService,
        rerank_score_threshold: float = -2.0
    ):
        """
        Initialize with hybrid search pipeline and quality threshold.

        Args:
            hybrid_search: HybridSearchService instance (embedding + vector + rerank)
            rerank_score_threshold: Minimum rerank score to include result (default: -2.0)
                - Results below threshold are filtered out
                - Prevents poor semantic matches from appearing
        """
        self.hybrid_search = hybrid_search
        self.rerank_score_threshold = rerank_score_threshold
        self.logger = logging.getLogger(__name__)

    async def search(
        self,
        query: str,
        restaurant_ids: List[str],
        limit: int = 10,
        num_candidates: int = 100,
        allergens_to_exclude: List[str] = None,
    ) -> List[FoodSearchResponse]:
        """
        Search food items by semantic similarity with safety filtering.

        Workflow:
        1. Embed query using OpenAI embeddings
        2. Vector search MongoDB food collection (with hard allergen filtering)
        3. Rerank top candidates using cross-encoder
        4. Filter by rerank score threshold
        5. Convert to FoodSearchResponse

        Args:
            query: Natural language food search query
                   Examples: "spicy vegan dumplings", "crispy fried chicken", "calamari appetizer"
            restaurant_ids: Pre-filtered restaurant IDs to search within
                           (results from restaurant search or manual selection)
            limit: Number of final results to return (1-10, default: 10)
            num_candidates: Number of candidates to consider for reranking
                           Higher value = more expensive but better reranking
                           (20-100, default: 100)
            allergens_to_exclude: CRITICAL - items containing ANY of these allergens are excluded
                                 Applied as hard filter in vector search (not post-filtering)

        Returns:
            List of FoodSearchResponse objects ranked by rerank score
            Only includes items with rerank_score >= threshold
            All results are guaranteed allergen-safe (no excluded allergens)
        """
        allergens_to_exclude = allergens_to_exclude or []

        with tracer.start_as_current_span("food_hybrid_search.search") as span:
            # Input attributes
            span.set_attribute("query", query)
            span.set_attribute("query.length", len(query))
            span.set_attribute("restaurant_ids.count", len(restaurant_ids))
            span.set_attribute("limit", limit)
            span.set_attribute("num_candidates", num_candidates)
            span.set_attribute("allergens.count", len(allergens_to_exclude))

            # Log input query as event
            span.add_event(
                "search_input",
                attributes={
                    "query": query,
                    "restaurants_searched": len(restaurant_ids),
                    "allergens_excluded": ", ".join(allergens_to_exclude) if allergens_to_exclude else "none",
                }
            )

            self.logger.info(
                f"🍽️  Food Hybrid Search: query='{query}', "
                f"restaurants={len(restaurant_ids)}, limit={limit}"
            )
            if allergens_to_exclude:
                self.logger.info(f"⚠️  Allergen Safety: excluding {allergens_to_exclude}")

            # ===== HYBRID SEARCH PIPELINE =====
            # 1. Embedding: OpenAI text-embedding-3-small (1536 dims)
            # 2. Vector Search: MongoDB $vectorSearch with hard allergen filtering
            # 3. Reranking: Cross-encoder for precision
            food_results = await self.hybrid_search.search(
                query=query,
                entity_ids=restaurant_ids,
                limit=num_candidates,
                num_candidates=num_candidates,
                allergens_to_exclude=allergens_to_exclude,
            )

            self.logger.info(f"📊 Pipeline returned {len(food_results)} candidates")
            span.set_attribute("candidates.returned", len(food_results))

            # ===== RESULT CONVERSION & FILTERING =====
            responses = []
            for result in food_results:
                # Type cast result to FoodSearchResult
                if not isinstance(result, FoodSearchResult):
                    # If it's coming as dict, wrap it
                    continue

                # Extract rerank score (added by reranker in pipeline)
                rerank_score = getattr(result, 'rerank_score', None) or 0.0

                # Filter by quality threshold
                if rerank_score < self.rerank_score_threshold:
                    self.logger.debug(
                        f"⏭️  Skipping {result.entity.name} "
                        f"(score {rerank_score:.4f} < threshold {self.rerank_score_threshold})"
                    )
                    continue

                # Convert FoodSearchResult → FoodSearchResponse
                response = FoodSearchResponse.from_entity(
                    entity=result.entity,
                    match_score=result.match_score,  # Vector similarity score
                    rerank_score=rerank_score  # Cross-encoder rerank score
                )
                responses.append(response)

            # Apply limit to final results
            responses = responses[:limit]

            span.set_attribute("results.after_threshold_filter", len(responses))
            span.set_attribute("rerank_threshold", self.rerank_score_threshold)
            span.set_attribute("results.final_count", len(responses))

            # Log final results as span events
            for idx, response in enumerate(responses, 1):
                span.add_event(
                    "final_result",
                    attributes={
                        "rank": idx,
                        "food_id": response.food_id,
                        "name": response.name,
                        "restaurant_id": response.restaurant_id,
                        "match_score": float(response.match_score) if response.match_score else 0.0,
                        "rerank_score": float(response.rerank_score) if response.rerank_score else 0.0,
                    }
                )

            self.logger.info(
                f"✅ Food search complete: {len(responses)} items "
                f"(after threshold filtering and limiting to {limit})"
            )

            return responses

    # ========================================================================
    # CONFIGURATION & UTILITIES
    # ========================================================================

    def set_rerank_threshold(self, threshold: float) -> None:
        """
        Adjust rerank score threshold for quality filtering.

        Threshold scale (typical values):
        - 4.0+: Very strict (only highest quality matches)
        - 0.0: Balanced (good default)
        - -2.0: Lenient (current default, allows some loose matches)
        - -5.0: Very lenient (accepts almost anything)

        Args:
            threshold: New rerank score threshold
        """
        self.logger.info(f"Updating rerank threshold: {self.rerank_score_threshold} → {threshold}")
        self.rerank_score_threshold = threshold

    def get_config(self) -> dict:
        """Get current search configuration."""
        return {
            "embedding_model": getattr(
                self.hybrid_search.embedding_adapter,
                "model",
                "text-embedding-3-small"
            ),
            "reranker_model": getattr(
                self.hybrid_search.reranker_adapter,
                "model_name",
                "cross-encoder"
            ),
            "rerank_score_threshold": self.rerank_score_threshold,
        }