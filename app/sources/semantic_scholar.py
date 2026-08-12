"""Semantic Scholar client — academic papers / non-patent literature.

Docs: https://api.semanticscholar.org/api-docs/graph
No API key is required for light usage; supplying one raises rate limits.
"""
import httpx

from .. import config
from .base import SearchResult

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


async def search(query: str, limit: int = None) -> list[SearchResult]:
    limit = limit or config.RESULTS_PER_SOURCE
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,url,year,venue",
    }
    headers = {}
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(SEARCH_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 - soft error, don't crash the whole search
        return [SearchResult(
            source="Semantic Scholar", kind="literature", external_id="", title="",
            snippet="", url="", error=f"Semantic Scholar request failed: {exc}",
        )]

    results = []
    for paper in data.get("data", []) or []:
        year = paper.get("year")
        results.append(SearchResult(
            source="Semantic Scholar",
            kind="literature",
            external_id=paper.get("paperId", ""),
            title=paper.get("title", "") or "",
            snippet=paper.get("abstract", "") or "",
            url=paper.get("url", "") or "",
            date=str(year) if year else "",
        ))
    return results
