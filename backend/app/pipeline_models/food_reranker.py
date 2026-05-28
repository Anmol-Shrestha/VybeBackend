import asyncio
from sentence_transformers import CrossEncoder
from app.pipeline_models.reranker_adapter import RerankerAdapter
from app.utils.logger import get_search_logger, log_subsection


class FoodReranker(RerankerAdapter):
    """Cross-encoder reranker optimized for food item semantic relevance.

    Composes food-rich text including:
    - Name and description (primary signal)
    - Cuisine, dietary tags, meal types
    - Category and preparation method
    - AI metadata (mood, occasion, taste, texture, wellness tags)

    Available models:
    - BAAI/bge-reranker-base (default, ~300-400MB): Good balance of speed and quality
    - BAAI/bge-reranker-large (~500-700MB): Higher quality, slower
    - mixedbread-ai/mxbai-rerank-large-v1 (~500-700MB): Alternative high-quality model
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.model = CrossEncoder(model_name)
        self.logger = get_search_logger()

    async def rerank(self, query: str, candidates: list) -> list[dict]:
        if not candidates:
            return []

        log_subsection(self.logger, "RE-RANKER: COMPOSED FOOD TEXTS")
        self.logger.info(f"Query: '{query}'")
        self.logger.info("")

        candidate_texts = []
        for candidate in candidates:
            text = self._compose_food_text(candidate)
            candidate_texts.append(text)

            # Log the exact text being fed to cross-encoder
            food_id = candidate.entity.food_id
            self.logger.info(f"[{food_id}]")
            self.logger.info(f"Text: {text}")
            self.logger.info("")

        self.logger.info("-" * 80)
        self.logger.info(f"Running cross-encoder prediction on {len(candidate_texts)} candidate pairs...")
        self.logger.info("")

        pairs = [[query, text] for text in candidate_texts]
        scores = await asyncio.to_thread(self.model.predict, pairs)

        log_subsection(self.logger, "RE-RANKER: SCORES ASSIGNED")
        for candidate, score in zip(candidates, scores):
            food_id = candidate.entity.food_id
            self.logger.info(f"[{food_id}] Score: {float(score):.4f}")
            candidate.rerank_score = float(score)

        self.logger.info("")

        def get_score(x):
            if isinstance(x, dict):
                return x.get("rerank_score", 0)
            return getattr(x, "rerank_score", 0)

        return sorted(candidates, key=get_score, reverse=True)

    def _compose_food_text(self, candidate) -> str:
        """Compose rich semantic text for food item reranking.

        Includes: name, description, cuisine, dietary, meal types, category,
        preparation method, and AI metadata (mood, occasion, taste, texture, wellness).

        CRITICAL: All list fields are converted to strings before joining to prevent
        TypeError when a list is passed to str.join().
        """
        parts = []

        if hasattr(candidate, "entity"):
            entity = candidate.entity

            # Primary signal: name and description
            if hasattr(entity, "name") and entity.name:
                name = str(entity.name).strip()
                if name:
                    parts.append(name)

            if hasattr(entity, "description") and entity.description:
                desc = str(entity.description).strip()
                if desc:
                    parts.append(desc)

            # Cuisine tags - convert list to string
            if hasattr(entity, "cuisine") and entity.cuisine:
                cuisine_str = self._listify_field(entity.cuisine)
                if cuisine_str:
                    parts.append(cuisine_str)

            # Dietary attributes - convert list to string
            if hasattr(entity, "dietary") and entity.dietary:
                dietary_str = self._listify_field(entity.dietary)
                if dietary_str:
                    parts.append(dietary_str)

            # Meal types - convert list to string
            if hasattr(entity, "meal_types") and entity.meal_types:
                meal_str = self._listify_field(entity.meal_types)
                if meal_str:
                    parts.append(meal_str)

            # Category - ensure string
            if hasattr(entity, "category") and entity.category:
                cat = str(entity.category).strip()
                if cat:
                    parts.append(cat)

            # Preparation method - ensure string
            if hasattr(entity, "preparation_method") and entity.preparation_method:
                prep = str(entity.preparation_method).strip()
                if prep:
                    parts.append(prep)

            # AI metadata: mood, occasion, taste, texture, wellness
            if hasattr(entity, "ai_metadata") and entity.ai_metadata:
                metadata = entity.ai_metadata
                if isinstance(metadata, dict):
                    # Mood tags
                    if "mood" in metadata and metadata["mood"]:
                        mood_str = self._listify_field(metadata["mood"])
                        if mood_str:
                            parts.append(mood_str)

                    # Occasion tags
                    if "occasion" in metadata and metadata["occasion"]:
                        occasion_str = self._listify_field(metadata["occasion"])
                        if occasion_str:
                            parts.append(occasion_str)

                    # Taste descriptors
                    if "taste" in metadata and metadata["taste"]:
                        taste_str = self._listify_field(metadata["taste"])
                        if taste_str:
                            parts.append(taste_str)

                    # Texture descriptors
                    if "texture" in metadata and metadata["texture"]:
                        texture_str = self._listify_field(metadata["texture"])
                        if texture_str:
                            parts.append(texture_str)

                    # Wellness tags
                    if "wellness" in metadata and metadata["wellness"]:
                        wellness_str = self._listify_field(metadata["wellness"])
                        if wellness_str:
                            parts.append(wellness_str)

        # Final guard: ensure all parts are strings before joining
        clean_parts = [str(p).strip() for p in parts if p]
        return " ".join(clean_parts)

    def _listify_field(self, field) -> str:
        """Convert any field (string, list, etc.) to a comma-separated string.

        Handles:
        - Lists: converts to comma-separated string
        - Strings: returns as-is
        - None/empty: returns empty string
        """
        if not field:
            return ""

        if isinstance(field, list):
            # Convert list items to strings and join
            str_items = [str(item).strip() for item in field if item]
            return ", ".join(str_items)

        # Already a string (or other type - convert to string)
        return str(field).strip()