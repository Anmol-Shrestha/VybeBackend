import asyncio
from sentence_transformers import CrossEncoder
from app.pipeline_models.reranker_adapter import RerankerAdapter
from app.utils.logger import get_search_logger, log_subsection


class RestaurantRerankerAdapter(RerankerAdapter):
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = CrossEncoder(model_name)
        self.logger = get_search_logger()

    async def rerank(self, query: str, candidates: list) -> list[dict]:
        if not candidates:
            return []

        log_subsection(self.logger, "RE-RANKER: COMPOSED RESTAURANT TEXTS")
        self.logger.info(f"Query: '{query}'")
        self.logger.info("")

        candidate_texts = []
        for candidate in candidates:
            text = self._compose_restaurant_text(candidate)
            candidate_texts.append(text)

            # Log the exact text being fed to cross-encoder
            restaurant_id = candidate.entity.restaurant_id
            self.logger.info(f"[{restaurant_id}]")
            self.logger.info(f"Text: {text}")
            self.logger.info("")

        self.logger.info("-" * 80)
        self.logger.info(f"Running cross-encoder prediction on {len(candidate_texts)} candidate pairs...")
        self.logger.info("")

        pairs = [[query, text] for text in candidate_texts]
        scores = await asyncio.to_thread(self.model.predict, pairs)

        log_subsection(self.logger, "RE-RANKER: SCORES ASSIGNED")
        for candidate, score in zip(candidates, scores):
            restaurant_id = candidate.entity.restaurant_id
            self.logger.info(f"[{restaurant_id}] Score: {float(score):.4f}")
            candidate.rerank_score = float(score)

        self.logger.info("")

        def get_score(x):
            if isinstance(x, dict):
                return x.get("rerank_score", 0)
            return getattr(x, "rerank_score", 0)

        return sorted(candidates, key=get_score, reverse=True)

    def _compose_restaurant_text(self, candidate) -> str:
        parts = []

        # Handle RestaurantSearchResult objects
        if hasattr(candidate, "entity"):
            entity = candidate.entity

            if hasattr(entity, "name"):
                parts.append(entity.name)

            if hasattr(entity, "description"):
                parts.append(entity.description)

            if hasattr(entity, "cuisine") and entity.cuisine:
                parts.append(" ".join(entity.cuisine))

            if hasattr(entity, "dietary") and entity.dietary:
                parts.append(" ".join(entity.dietary))

            if hasattr(entity, "meal_types") and entity.meal_types:
                parts.append(" ".join(entity.meal_types))

        # Fallback for dict objects (legacy support)
        else:
            if isinstance(candidate, dict):
                if "name" in candidate:
                    parts.append(candidate["name"])
                if "description" in candidate:
                    parts.append(candidate["description"])
                if "cuisine" in candidate and candidate["cuisine"]:
                    parts.append(" ".join(candidate["cuisine"]))
                if "dietary" in candidate and candidate["dietary"]:
                    parts.append(" ".join(candidate["dietary"]))
                if "meal_types" in candidate and candidate["meal_types"]:
                    parts.append(" ".join(candidate["meal_types"]))

        return " ".join(parts)
