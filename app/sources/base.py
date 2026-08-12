"""Shared data model for search results returned by every source client."""
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    source: str          # e.g. "PatentsView", "EPO", "Semantic Scholar"
    kind: str            # "patent" or "literature"
    external_id: str
    title: str
    snippet: str         # abstract or excerpt
    url: str
    date: str = ""       # publication/filing date if available
    score: float = 0.0   # similarity score filled in after ranking
    error: str = field(default="", repr=False)  # non-fatal fetch error, if any
