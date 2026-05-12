"""Concrete MongoDB implementation of RestaurantRepository."""

from datetime import datetime
from app.repositories.restaurant_repo import RestaurantRepository
from app.model.restaurants.models import RestaurantEntity, GeoLocation
from app.db.client import db


class MongoRestaurantRepository(RestaurantRepository):
    def __init__(self):
        self.collection = db["restaurants"]

    async def filter_restaurants(self, criteria: dict, bypass_hours: bool = False) -> list[RestaurantEntity]:
        """
        Executes the 5-stage aggregation pipeline:
        1. $geoNear: Proximity filter with dietary query
        2. $match: Strict dietary re-check
        3. $addFields: Compute match_score (parking + live music)
        4. $match: Temporal/service hours check (skipped if bypass_hours=True)
        5. $sort + $limit: Score DESC, distance ASC, limit 20
        """
        latitude = criteria.get("latitude", 0)
        longitude = criteria.get("longitude", 0)
        radius_km = criteria.get("radius_km", 5)
        dietary = criteria.get("dietary", [])
        has_parking = criteria.get("has_parking", False)
        has_live_music = criteria.get("has_live_music", False)

        # Get current day and time for temporal matching
        now = datetime.now()
        day_name = now.strftime("%A")
        current_minutes = now.hour * 60 + now.minute

        pipeline = [
            # Stage 1: $geoNear — proximity filter with dietary query for perf
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "distanceField": "distance_km",
                    "distanceMultiplier": 0.001,
                    "maxDistance": radius_km * 1000,  # Convert km to meters
                    "spherical": True,
                    "query": {"dietary": {"$in": dietary}} if dietary else {}
                }
            },

            # Stage 2: $match — strict dietary re-check
            {
                "$match": {
                    "dietary": {"$in": dietary}
                } if dietary else {}
            } if dietary else {"$match": {}},

            # Stage 3: $addFields — compute match_score
            {
                "$addFields": {
                    "match_score": {
                        "$add": [
                            {
                                "$cond": [
                                    {"$eq": ["$has_parking", has_parking]},
                                    1,
                                    0
                                ]
                            },
                            {
                                "$cond": [
                                    {"$eq": ["$has_live_music", has_live_music]},
                                    1,
                                    0
                                ]
                            }
                        ]
                    }
                }
            },
        ]

        # Stage 4: $match — temporal/service hours check (optional, can be bypassed)
        if not bypass_hours:
            pipeline.append({
                "$match": {
                    "$expr": {
                        "$let": {
                            "vars": {
                                "hours": f"$service_hours.{day_name}"
                            },
                            "in": {
                                "$cond": [
                                    {"$eq": ["$$hours", None]},
                                    False,  # Not open today
                                    {
                                        "$cond": [
                                            {"$lt": ["$$hours.close", "$$hours.open"]},
                                            # Overnight case: open at 11pm, close at 2am
                                            {
                                                "$or": [
                                                    {"$gte": [current_minutes, "$$hours.open"]},
                                                    {"$lt": [current_minutes, "$$hours.close"]},
                                                ]
                                            },
                                            # Normal case
                                            {
                                                "$and": [
                                                    {"$gte": [current_minutes, "$$hours.open"]},
                                                    {"$lt": [current_minutes, "$$hours.close"]},
                                                ]
                                            },
                                        ]
                                    },
                                ]
                            }
                        }
                    }
                }
            })

        # Stage 5: $sort + $limit
        pipeline.extend([
            {
                "$sort": {
                    "match_score": -1,  # DESC
                    "distance_km": 1    # ASC
                }
            },
            {
                "$limit": 20
            }
        ])

        # Remove empty $match stages
        pipeline = [stage for stage in pipeline if stage != {"$match": {}}]

        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=20)

        # Transform to RestaurantEntity
        entities = []
        for doc in results:
            # Convert location dict to GeoLocation
            location = GeoLocation(
                type=doc["location"].get("type", "Point"),
                coordinates=doc["location"].get("coordinates", [0, 0])
            )

            entity = RestaurantEntity(
                restaurant_id=doc["restaurant_id"],
                name=doc["name"],
                slug=doc["slug"],
                description=doc["description"],
                location=location,
                rating=doc.get("rating", 0),
                cuisine=doc.get("cuisine", []),
                dietary=doc.get("dietary", []),
                meal_types=doc.get("meal_types", []),
                max_capacity=doc.get("max_capacity", 0),
                has_parking=doc.get("has_parking", False),
                has_live_music=doc.get("has_live_music", False),
                price_max=doc.get("price_max", 0),
                service_hours=doc.get("service_hours", {}),
                ai_metadata=doc.get("ai_metadata", {})
            )
            entities.append(entity)

        return entities
