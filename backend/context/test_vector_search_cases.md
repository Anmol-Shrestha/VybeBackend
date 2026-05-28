# Vector Search Test Cases for Restaurant Discovery

## Persona: Regular Customer (No dietary restrictions - can eat anything)
This persona tests semantic relevance across diverse query types.

---

## Test Case Categories

### Category 1: Dietary/Cuisine Specificity

#### TC1.1: "I'm looking for vegan options"
**Expected Top 3:**
1. ✅ Green Garden Bistro (100% vegan, modern)
2. ✅ Purely Vegan Hub (vegan focused)
3. ✅ 24hr Vegan Diner (24-hour vegan)

**Reason:** All have "vegan" in dietary + description/metadata

---

#### TC1.2: "Give me halal food"
**Expected Top 3:**
1. ✅ Sultan's Halal Kitchen (halal certified)
2. ⚠️ Spice & Rhythm Indian (vegetarian/vegan options, but not halal-specific)
3. ⚠️ Family Feast Pizzeria (vegetarian options)

**Reason:** Only Sultan's Halal is certified. Others are fallback matches.

---

#### TC1.3: "I want kosher"
**Expected Top 2:**
1. ✅ The Kosher Deli (Glatt Kosher certified)
2. (No strong alternative - very niche)

**Reason:** Only one kosher option in dataset.

---

#### TC1.4: "Indian food with vegetarian options"
**Expected Top 2:**
1. ✅ Spice & Rhythm Indian Kitchen (vegetarian/vegan/regular, live music, buffet)
2. ✅ The Green Leaf Bistro (vegetarian Italian - fallback)

**Reason:** Primary match on "Indian" + vegetarian availability.

---

#### TC1.5: "Sushi or Japanese cuisine"
**Expected Top 1:**
1. ✅ The Sushi Master (premium omakase, Japanese)

**Reason:** Direct cuisine match + authentic descriptor.

---

### Category 2: Occasion/Vibe-Based Queries

#### TC2.1: "Looking for a romantic date night spot"
**Expected Top 3:**
1. ✅ Sky & Stars Rooftop Lounge (romantic, upscale, city views)
2. ✅ The Sushi Master (intimate, special occasions)
3. ✅ The Jazz Corner Bar & Grill (intimate, live jazz, romantic)

**Reason:** All have "romance", "intimate", "special occasion" in metadata/description.

---

#### TC2.2: "Best place for group celebrations and parties"
**Expected Top 3:**
1. ✅ Family Feast Pizzeria (kids menu, large tables, parties, 120 capacity)
2. ✅ Spice & Rhythm Indian Kitchen (group dinners, 90 capacity, buffet)
3. ✅ Sky & Stars Rooftop Lounge (special occasions, 75 capacity)

**Reason:** "Family", "party", "celebration", large capacity explicitly mentioned.

---

#### TC2.3: "I want to work or study with good coffee"
**Expected Top 2:**
1. ✅ The Cozy Study Cafe (quiet, wifi, productive, study sessions)
2. ✅ Bubble Tea Paradise (student hangout, modern, social)

**Reason:** "Work", "study", "cafe", "productive" in metadata.

---

### Category 3: Time/Availability Queries

#### TC3.1: "Open 24 hours, late night food"
**Expected Top 3:**
1. ✅ 24hr Vegan Diner (24/7 explicit, late night, always open)
2. ✅ The Night Owl Diner (24/7 explicit, late night, classic diner)
3. ✅ Standard Grill & Bar (opens 4pm, goes to midnight - late night option)

**Reason:** "24 hour" and "late night" in meal_types or ai_metadata.

---

#### TC3.2: "Breakfast or brunch spot"
**Expected Top 3:**
1. ✅ Sunday Brunch House (brunch specialist, eggs benedict, pancakes)
2. ✅ The Cozy Study Cafe (breakfast, brunch, morning vibe)
3. ✅ Tropical Smoothie Bowl Café (breakfast, brunch, health-focused)

**Reason:** "Breakfast", "brunch" in meal_types + relevant description.

---

### Category 4: Amenity/Experience Queries

#### TC4.1: "Live music venue with food"
**Expected Top 3:**
1. ✅ The Jazz Corner Bar & Grill (live jazz nightly)
2. ✅ Spice & Rhythm Indian Kitchen (live sitar on weekends)
3. ✅ Sky & Stars Rooftop Lounge (live music, upscale)

**Reason:** has_live_music: true + music/atmosphere in metadata.

---

#### TC4.2: "Restaurant with parking"
**Expected Multiple Matches:**
1. ✅ Standard Grill & Bar
2. ✅ Sultan's Halal Kitchen
3. ✅ Sky & Stars Rooftop Lounge
4. ✅ The Night Owl Diner
5. ✅ Sunday Brunch House
6. ✅ Family Feast Pizzeria
7. ✅ The Jazz Corner Bar & Grill
8. ✅ The Steakhouse Prime
9. ✅ 24hr Vegan Diner
10. ✅ Purely Vegan Hub
11. ✅ The Green Leaf Bistro

**Reason:** These have has_parking: true. But semantic search shouldn't rank ALL of them - 
should prioritize those where parking is mentioned or lifestyle-relevant (family, business).

---

### Category 5: Budget/Price-Based Queries

#### TC5.1: "Budget-friendly quick lunch under $15"
**Expected Top 3:**
1. ✅ Street Tacos Express ($12, quick, lunch)
2. ✅ Bubble Tea Paradise ($8, quick, student-friendly)
3. ✅ The Cozy Study Cafe ($15, budget-friendly)

**Reason:** Low price_max + "quick", "budget", "lunch" in description/metadata.

---

#### TC5.2: "Fine dining, special occasion, premium experience"
**Expected Top 2:**
1. ✅ The Steakhouse Prime ($100, USDA Prime, upscale, caviar)
2. ✅ The Sushi Master ($80, omakase, premium sake, intimate)

**Reason:** High price_max + "fine dining", "upscale", "premium" in description.

---

### Category 6: Cuisine Combinations

#### TC6.1: "Italian pizza, family-friendly"
**Expected Top 2:**
1. ✅ Family Feast Pizzeria (Italian, pizza, family, 120 capacity)
2. ✅ The Green Leaf Bistro (Italian, but vegetarian/salads - secondary)

**Reason:** "Pizza", "Italian", "family" match.

---

#### TC6.2: "Mexican street food, casual"
**Expected Top 1:**
1. ✅ Street Tacos Express (Mexican, authentic street tacos, casual)

**Reason:** Direct cuisine + casual atmosphere match.

---

### Category 7: Health/Wellness Queries

#### TC7.1: "Healthy, plant-based, vegan options"
**Expected Top 3:**
1. ✅ Green Garden Bistro (100% plant-based, organic, sustainable)
2. ✅ Tropical Smoothie Bowl Café (health-conscious, açaí, smoothies)
3. ✅ 24hr Vegan Diner (vegan, plant-based)

**Reason:** "Healthy", "plant-based", "vegan", "wellness" in metadata.

---

#### TC7.2: "Gluten-free safe dining"
**Expected Top 2:**
1. ✅ The Gluten-Free Haven (dedicated gluten-free, certified prep areas)
2. ✅ Tropical Smoothie Bowl Café (gluten-free available)

**Reason:** Explicit "gluten-free" in dietary + safety messaging.

---

## Evaluation Metrics

### For Each Test Case:
- **Precision@3**: Are top 3 results relevant?
- **Recall**: Are all truly relevant restaurants included in top-K?
- **MRR (Mean Reciprocal Rank)**: Position of first relevant result
- **NDCG (Normalized Discounted Cumulative Gain)**: Ranking quality

### Success Criteria:
- ✅ **Excellent (80-100%)**: Top result is clearly correct
- ⚠️ **Good (60-80%)**: Top 3 contains expected results
- ❌ **Poor (<60%)**: Misses obvious relevant restaurants

---

## Edge Cases to Test

#### EC1: Ambiguous Queries
- "Asian" → Should return: Japanese (Sushi Master), Indian (Spice & Rhythm), Korean (Vegan Kitchen)
- "Comfort food" → Should return: The Night Owl Diner, Family Feast Pizzeria, Standard Grill & Bar

#### EC2: Negation/Exclusion (Future)
- "No meat, vegan only" → Should heavily weight vegan restaurants
- "Not fast food" → Should deprioritize street tacos, bubble tea

#### EC3: Compound Queries
- "Vegan Indian restaurant with live music" → Spice & Rhythm (vegetarian/vegan available, live music)
- "Late night romantic dinner" → The Jazz Corner Bar & Grill (late night, jazz, romantic vibe)

---

## Data Quality Notes

### Current Dataset Strengths:
✅ Rich ai_metadata with atmosphere, vibe_tags, best_for
✅ Diverse cuisines and dietary options
✅ Detailed descriptions for semantic matching
✅ Multiple meal types per restaurant
✅ Amenity flags (parking, live_music)

### Current Dataset Weaknesses:
⚠️ Service hours in mixed formats (string vs. minutes from midnight)
⚠️ Some restaurants have very similar descriptions (Korean Vegan Kitchen and Purely Vegan Hub)
⚠️ Limited "budget" vs "premium" explicit tags in descriptions
⚠️ No review/rating-based semantic data (e.g., "highly rated", "customer favorite")

---

## Do We Need Evals?

### YES, for these reasons:

1. **Embedding Quality Check**: Confirm OpenAI embeddings capture semantic intent
   - Run test queries, log similarity scores, ensure top matches have high scores (>0.75)

2. **Cross-Encoder Re-ranker Validation**:
   - Verify re-ranker actually improves ordering
   - Compare: Raw embedding scores vs. cross-encoder scores

3. **Identify Embedding Failure Modes**:
   - Which queries fail? (e.g., "red wine pairing" - not in our data)
   - Which restaurants are confused? (e.g., similar descriptions)

4. **Continuous Improvement**:
   - Track embedding effectiveness as we add new restaurants
   - Detect when semantic changes break matching (e.g., new cuisine types)

### Recommended Eval Framework:

```
For each test case:
  1. Run query → Get embeddings
  2. Log vector similarity (0-100%)
  3. Log cross-encoder re-rank scores
  4. Measure: Precision@1, Precision@3, MRR
  5. Report: Pass/Fail threshold
  
Example:
Query: "vegan options"
- Vector Sim (Green Garden Bistro): 87% ✅
- Vector Sim (Standard Grill): 15% ✅ (correctly low)
- Reranker score (Green Garden): 0.95 ✅
- Result: PASS (top result correct, high confidence)
```

---

## Summary

- **18 comprehensive test cases** covering 7 categories
- **5 edge cases** for boundary testing
- **Evaluation framework** with precision metrics
- **Clear success criteria** (80%+ semantic relevance)

This tests the vector search in isolation without distance constraints, letting us validate that semantic matching works across diverse query intents and restaurant types.