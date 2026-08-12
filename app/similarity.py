"""Rank search results against the submitted idea using TF-IDF cosine similarity.

No LLM calls are used — this is plain keyword/term-frequency based similarity,
computed locally and deterministically.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .sources.base import SearchResult


def rank_results(idea_text: str, results: list[SearchResult]) -> list[SearchResult]:
    """Assign a similarity score (0-1) to each result and return them sorted
    from most to least similar to `idea_text`. Results with a fetch error are
    left with a score of 0 and sorted to the end.
    """
    scorable = [r for r in results if not r.error]
    errored = [r for r in results if r.error]

    if not scorable:
        return errored

    documents = [idea_text] + [f"{r.title} {r.snippet}".strip() for r in scorable]

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        matrix = vectorizer.fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except ValueError:
        # Happens if every document is empty after stop-word removal.
        similarities = [0.0] * len(scorable)

    for result, score in zip(scorable, similarities):
        result.score = round(float(score), 4)

    scorable.sort(key=lambda r: r.score, reverse=True)
    return scorable + errored
