"""Food Service Data Models."""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- 1. Internal Domain Entity ---

class FoodItemEntity(BaseModel):
    """Complete food item entity with all attributes and AI metadata."""

    model_config = ConfigDict(populate_by_name=True)

    # Identifiers
    food_id: str
    restaurant_id: str

    # Basic Info
    name: str
    description: str
    category: str  # appetizer, main_course, dessert, beverage, etc.
    cuisine: List[str]

    # Dietary & Allergen Info
    dietary: List[str]  # vegan, vegetarian, gluten-free, dairy-free, etc.
    allergens: List[str]  # nuts, shellfish, dairy, soy, etc.
    ingredients: List[str]

    # Food Characteristics
    spice_level: int = Field(default=0, ge=0, le=5)  # 0-5 scale
    prep_time_minutes: Optional[int] = Field(default=None, description="Estimated preparation time in minutes")
    preparation_method: List[str] = Field(default_factory=list)  # grilled, fried, baked, raw
    meal_types: List[str] = Field(default_factory=list)  # breakfast, lunch, dinner, snack
    price: float
    calories: Optional[int] = None

    # Dietary Flags (convenience booleans)
    vegetarian_friendly: bool = False
    vegan_friendly: bool = False
    gluten_free: bool = False

    # Popularity & Ratings
    is_signature_dish: bool = False
    is_popular: bool = False
    rating: Optional[float] = None
    popularity_score: Optional[float] = None

    # AI Metadata for informal queries
    ai_metadata: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Informal descriptions and context tags"
    )
    # Examples:
    # - "comfort_food": ["mac and cheese", "feels like home"]
    # - "mood": ["feel-good", "indulgent", "light"]
    # - "occasion": ["date night", "quick lunch", "celebration"]
    # - "taste_profile": ["sweet", "savory", "umami", "tangy"]
    # - "texture": ["crispy", "creamy", "chewy", "tender"]

    # Vector Embeddings (OpenAI text-embedding-3-small)
    vector_embeddings: Optional[List[float]] = Field(
        default=None,
        description="1536-dimensional semantic vector representing the food item"
    )
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536)
    embedding_source: Optional[str] = None  # The text that was embedded
    embedding_timestamp: Optional[datetime] = None
    
    def to_embedding_text(self) -> str:
        """
        Compiles a rich, multi-faceted semantic string representation for vector generation.
        Optimized for OpenAI text-embedding-3-small to capture taste, dietary, occasion, and mood.
        """
        # Compose base food info
        cuisine_str = ", ".join(self.cuisine) if self.cuisine else "unknown"
        dietary_str = ", ".join(self.dietary) if self.dietary else "none"
        meal_types_str = ", ".join(self.meal_types) if self.meal_types else "unknown"
        ingredients_str = ", ".join(self.ingredients) if self.ingredients else "various"
        prep_str = ", ".join(self.preparation_method) if self.preparation_method else "standard"

        # Flatten AI metadata tags for semantic richness
        mood_tags = self.ai_metadata.get("mood", [])
        taste_tags = self.ai_metadata.get("taste_profile", [])
        texture_tags = self.ai_metadata.get("texture", [])
        occasion_tags = self.ai_metadata.get("occasion", [])
        comfort_tags = self.ai_metadata.get("comfort_food", [])

        mood_str = ", ".join(mood_tags) if mood_tags else ""
        taste_str = ", ".join(taste_tags) if taste_tags else ""
        texture_str = ", ".join(texture_tags) if texture_tags else ""
        occasion_str = ", ".join(occasion_tags) if occasion_tags else ""
        comfort_str = ", ".join(comfort_tags) if comfort_tags else ""

        # Build embedding text with semantic emphasis
        parts = [
            f"{self.name}",
            f"Category: {self.category}",
            f"Cuisine: {cuisine_str}",
            f"Description: {self.description}",
            f"Dietary: {dietary_str}. {dietary_str}",  # Repeat for emphasis
            f"Ingredients: {ingredients_str}",
            f"Meal types: {meal_types_str}",
            f"Preparation: {prep_str}",
            f"Spice level: {self.spice_level}/5",
            f"Taste: {taste_str}",
            f"Texture: {texture_str}",
            f"Mood: {mood_str}",
            f"Occasion: {occasion_str}",
            f"Comfort food: {comfort_str}",
        ]

        # Filter out empty parts
        text = ". ".join(part for part in parts if part and any(c != ":" for c in part.split(": ")[-1]))
        return text + "."
    
    


# --- 2. API Request Models ---

class FoodSearchRequest(BaseModel):
    """Manual food item search request with filters."""

    # Pre-filtering by restaurant
    restaurant_ids: List[str] = Field(default_factory=list, description="Filter to specific restaurants")

    # Keyword search
    query: Optional[str] = None

    # Strict Filters
    dietary: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)  # Items to exclude
    category: Optional[str] = None
    cuisine: List[str] = Field(default_factory=list)
    meal_types: List[str] = Field(default_factory=list)

    # Optional Preferences
    price: Optional[int] = None
    spice_level: Optional[int] = None  # Exact or minimum level
    max_prep_time: Optional[int] = None  # Maximum preparation time in minutes

    # User identification (for preference injection)
    userID: Optional[str] = None

    # Pagination
    limit: int = 10
    offset: int = 0


class FoodVectorSearchRequest(BaseModel):
    """Vector-based semantic food search request."""

    query: str = Field(..., description="Natural language search query (e.g., 'spicy vegetarian main course')")
    restaurant_ids: List[str] = Field(default_factory=list, description="Optional: pre-filter to specific restaurants")
    limit: int = Field(default=5, ge=1, le=100)
    num_candidates: int = Field(default=20, ge=1, le=200, description="Number of candidates to rerank")


# --- 3. API Response Models ---

class FoodSearchResponse(BaseModel):
    """API response for food search results."""

    food_id: str
    name: str
    description: str
    restaurant_id: str

    # Display Info
    category: str
    cuisine: List[str]
    meal_types: List[str]
    price: float
    spice_level: int

    # Dietary & Allergen Info
    dietary: List[str]
    allergens: List[str]
    vegetarian_friendly: bool
    vegan_friendly: bool
    gluten_free: bool

    # Popularity
    is_signature_dish: bool
    is_popular: bool
    rating: Optional[float]

    # Relevance (for semantic search)
    match_score: Optional[float] = None  # From manual filtering
    rerank_score: Optional[float] = None  # From vector search reranking

    @classmethod
    def from_entity(cls, entity: FoodItemEntity, match_score: float = 0.0, rerank_score: Optional[float] = None):
        """Helper to map FoodItemEntity → FoodSearchResponse"""
        return cls(
            food_id=entity.food_id,
            name=entity.name,
            description=entity.description,
            restaurant_id=entity.restaurant_id,
            category=entity.category,
            cuisine=entity.cuisine,
            meal_types=entity.meal_types,
            price=entity.price,
            spice_level=entity.spice_level,
            dietary=entity.dietary,
            allergens=entity.allergens,
            vegetarian_friendly=entity.vegetarian_friendly,
            vegan_friendly=entity.vegan_friendly,
            gluten_free=entity.gluten_free,
            is_signature_dish=entity.is_signature_dish,
            is_popular=entity.is_popular,
            rating=entity.rating,
            match_score=match_score,
            rerank_score=rerank_score,
        )


# --- 4. Internal Result Wrapper ---

class FoodSearchResult:
    """Lightweight wrapper: repository result with dynamic scoring metadata."""

    def __init__(self, entity: FoodItemEntity, match_score: float = 0.0):
        self.entity = entity
        self.match_score = match_score
        self.rerank_score: Optional[float] = None  # Added by reranker
