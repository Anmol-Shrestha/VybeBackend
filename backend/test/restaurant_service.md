# Restaurant Service Definition

## Responsibility
Acts as the orchestrator between the API layer, User Repository, and Restaurant Repository.

## Logic Flow: Preference Injection
- **Input:** `SearchRequest` (may be incomplete).
- **Check:** If `dietary` or `allergens` are null/empty.
- **Action:** If incomplete, call `UserRepo.get_by_id(userID)` to fetch persistent preferences.
- **Merge:** Overwrite request fields with User identity.
- **Output:** Pass "Complete Filter Object" to `RestaurantRepo`.

## Scoring Rules (Ranking)
- **Primary:** Distance (via $geoNear).
- **Secondary:** Boolean Match Boost (+1 score for each matching amenity: Parking, Live Music).
- **Constraint:** Strict exclusion for `dietary` mismatch.

## Constraints
- Must use `pymongo.asynchronous`.
- Must return `RestaurantEntity` objects mapped to `RestaurantResponse`.