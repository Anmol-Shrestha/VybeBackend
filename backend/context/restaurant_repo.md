Responsibility

Handles all direct communication with the MongoDB restaurants collection using native PyMongo Async.
Required Indexes

    Type: 2dsphere on the location field.

    Purpose: Required for $geoNear distance and proximity calculations.


This is what the retaurant_service will get, if you dont see the dietary field, then you need to call the user collection to fetch the dietary since wihtout dietary or allergen the search would be incomplete.
 {
        "name": "Mr.Vegan",
        "userID":123123,
        "latitude": 43.77579,
        "longitude": -79.20664,
        "dietary": [],
        "allergen":[],
        "cuisine":[],
        "meal_type":[],
        "price_max":30,
        "min_rating":4,
        "min_capacity":4,
        "has_parking":True,
        "live_music": True,
    }

In the service layer, since the dietary and allergen field is not present, service will make a call to user collection which will give it acces to dietary field and allergen field.
you need to get them both and merge it with the incomplete object.
    {
        "name": "Mr.Vegan",
        "userID":123123,
        "dietary": "vegan",
        "allergen":["nut, dairy, gluten"]
    }

After we have a complete obejct which looks like this:
 {
        "name": "Mr.Vegan",
        "userID":123123,
        "latitude": 43.77579,
        "longitude": -79.20664,
        "dietary": ['vegan'],
        "allergen":['nut', dairy', 'gluten'],
        "cuisine":[],
        "meal_type":[],
        "price_max":30,
        "min_rating":4,
        "min_capacity":4,
        "has_parking":True,
        "live_music": True,
    }

Service will call the resturant_repo method called filter_by_restaurants
This is what the resturant for Vegan is supposed ot return since
{
  "name": "Purely Vegan Hub",
  "address_display": "92 Botany, Scarborough, ON M5T 2L8",
  "description": "A casual takeout and dine-in spot specializing in Korean-inspired street food like fried chicken, corn dogs, and kimchi fries. Popular for relaxed hangouts and quick bites in Kensington Market.",
  "latitude": 43.65518646485583, 
  "longitude": -79.40210001991301,



  "price_max": 20, 
  "cuisine": ["american"],
  "dietary": ["vegan"],
  "meal_types": ["Brunch", "Lunch", "Dinner", "Late Night"],
  "has_parking": true,
  "has_live_music": true,
  "max_capacity": 20,
  "service_hours": {
  "Monday": { "open": 720, "close": 1140 },  
  "Tuesday": { "open": 720, "close": 1140 },
  "Friday": { "open": 720, "close": 1440 },  
  "Saturday": { "open": 720, "close": 1440 },
  "Sunday": { "open": 720, "close": 1440 }
  },
  



  "ai_metadata": {
    "atmosphere": ["Casual Hangout", "Quick Bites", "Student Friendly"],
    "vibe_tags": ["Modern", "Cute", "Casual", "Trendy", "Instagram-friendly"],
    "best_for": ["Quick grab-and-go", "Food explorers"]
  }
}

The Discovery Pipeline (Master Aggregation)

The repository must implement a single search_aggregate method that executes the following stages in strict order:
1. Stage: $geoNear (Proximity)

    Input: Coordinates [long, lat] and maxDistance in meters.

    Output: Injects distance_km field (use distanceMultiplier: 0.001).

    Filter: Apply the dietary requirement here inside the query parameter for performance.

2. Stage: $match (Allergen Exclusion)

    Logic: Strictly exclude any restaurant where the dietary array does not contain user's dietary preference found in the dietary field

3. Stage: $addFields (Ranking Score)

    Logic: Create a match_score integer.

    Weighting: - If has_parking matches user preference: +1

        If live_music matches user preference: +1

        Future-proofing: Leave room for AI-based vibe scores here.

4. Stage: $match (Temporal/Status)

    Logic: Use the "Minutes from Midnight" logic to check if service_hours matches the current_time_minutes.

5. Stage: $sort & $limit

    Primary Sort: match_score (Descending).

    Secondary Sort: distance_km (Ascending).

    Limit: Default to top 20 results.