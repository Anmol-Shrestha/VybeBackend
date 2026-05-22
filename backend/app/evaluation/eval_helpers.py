"""Evaluation metrics for restaurant search quality."""


def calculate_precision_at_k(actual_ids: list[str], expected_ids: list[str], k: int = 1) -> float:
    """
    Calculate Precision@K: What fraction of top-K results are relevant?

    Args:
        actual_ids: IDs returned by search engine (ordered by rank)
        expected_ids: Ground truth relevant IDs
        k: Evaluate only top-K results

    Returns:
        Float between 0 and 1
        - 1.0: All top-K are relevant
        - 0.5: Half of top-K are relevant
        - 0.0: None of top-K are relevant
    """
    if not actual_ids or not expected_ids:
        return 0.0

    top_k = actual_ids[:k]
    relevant_count = sum(1 for id in top_k if id in expected_ids)
    return relevant_count / k


def calculate_mrr(actual_ids: list[str], expected_ids: list[str]) -> float:
    """
    Calculate Mean Reciprocal Rank: Position of first relevant result.

    Args:
        actual_ids: IDs returned by search engine (ordered by rank)
        expected_ids: Ground truth relevant IDs

    Returns:
        Float between 0 and 1
        - 1.0: First result is relevant (rank 1)
        - 0.5: Second result is relevant (rank 2)
        - 0.33: Third result is relevant (rank 3)
        - 0.0: No relevant result found
    """
    for rank, id in enumerate(actual_ids, 1):
        if id in expected_ids:
            return 1.0 / rank
    return 0.0


def calculate_recall_at_k(actual_ids: list[str], expected_ids: list[str], k: int = 10) -> float:
    """
    Calculate Recall@K: What fraction of relevant items are in top-K?

    Args:
        actual_ids: IDs returned by search engine (ordered by rank)
        expected_ids: Ground truth relevant IDs
        k: Evaluate only top-K results

    Returns:
        Float between 0 and 1
    """
    if not expected_ids:
        return 0.0

    top_k = actual_ids[:k]
    relevant_found = sum(1 for id in top_k if id in expected_ids)
    return relevant_found / len(expected_ids)


def calculate_ndcg(actual_ids: list[str], expected_ids: list[str], k: int = 10) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain: Quality of ranking.

    Penalizes relevant items that appear later in the ranking.
    - DCG rewards relevant items, discounts by position: sum(rel_i / log2(i+1))
    - NDCG = DCG / IDCG (normalized by ideal ranking)

    Args:
        actual_ids: IDs returned by search engine (ordered by rank)
        expected_ids: Ground truth relevant IDs
        k: Evaluate only top-K results

    Returns:
        Float between 0 and 1 (1.0 = perfect ranking)
    """
    import math

    if not expected_ids:
        return 0.0

    # Calculate DCG
    dcg = 0.0
    for rank, id in enumerate(actual_ids[:k], 1):
        relevance = 1.0 if id in expected_ids else 0.0
        dcg += relevance / math.log2(rank + 1)

    # Calculate IDCG (ideal: all relevant items at top)
    idcg = 0.0
    for rank in range(1, min(len(expected_ids), k) + 1):
        idcg += 1.0 / math.log2(rank + 1)

    if idcg == 0:
        return 0.0

    return dcg / idcg