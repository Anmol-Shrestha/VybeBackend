
# --- 1. Internal Domain Entity ---
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class GeoLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[Longitude, Latitude]")







class RestaurantEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    restaurant_id: str
    name: str
    slug: str
    description: str
    location: GeoLocation
    rating: float

    cuisine: List[str]
    dietary: List[str]
    meal_types: List[str]
    max_capacity: int
    has_parking: bool
    has_live_music: bool
    price_max: int

    service_hours: Dict = Field(default_factory=dict)

    ai_metadata: Dict[str, List[str]] = Field(default_factory=dict)

    # OpenAI's text-embedding-3-small outputs 1536 dimensions by default
    vector_embeddings: Optional[List[float]] = Field(
        default=None, 
        description="1536-dimensional semantic vector representing the restaurant's vibe and description"
    )




# --- 2. API Request Models ---
class RestaurantSearchRequest(BaseModel):
    # User identification (needed for preference injection)
    userID: Optional[str] = None

    # Proximity
    latitude: float
    longitude: float
    radius_km: int = 5

    # Strict Filters
    meal_types: List[str] = []
    cuisine: List[str] = []
    dietary: List[str] = []

    # Optional Preferences
    price_max: Optional[int] = None
    min_rating: float = 0.0
    min_capacity: int = 1

    # Amenities (Defaulting to False as requested)
    has_live_music: bool = False
    has_parking: bool = False
    

# --- 3. API Response Models ---
class RestaurantsSearchResponse(BaseModel): 
    
    restaurant_id: str
    name: str
    latitude: float
    longitude: float
    distance_km: float
    is_open: bool
    is_online: bool = True  # Placeholder for your business logic

    dietary: List[str]
    cuisine: List[str]
    meal_types: List[str]

    price_max: int
    rating: float
    has_parking: bool
    has_live_music: bool
    max_capacity: int

    @classmethod
    def from_entity(cls, entity: RestaurantEntity, distance: float, is_open: bool):
        """Helper to map Entity -> Response"""
        return cls(
            restaurant_id=entity.restaurant_id,
            name=entity.name,
            latitude=entity.location.coordinates[1],
            longitude=entity.location.coordinates[0],
            distance_km=round(distance, 2),
            is_open=is_open,
            dietary=entity.dietary,
            cuisine=entity.cuisine,
            meal_types=entity.meal_types,
            price_max=entity.price_max,
            rating=entity.rating,
            has_parking=entity.has_parking,
            has_live_music=entity.has_live_music,
            max_capacity=entity.max_capacity
        )
        
        
        
        
class RestaurantVectorSearchRequest(BaseModel):
    query:str
    restaurant_ids:List[str]
    limit: int = 10
    num_candidates = int = 100
    
    

