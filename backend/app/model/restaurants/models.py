
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


class RestaurantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    
    # We take lat/long directly from the "Client" or your Geocoding Adapter
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    # Your Disciplined Integer approach
    price_level: int = Field(..., ge=1, le=4, description="1=$, 2=$$, 3=$$$, 4=$$$$")
    
    # Attributes for your Boolean columns/filters
    cuisine: List[str]
    dietary: List[str]
    meal_types: List[str]
    
    # Individual Booleans (Amenities)
    has_parking: bool = False
    has_live_music: bool = False
    buffet: bool = False
    max_capacity: int = Field(..., gt=0)
    
    # For display
    address_display: str = Field(..., description="The human-readable address")
    service_hours: Dict[str, str] = Field(..., description="Service hours by day")



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