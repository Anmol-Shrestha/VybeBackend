# Restaurant Service Definition
┌────────────────────────────────────────────────────────┐
│                 Incoming HTTP Request                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
  1. Top Layer:   @router.get("/restaurants")
                  Requires: Depends(get_restaurant_search_service)
                                   │
                                   ▼
  2. Service Layer:  get_restaurant_search_service()
                     Requires: Depends(get_mongo_repository)
                     Requires: Depends(get_reranker_adapter)
                                   │
                                   ▼
  3. Infra Layer:       get_mongo_repository()  ──► Requires: Depends(get_db_client)
                        get_reranker_adapter()  ──► Requires: Inits CrossEncoder
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │  FastAPI resolves the entire tree, executes your route │
       │  logic, and tears down/closes connections cleanly!     │
       └────────────────────────────────────────────────────────┘

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

