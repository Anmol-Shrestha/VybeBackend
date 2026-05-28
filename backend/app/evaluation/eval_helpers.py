"""Shared evaluation metrics for search quality assessment."""


def calculate_precision_at_k(actual_ids, expected_ids, k=5):
    """Calculate Precision@K: fraction of top-k results that are relevant.

    Args:
        actual_ids: List of returned result IDs
        expected_ids: List of relevant/expected IDs
        k: Cutoff position

    Returns:
        Precision@K (0.0 to 1.0)
    """
    if not actual_ids or not expected_ids:
        return 0.0

    top_k = actual_ids[:k]
    relevant_count = sum(1 for id in top_k if id in expected_ids)
    return relevant_count / min(k, len(top_k))


def calculate_recall_at_k(actual_ids, expected_ids, k=5):
    """Calculate Recall@K: fraction of expected IDs found in top-k.

    Args:
        actual_ids: List of returned result IDs
        expected_ids: List of relevant/expected IDs
        k: Cutoff position

    Returns:
        Recall@K (0.0 to 1.0)
    """
    if not expected_ids:
        return 0.0

    top_k = actual_ids[:k]
    relevant_count = sum(1 for id in expected_ids if id in top_k)
    return relevant_count / len(expected_ids)


def calculate_mrr(actual_ids, expected_ids):
    """Calculate Mean Reciprocal Rank: rank of first relevant result.

    Args:
        actual_ids: List of returned result IDs
        expected_ids: List of relevant/expected IDs

    Returns:
        MRR (0.0 to 1.0). Higher is better.
        1.0 = first result is relevant
        0.5 = first relevant result at position 2
        0.0 = no relevant results found
    """
    for i, id in enumerate(actual_ids):
        if id in expected_ids:
            return 1.0 / (i + 1)
    return 0.0


def calculate_ndcg(actual_ids, expected_ids, k=5):
    """Calculate Normalized Discounted Cumulative Gain.

    NDCG measures ranking quality accounting for position decay.
    Relevant results ranked earlier contribute more to the score.

    Args:
        actual_ids: List of returned result IDs
        expected_ids: List of relevant/expected IDs
        k: Cutoff position

    Returns:
        NDCG@K (0.0 to 1.0)
    """
    if not actual_ids or not expected_ids:
        return 0.0

    # Calculate DCG (Discounted Cumulative Gain)
    dcg = 0.0
    for i, id in enumerate(actual_ids[:k]):
        relevance = 1.0 if id in expected_ids else 0.0
        # Discount factor: 1 / log2(position + 1)
        discount = 1.0 / (2 ** (i / 1.0))
        dcg += relevance * discount

    # Calculate IDCG (Ideal DCG) - perfect ranking
    idcg = 0.0
    num_relevant = len(expected_ids)
    for i in range(min(k, num_relevant)):
        discount = 1.0 / (2 ** (i / 1.0))
        idcg += discount

    if idcg == 0:
        return 0.0

    return dcg / idcg


