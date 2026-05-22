"""Evaluation tests for restaurant vector search quality."""
import os
from openai import AsyncOpenAI
import pytest
from app.evaluation.eval_helpers import (
    calculate_precision_at_k,
    calculate_mrr,
    calculate_recall_at_k,
    calculate_ndcg,
)
from app.services.hybrid_search_service import HybridSearchService
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.restaurant_reranker import RestaurantRerankerAdapter
from app.repositories.mongo_restaurant_repo import MongoRestaurantRepository


# Restaurant ID mapping (order from restaurants.json)
RESTAURANTS = {
    "restaurant_1": "24hr Vegan Diner",
    "restaurant_2": "Vegan Kitchen",
    "restaurant_3": "Purely Vegan Hub",
    "restaurant_4": "The Green Leaf Bistro",
    "restaurant_5": "Standard Grill & Bar",
    "restaurant_6": "Sultan's Halal Kitchen",
    "restaurant_7": "The Kosher Deli",
    "restaurant_8": "Sky & Stars Rooftop Lounge",
    "restaurant_9": "The Cozy Study Cafe",
    "restaurant_10": "Sunday Brunch House",
    "restaurant_11": "Spice & Rhythm Indian Kitchen",
    "restaurant_12": "The Night Owl Diner",
    "restaurant_13": "Green Garden Bistro",
    "restaurant_14": "Family Feast Pizzeria",
    "restaurant_15": "The Sushi Master",
    "restaurant_16": "Street Tacos Express",
    "restaurant_17": "The Gluten-Free Haven",
    "restaurant_18": "The Jazz Corner Bar & Grill",
    "restaurant_19": "Bubble Tea Paradise",
    "restaurant_20": "The Steakhouse Prime",
    "restaurant_21": "Tropical Smoothie Bowl Café",
}


# Define a "Golden Dataset" mapping queries to the exact IDs that SHOULD rank high
GOLDEN_EVAL_CASES = [
    # ===== DIETARY/CUISINE SPECIFICITY =====
    {
        "name": "TC1.1: Vegan Options",
        "query": "looking for vegan food",
        "expected_top_ids": ["restaurant_13", "restaurant_3", "restaurant_1"],  # Green Garden, Purely Vegan, 24hr Vegan
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    {
        "name": "TC1.2: Halal Food",
        "query": "I want halal certified food",
        "expected_top_ids": ["restaurant_6"],  # Sultan's Halal Kitchen
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    {
        "name": "TC1.3: Indian Food",
        "query": "Indian restaurant with vegetarian options",
        "expected_top_ids": ["restaurant_11"],  # Spice & Rhythm Indian
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 0.5,
    },
    {
        "name": "TC1.4: Japanese/Sushi",
        "query": "sushi or Japanese cuisine",
        "expected_top_ids": ["restaurant_15"],  # The Sushi Master
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    # ===== OCCASION/VIBE QUERIES =====
    {
        "name": "TC2.1: Romantic Date Night",
        "query": "romantic date night spot with atmosphere",
        "expected_top_ids": ["restaurant_8", "restaurant_15", "restaurant_18"],  # Sky & Stars, Sushi Master, Jazz Corner
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 0.66,  # Top result is romantic
        "min_mrr": 0.5,
    },
    {
        "name": "TC2.2: Group Celebrations",
        "query": "best place for group celebrations and parties",
        "expected_top_ids": ["restaurant_14", "restaurant_11"],  # Family Feast, Spice & Rhythm
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 0.66,
        "min_mrr": 0.5,
    },
    {
        "name": "TC2.3: Work/Study Cafe",
        "query": "quiet place to work or study with good coffee",
        "expected_top_ids": ["restaurant_9"],  # The Cozy Study Cafe
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    # ===== TIME/AVAILABILITY =====
    {
        "name": "TC3.1: Late Night 24/7",
        "query": "open 24 hours late night food",
        "expected_top_ids": ["restaurant_1", "restaurant_12"],  # 24hr Vegan Diner, Night Owl Diner
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    {
        "name": "TC3.2: Breakfast/Brunch",
        "query": "best breakfast or brunch spot",
        "expected_top_ids": ["restaurant_10", "restaurant_9"],  # Sunday Brunch House, Cozy Study Cafe
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 0.66,
        "min_mrr": 0.5,
    },
    # ===== AMENITY/EXPERIENCE =====
    {
        "name": "TC4.1: Live Music",
        "query": "restaurant with live music venue",
        "expected_top_ids": ["restaurant_18", "restaurant_11", "restaurant_8"],  # Jazz Corner, Spice & Rhythm, Sky & Stars
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    # ===== BUDGET/PRICE =====
    {
        "name": "TC5.1: Budget Quick Lunch",
        "query": "budget friendly quick lunch under 15 dollars",
        "expected_top_ids": ["restaurant_16", "restaurant_19"],  # Street Tacos, Bubble Tea
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 0.66,
        "min_mrr": 0.5,
    },
    {
        "name": "TC5.2: Fine Dining Premium",
        "query": "fine dining premium experience special occasion",
        "expected_top_ids": ["restaurant_20", "restaurant_15"],  # Steakhouse Prime, Sushi Master
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 0.5,
    },
    # ===== CUISINE COMBINATIONS =====
    {
        "name": "TC6.1: Italian Pizza Family",
        "query": "Italian pizza family friendly",
        "expected_top_ids": ["restaurant_14"],  # Family Feast Pizzeria
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    {
        "name": "TC6.2: Mexican Street Food",
        "query": "Mexican street food casual",
        "expected_top_ids": ["restaurant_16"],  # Street Tacos Express
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    # ===== HEALTH/WELLNESS =====
    {
        "name": "TC7.1: Healthy Plant-Based",
        "query": "healthy plant based vegan organic",
        "expected_top_ids": ["restaurant_13", "restaurant_21"],  # Green Garden Bistro, Smoothie Bowl
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
    {
        "name": "TC7.2: Gluten-Free Safe",
        "query": "gluten free safe dining certified",
        "expected_top_ids": ["restaurant_17"],  # The Gluten-Free Haven
        "allowed_ids": list(RESTAURANTS.keys()),
        "min_precision_at_1": 1.0,
        "min_mrr": 1.0,
    },
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", GOLDEN_EVAL_CASES)
async def test_search_quality_evals(setup_hybrid_search, case):
    """Automated Vector Search Evaluation Suite with Precision, MRR, Recall, NDCG metrics."""
    hybrid_search = setup_hybrid_search

    print(f"\n{'='*70}")
    print(f"📊 {case['name']}")
    print(f"Query: '{case['query']}'")
    print(f"{'='*70}")

    # Run the vector search pipeline
    results = await hybrid_search.search(
        query=case["query"],
        entity_ids=case["allowed_ids"],
        limit=5,
        num_candidates=20,
    )

    # Extract restaurant IDs from results
    actual_ids = [r.restaurant_id if hasattr(r, "restaurant_id") else r["restaurant_id"] for r in results]

    # Calculate metrics
    p1 = calculate_precision_at_k(actual_ids, case["expected_top_ids"], k=1)
    p3 = calculate_precision_at_k(actual_ids, case["expected_top_ids"], k=3)
    mrr = calculate_mrr(actual_ids, case["expected_top_ids"])
    recall_5 = calculate_recall_at_k(actual_ids, case["expected_top_ids"], k=5)
    ndcg_5 = calculate_ndcg(actual_ids, case["expected_top_ids"], k=5)

    # Log results
    print(f"Expected Top IDs: {[RESTAURANTS.get(id, id) for id in case['expected_top_ids']]}")
    print(f"Actual Top 3 IDs: {[RESTAURANTS.get(id, id) for id in actual_ids[:3]]}")
    print(f"\nMetrics:")
    print(f"  Precision@1: {p1:.2f} (min: {case['min_precision_at_1']:.2f})")
    print(f"  Precision@3: {p3:.2f}")
    print(f"  MRR:         {mrr:.2f} (min: {case['min_mrr']:.2f})")
    print(f"  Recall@5:    {recall_5:.2f}")
    print(f"  NDCG@5:      {ndcg_5:.2f}")

    # Assertions: Quality guardrails
    assert p1 >= case["min_precision_at_1"], (
        f"❌ Failed Precision@1 for '{case['query']}'. "
        f"Expected {case['expected_top_ids']}, got {actual_ids[0] if actual_ids else 'no results'}"
    )
    assert mrr >= case["min_mrr"], (
        f"❌ Failed MRR for '{case['query']}'. "
        f"First relevant result too far: {actual_ids}"
    )

    print(f"✅ PASSED\n")