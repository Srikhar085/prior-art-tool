"""Lightweight, local synonym-based query expansion using WordNet.

Broadens patent-database queries beyond an idea's exact wording, so a
relevant patent isn't missed just because it uses different vocabulary for
the same concept. Purely local: WordNet's corpus is downloaded once at build
time (see Dockerfile / render.yaml), so no network calls happen per-request
and no idea text is sent anywhere new.
"""
import re

from nltk.corpus import wordnet as wn

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "with", "to", "in", "on",
    "is", "are", "that", "this", "using", "used", "via", "by", "from",
}

MAX_SYNONYMS_PER_WORD = 1
MAX_EXPANSION_WORDS = 8


def expand_query(query: str) -> str:
    """Return the query with a handful of WordNet synonyms appended for its
    significant words, for use as a broader/looser search query. Falls back
    to the original query unchanged if WordNet's data isn't available."""
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", query)]
    keywords = [w for w in words if w not in _STOPWORDS and len(w) > 2]

    seen = set(words)
    extra_terms = []
    for word in keywords:
        if len(extra_terms) >= MAX_EXPANSION_WORDS:
            break
        try:
            synsets = wn.synsets(word)
        except LookupError:
            # WordNet corpus not downloaded — expansion unavailable, no-op.
            return query

        added = 0
        for synset in synsets:
            for lemma in synset.lemma_names():
                candidate = lemma.replace("_", " ").lower()
                if candidate in seen or " " in candidate:
                    continue
                extra_terms.append(candidate)
                seen.add(candidate)
                added += 1
                break
            if added >= MAX_SYNONYMS_PER_WORD:
                break

    if not extra_terms:
        return query
    return f"{query} {' '.join(extra_terms)}"
