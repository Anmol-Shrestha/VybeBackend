"""Evaluation tests for food vector search quality.

Parametrized golden dataset evaluation using probabilistic IR metrics:
- Precision@K: fraction of top-K results that are relevant
- MRR: Mean Reciprocal Rank (position of first relevant result)
- Recall@K: coverage of expected items in top-K
- NDCG@K: ranking quality with position decay

Includes CRITICAL safety tests for allergen filtering.
"""

import os
import pytest
from openai import AsyncOpenAI
from pymongo import AsyncMongoClient

from app.evaluation.eval_helpers import (
    calculate_precision_at_k,
    calculate_mrr,
    calculate_recall_at_k,
    calculate_ndcg,
)
from app.services.hybrid_search_service import HybridSearchService
from app.pipeline_models.openai_adapter import OpenAIEmbeddingAdapter
from app.pipeline_models.food_reranker import FoodReranker
from app.repositories.mongo_food_repo import MongoFoodRepository


# Golden dataset: semantic queries with expected food items and quality thresholds
GOLDEN_FOOD_EVAL_CASES = [
    {
        "name": "TC1: Sweet Comforting Late Night Craving",
        "query": "something sweet and comforting for a late night craving",
        "expected_items": ["Apple Pie with Ice Cream"],
        "expected_restaurant_ids": ["restaurant_12"],
        "allergens_to_avoid": [],
        "description": "Tests semantic mapping of abstract mood tags ('sweet', 'comforting') and occasion ('late night') directly to a dessert without using the word pie or cake.",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC2: Spicy Asian Late Night Noodles",
        "query": "spicy asian noodles for a late night meal",
        "expected_items": ["Midnight Pad Thai", "24-Hour Buddha Noodle Soup"],
        "expected_restaurant_ids": ["restaurant_1"],
        "allergens_to_avoid": [],
        "description": "Multi-intent verification. Must filter by occasion ('late night'), category mapping for noodles, cuisine ('thai'/'asian'), and higher spice levels.",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC3: Premium Elegant Seafood Dinner",
        "query": "premium elegant seafood dinner for a special occasion",
        "expected_items": ["Omakase Experience (Chef's Selection)", "Lobster Tail with Drawn Butter"],
        "expected_restaurant_ids": ["restaurant_15", "restaurant_20"],
        "allergens_to_avoid": [],
        "description": "Evaluates luxury vector matching. 'Premium' and 'elegant' should map directly to high-end fine dining text profiles and premium price tiers.",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC4: Crispy Fried Street Food Snack",
        "query": "crispy fried street food style snack",
        "expected_items": ["Crispy Vegan Fried Chicken", "Kimchi Corn Dogs"],
        "expected_restaurant_ids": ["restaurant_2"],
        "allergens_to_avoid": [],
        "description": "Validates intersection of texture ('crispy'), mood ('street-style'), and category ('snack' or main course items with street flags).",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC5: Warming Aromatic Comforting Stew",
        "query": "warming aromatic comforting stew",
        "expected_items": ["Creamy Coconut Curry", "Lamb Mandy", "Butter Chicken Curry"],
        "expected_restaurant_ids": ["restaurant_1", "restaurant_6", "restaurant_11"],
        "allergens_to_avoid": [],
        "description": "Tests purely abstract culinary concepts. 'Warming', 'aromatic', and 'stew' must semantically cluster with curries and slow-cooked rice/broth dishes.",
        "min_precision_at_1": 0.2,
        "min_mrr": 0.2,
    },
    {
        "name": "TC6: Energizing Post-Workout Breakfast Bowl",
        "query": "energizing post-workout breakfast bowl",
        "expected_items": ["Açaí Energy Bowl", "Protein Power Bowl"],
        "expected_restaurant_ids": ["restaurant_21"],
        "allergens_to_avoid": [],
        "description": "Verifies precise health/wellness niche matching. Maps 'post-workout' and 'energizing' straight to the targeted ai_metadata fields.",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC7: Safe Comforting Gluten-Free Dinner",
        "query": "safe comforting gluten-free dinner option",
        "expected_items": ["Gluten-Free Pizza Margherita"],
        "expected_restaurant_ids": ["restaurant_17"],
        "allergens_to_avoid": [],
        "description": "Tests specific lifestyle text alignments where 'safe' matches the 'safe' mood metadata inside the dedicated gluten-free collection records.",
        "min_precision_at_1": 0.33,
        "min_mrr": 0.25,
    },
    {
        "name": "TC8: SAFETY - Vegan Asian Appetizer (No Soy/Sesame)",
        "query": "vegan asian appetizer with no soy or sesame",
        "expected_items": [],
        "expected_restaurant_ids": [],
        "allergens_to_avoid": ["soy", "sesame"],
        "description": "CRITICAL SAFETY TEST: Verifies negative allergen filter ($nin). If user specifies 'no soy or sesame', NO results should contain those allergens, even if semantically relevant.",
        "min_precision_at_1": 1.0,
        "min_mrr": 0.0,
    },
]


@pytest.fixture
async def setup_food_hybrid_search_eval():
    """Setup food hybrid search service for evaluation."""
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "vybe")

    client = AsyncMongoClient(mongodb_url)
    db = client[database_name]
    food_collection = db["food"]

    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embedding_adapter = OpenAIEmbeddingAdapter(client=openai_client, model="text-embedding-3-small")
    food_repo = MongoFoodRepository(food_collection)
    reranker_adapter = FoodReranker()

    hybrid_search = HybridSearchService(
        embedding_adapter=embedding_adapter,
        vector_repository=food_repo,
        reranker_adapter=reranker_adapter,
    )

    yield hybrid_search, food_repo

    await client.close()


def is_relevant(result, expected_items, allergens_to_avoid=None):
    """Check if result is relevant and safe.

    Args:
        result: FoodSearchResult object (from reranker)
        expected_items: List of expected food item names
        allergens_to_avoid: List of allergens to exclude (safety check)

    Returns:
        Tuple: (is_relevant: bool, safety_violation: bool, violation_reason: str)
    """
    allergens_to_avoid = allergens_to_avoid or []

    # Extract entity and its allergens
    entity = result.entity if hasattr(result, 'entity') else result

    # CRITICAL SAFETY CHECK: allergen filtering must be strict
    if allergens_to_avoid:
        result_allergens = [a.lower() for a in (entity.allergens or [])]
        for avoided in allergens_to_avoid:
            avoided_lower = avoided.lower()
            if avoided_lower in result_allergens:
                return False, True, f"Contains avoided allergen: {avoided}"

    # Check semantic relevance via fuzzy name matching
    result_lower = entity.name.lower()
    for expected in expected_items:
        expected_lower = expected.lower()
        # Exact match
        if result_lower == expected_lower:
            return True, False, None
        # Partial match (e.g., "Pad Thai" in "Midnight Pad Thai")
        if expected_lower in result_lower or result_lower in expected_lower:
            return True, False, None

    return False, False, None


def evaluate_query(results, expected_items, allergens_to_avoid=None):
    """Evaluate results against expected items and safety constraints.

    Args:
        results: List of FoodSearchResult objects
        expected_items: List of expected food item names
        allergens_to_avoid: List of allergens to exclude

    Returns:
        Dict with evaluation metrics
    """
    allergens_to_avoid = allergens_to_avoid or []
    safety_violations = []

    # Categorize results
    relevant_indices = []
    unsafe_indices = []

    for i, result in enumerate(results):
        is_rel, is_unsafe, reason = is_relevant(result, expected_items, allergens_to_avoid)

        # Extract entity for attribute access
        entity = result.entity if hasattr(result, 'entity') else result

        if is_unsafe:
            unsafe_indices.append(i)
            safety_violations.append({
                "index": i,
                "item": entity.name,
                "reason": reason,
                "allergens": entity.allergens
            })
        elif is_rel:
            relevant_indices.append(i)

    # Calculate metrics using only safe results
    # Synthetic IDs for metric calculation
    actual_ids = [f"result_{i}" for i in range(len(results))]
    expected_ids = [f"result_{i}" for i in relevant_indices]

    # Only count safe results in metrics
    safe_results_count = len(results) - len(unsafe_indices)

    p1 = calculate_precision_at_k(actual_ids, expected_ids, k=1) if relevant_indices else 0.0
    p3 = calculate_precision_at_k(actual_ids, expected_ids, k=3) if relevant_indices else 0.0
    p5 = calculate_precision_at_k(actual_ids, expected_ids, k=5) if relevant_indices else 0.0
    mrr = calculate_mrr(actual_ids, expected_ids)
    recall_5 = calculate_recall_at_k(actual_ids, expected_ids, k=5) if relevant_indices else 0.0
    ndcg_5 = calculate_ndcg(actual_ids, expected_ids, k=5) if relevant_indices else 0.0

    return {
        "p1": p1,
        "p3": p3,
        "p5": p5,
        "mrr": mrr,
        "recall_5": recall_5,
        "ndcg_5": ndcg_5,
        "relevant_count": len(relevant_indices),
        "safety_violations": safety_violations,
        "safe_results_count": safe_results_count,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("case", GOLDEN_FOOD_EVAL_CASES)
async def test_food_search_quality_evals(setup_food_hybrid_search_eval, case):
    """Automated Food Vector Search Evaluation with safety constraints.

    Uses Precision@K, MRR, Recall@K, NDCG@K to measure ranking quality.
    CRITICAL: Enforces strict allergen filtering.
    """
    hybrid_search, food_repo = setup_food_hybrid_search_eval

    print(f"\n{'='*100}")
    print(f"📊 {case['name']}")
    print(f"Query: '{case['query']}'")
    if case["allergens_to_avoid"]:
        print(f"⚠️  ALLERGEN SAFETY TEST - Avoiding: {case['allergens_to_avoid']}")
    print(f"{'='*100}")

    # Get all available restaurants
    all_food = await food_repo.filter_food(limit=1000)
    restaurant_ids = list(set([item.entity.restaurant_id for item in all_food]))

    # Run the vector search pipeline with hard allergen filtering
    results = await hybrid_search.search(
        query=case["query"],
        entity_ids=restaurant_ids,
        limit=10,
        num_candidates=100,
        allergens_to_exclude=case["allergens_to_avoid"],
    )

    # Evaluate with safety constraints
    metrics = evaluate_query(results, case["expected_items"], case["allergens_to_avoid"])

    # Log results
    expected_names = case["expected_items"]
    actual_names = [
        (r.entity.name if hasattr(r, 'entity') else r.name)
        for r in results[:5]
    ]
    relevant_names = [
        (r.entity.name if hasattr(r, 'entity') else r.name)
        for r in results
        if is_relevant(r, expected_names, case["allergens_to_avoid"])[0]
    ]

    print(f"Expected Items: {expected_names}")
    print(f"Actual Top 5: {actual_names}")
    print(f"Relevant Items Found: {relevant_names if relevant_names else '(none)'}")

    # Log safety violations if present
    if metrics["safety_violations"]:
        print(f"\n⚠️  SAFETY VIOLATIONS DETECTED:")
        for violation in metrics["safety_violations"]:
            print(f"   [{violation['index']}] {violation['item']}: {violation['reason']}")
            print(f"       Allergens: {violation['allergens']}")

    print(f"\nMetrics:")
    print(f"  Precision@1: {metrics['p1']:.2f} (min: {case['min_precision_at_1']:.2f})")
    print(f"  Precision@3: {metrics['p3']:.2f}")
    print(f"  Precision@5: {metrics['p5']:.2f}")
    print(f"  MRR:         {metrics['mrr']:.2f} (min: {case['min_mrr']:.2f})")
    print(f"  Recall@5:    {metrics['recall_5']:.2f}")
    print(f"  NDCG@5:      {metrics['ndcg_5']:.2f}")
    if metrics["safety_violations"]:
        print(f"  Safety Violations: {len(metrics['safety_violations'])} ❌")

    # Quality assertions
    assert metrics['p1'] >= case['min_precision_at_1'], (
        f"❌ Failed Precision@1 for '{case['query']}'. "
        f"Expected {expected_names}, got {actual_names}"
    )
    assert metrics['mrr'] >= case['min_mrr'], (
        f"❌ Failed MRR for '{case['query']}'. "
        f"First relevant too far: {actual_names}"
    )

    # CRITICAL: Safety assertion (no allergens allowed)
    if case["allergens_to_avoid"]:
        assert len(metrics["safety_violations"]) == 0, (
            f"❌ SAFETY VIOLATION: Results contain avoided allergens {case['allergens_to_avoid']}: "
            f"{[v['item'] for v in metrics['safety_violations']]}"
        )

    print(f"✅ PASSED\n")
