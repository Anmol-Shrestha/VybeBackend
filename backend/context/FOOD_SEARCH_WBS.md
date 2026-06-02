# Food Search Service - Work Breakdown Structure

## Overview
Implement a Food Search service mirroring the Restaurant Search architecture with manual filters + vector/semantic search.

---

## Phase 1: Data Model & Entity Design

### 1.1 FoodItemEntity (backend/app/model/food/models.py)
```
Attributes needed:
- food_id: str (unique identifier)
- restaurant_id: str (relationship to restaurant)
- name: str (food name)
- description: str (detailed description)
- category: str (appetizer, main course, dessert, beverage, etc.)
- cuisine: List[str] (Italian, Asian, Mexican, etc.)
- dietary: List[str] (vegan, vegetarian, gluten-free, dairy-free, etc.)
- allergens: List[str] (nuts, shellfish, dairy, soy, etc.)
- ingredients: List[str] (for filtering/searching)
- spice_level: int (0-5 scale)
- preparation_method: List[str] (grilled, fried, baked, raw, etc.)
- meal_types: List[str] (breakfast, lunch, dinner, snack)
- price: float (cost per item)
- calories: Optional[int] (nutritional info)
- vegetarian_friendly: bool
- vegan_friendly: bool
- gluten_free: bool
- is_signature_dish: bool
- is_popular: bool
- rating: Optional[float]
- popularity_score: Optional[float] (number of orders)

AI Metadata:
- ai_metadata: Dict[str, List[str]] (informal descriptions, slang, context)
  Examples:
  - "comfort_food": ["mac and cheese", "feels like home"]
  - "mood": ["feel-good", "indulgent", "light"]
  - "occasion": ["date night", "quick lunch", "celebration"]
  - "taste_profile": ["sweet", "savory", "umami", "tangy"]
  - "texture": ["crispy", "creamy", "chewy", "tender"]

Vector Embeddings:
- vector_embeddings: Optional[List[float]] (1536 dims from OpenAI)
- embedding_model: str ("text-embedding-3-small")
- embedding_dimensions: int (1536)
- embedding_source: str (the text that was embedded)
- embedding_timestamp: datetime
```

### 1.2 Request/Response Models (backend/app/model/food/models.py)
- `FoodSearchRequest` - for manual filter search
- `FoodVectorSearchRequest` - for semantic search (query + optional restaurant_ids)
- `FoodSearchResponse` - API response model

---

## Phase 2: Database & Repository Layer

### 2.1 MongoDB Collection Setup
- Create `food` collection in MongoDB
- Add indexes:
  - `restaurant_id` (for filtering by restaurant)
  - `dietary`, `allergens`, `category`, `cuisine` (for faceted search)
  - `2dsphere` geospatial index via restaurant location join
  - Vector index for `vector_embeddings` (MongoDB Atlas Vector Search)

### 2.2 MongoFoodRepository (backend/app/repositories/mongo_food_repo.py)
**Methods needed:**

```python
async def filter_food_items(
    filter_request: FoodSearchRequest,
    restaurant_ids: List[str] = None
) -> List[FoodSearchResult]
# MongoDB aggregation pipeline:
# - $match: filter by dietary, allergens, category, price range
# - $addFields: calculate match_score (dietary matches, allergens avoidance)
# - $sort: by match_score DESC
# - Constraint: only search within restaurant_ids if provided

async def vector_search_by_ids(
    food_ids: List[str],
    query_embedding: List[float],
    limit: int = 10,
    num_candidates: int = 100
) -> List[FoodSearchResult]
# MongoDB $vectorSearch:
# - Filter by food_ids (pre-filtered results)
# - Vector similarity search on embeddings
# - Return top candidates for reranking
```

### 2.3 FoodSearchResult Class
```python
class FoodSearchResult:
    def __init__(self, entity: FoodItemEntity, match_score: float = 0.0):
        self.entity = entity
        self.match_score = match_score
        self.rerank_score = None  # Added by reranker
```

---

## Phase 3: Service Layer

### 3.1 FoodService (backend/app/services/food_service.py)
- Manual filter-based search
- Similar to RestaurantService
- Preference injection (user dietary preferences, allergies)
- Handles both authenticated & anonymous searches

### 3.2 FoodSearchService (backend/app/services/food_search_service.py)
- Wrapper around HybridSearchService for food items
- Converts FoodSearchResult → FoodSearchResponse
- **Rerank score threshold: -2.0** (filter poor matches)
- Returns semantic ranked food items

---

## Phase 4: Adapter Layer

### 4.1 FoodRerankerAdapter (backend/app/pipeline_models/food_reranker.py)
- Similar to RestaurantRerankerAdapter
- Uses same cross-encoder model (ms-marco-MiniLM-L-6-v2)
- Compose food text from: name + description + ingredients + dietary + allergens + ai_metadata
- Returns reranked food items

### 4.2 Reuse Existing Adapters
- `OpenAIEmbeddingAdapter` (already exists, reuse)
- `HybridSearchService` (already exists, reuse generically)

---

## Phase 5: Data Seeding

### 5.1 Food Data Creation (backend/scripts/seed_food_database.py)
**Tasks:**
1. Create comprehensive food dataset (50-100 diverse food items across restaurants)
2. Coverage:
   - All dietary restrictions (vegan, vegetarian, gluten-free, etc.)
   - All allergens
   - All cuisines
   - Different price points
   - Different spice levels
   - Popular & signature dishes
3. Generate OpenAI embeddings for each food item
4. Store with rich ai_metadata for informal queries

**Dataset schema:**
```json
{
  "food_id": "food_123",
  "restaurant_id": "restaurant_2",
  "name": "Spicy Thai Green Curry",
  "description": "Traditional Thai curry with green chilies, coconut milk, and jasmine rice",
  "category": "main_course",
  "cuisine": ["Thai"],
  "dietary": ["vegan"],
  "allergens": ["coconut"],
  "ingredients": ["green chilies", "coconut milk", "jasmine rice", "vegetables"],
  "spice_level": 4,
  "price": 14.99,
  "ai_metadata": {
    "mood": ["adventurous", "warming", "comforting"],
    "occasion": ["dinner", "group meal"],
    "texture": ["creamy", "tender"],
    "taste_profile": ["spicy", "aromatic", "savory"]
  },
  "vector_embeddings": [... 1536 dims ...]
}
```

---

## Phase 6: API Endpoints

### 6.1 Manual Food Search (backend/app/api/v1/food.py)
```
POST /api/v1/food/search
Request:
- query: optional (keyword search in name/description)
- restaurant_ids: List[str] (filter to specific restaurants)
- dietary: List[str]
- allergens: List[str]
- category: Optional[str]
- cuisine: List[str]
- max_price: Optional[float]
- spice_level: Optional[int] (0-5)

Response: List[FoodSearchResponse]
```

### 6.2 Vector Food Search (backend/app/api/v1/food.py)
```
POST /api/v1/food/vector-search
Request:
- query: str ("spicy vegetarian main course", "gluten-free dessert")
- restaurant_ids: List[str] (optional, pre-filter)
- limit: int (default: 5)
- num_candidates: int (default: 20)

Response: List[FoodSearchResponse] (reranked, threshold filtered)
```

---

## Phase 7: Testing & Evaluation

### 7.1 Unit Tests (backend/test/test_food_service.py)
- Test FoodService with various filter combinations
- Test preference injection

### 7.2 Integration Tests (backend/test/test_food_hybrid_search.py)
- Test HybridSearchService with food items
- Test FoodRerankerAdapter
- Test FoodSearchService with threshold

### 7.3 Evaluation Suite (backend/test/test_food_eval.py)
**Golden test cases:**
1. "gluten-free dessert" → returns only gluten-free desserts
2. "spicy vegan curry" → returns spicy vegan mains/curries
3. "romantic appetizer" → returns refined small plates
4. "quick breakfast" → returns fast breakfast items
5. "budget friendly" → returns low-cost items
6. "nut allergy" → excludes all nut-containing items
7. "spicy food" (level 4-5) → high spice level items
8. "light salad" → low-calorie vegetables

**Metrics:** Precision@1, MRR, Recall@5, NDCG@5 (same as restaurants)

---

## Phase 8: Frontend Integration

### 8.1 Food Search Page/Component (frontend/src/components/FoodSearchContainer.jsx)
- Similar to VectorSearchContainer
- Chat interface for semantic food queries
- Display food items with:
  - Name, description
  - Restaurant name
  - Price, spice level, dietary badges
  - Allergen warnings

### 8.2 API Integration (frontend/src/api/food.js)
```javascript
export async function searchFood(params)  // Manual
export async function vectorSearchFood(query, food_ids)  // Vector
```

### 8.3 UI Layout
- Option A: Separate "Food Search" page (like restaurants)
- Option B: Tab-based view (Restaurants | Food)
- Option C: Nested (Click restaurant → see food items)

---

## Phase 9: Deployment & Documentation

### 9.1 Update README
- Add Food Search service documentation
- API endpoint examples

### 9.2 Database Backup
- Backup food collection schema

---

## Timeline Summary (For Tomorrow)

**Day 1 (Phase 1-4):**
- Entity & model design
- Repository implementation
- Service layer
- Adapter (food reranker)

**Day 2 (Phase 5-6):**
- Data seeding
- API endpoints
- Initial testing

**Day 3 (Phase 7-8):**
- Evaluation suite
- Frontend integration
- UI/UX polish

---

## Key Differences from Restaurant Service

| Aspect | Restaurant | Food |
|--------|-----------|------|
| Entity | Location-based | Ingredient-based |
| Primary Filter | Geospatial | Dietary/Allergens |
| AI Metadata | Vibe, ambiance | Taste, texture, occasion |
| Relationship | Standalone | Belongs to Restaurant |
| Vector Search | Location + vibe | Taste + dietary + occasion |
| Threshold | -2.0 | -2.0 (same) |

---

## Reusable Components

✅ `HybridSearchService` - Generic (reuse as-is)
✅ `OpenAIEmbeddingAdapter` - Generic (reuse as-is)
✅ Pattern: Repository → Service → Adapter → API
✅ Evaluation metrics framework
✅ Frontend chat UI pattern

---

## Success Criteria

- [ ] All 8+ golden test cases pass (P@1 ≥ 0.66)
- [ ] Threshold filter prevents poor matches
- [ ] Allergen queries work perfectly (zero false negatives)
- [ ] Vector search captures informal queries ("tasty", "comforting", etc.)
- [ ] API endpoints return <2s response time
- [ ] Frontend smoothly integrated with restaurant view