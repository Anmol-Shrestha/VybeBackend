from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class UserEntity(BaseModel):
    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "user_id": "user_001",
                "name": "Mr. Vegan",
                "latitude": 43.7757,
                "longitude": -79.2066,
                "dietary": "Vegan",
                "allergens": ["nut"],
                "requires_wheelchair_access": False
            }
        }
    )

    user_id: str
    name: str

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    dietary: str
    allergens: List[str] = []

    requires_wheelchair_access: bool = False