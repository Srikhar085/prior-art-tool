"""Rank search results against the submitted idea using a hybrid of TF-IDF
cosine similarity and latent semantic analysis (LSA, via truncated SVD).

LSA projects the TF-IDF vectors into a lower-dimensional "topic" space,
which helps catch results that are conceptually similar even when they
don't share many exact keywords with the idea text. Both techniques are
purely local, deterministic statistics over the result text — no LLM calls,
no external API calls, no idea text leaves this process.
"""
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .sources.base import SearchResult

# Weight given to the LSA (semantic) similarity vs. raw TF-IDF (keyword)
# similarity in the final blended score.
LSA_WEIGHT = 0.5


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
        tfidf_matrix = vectorizer.fit_transform(documents)
        tfidf_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    except ValueError:
        # Happens if every document is empty after stop-word removal.
        tfidf_matrix = None
        tfidf_similarities = [0.0] * len(scorable)

    similarities = tfidf_similarities
    if tfidf_matrix is not None:
        lsa_similarities = _lsa_similarities(tfidf_matrix)
        if lsa_similarities is not None:
            similarities = [
                (1 - LSA_WEIGHT) * tfidf_score + LSA_WEIGHT * lsa_score
                for tfidf_score, lsa_score in zip(tfidf_similarities, lsa_similarities)
            ]

    for result, score in zip(scorable, similarities):
        result.score = round(float(score), 4)

    scorable.sort(key=lambda r: r.score, reverse=True)
    return scorable + errored


def _lsa_similarities(tfidf_matrix):
    """Project the TF-IDF matrix into a lower-dimensional semantic space with
    truncated SVD and return cosine similarity between the idea (row 0) and
    every result, or None if the corpus is too small for SVD to be meaningful."""
    n_samples, n_features = tfidf_matrix.shape
    n_components = min(100, n_features - 1, n_samples - 1)
    if n_components < 2:
        return None

    try:
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        lsa_matrix = svd.fit_transform(tfidf_matrix)
    except ValueError:
        return None

    return cosine_similarity(lsa_matrix[0:1], lsa_matrix[1:]).flatten()
