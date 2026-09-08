"""Semantic Scholar client — academic papers / non-patent literature.

Docs: https://api.semanticscholar.org/api-docs/graph
No API key is required for light usage; supplying one raises rate limits.
"""
import asyncio

import httpx

from .. import config
from .base import SearchResult

SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

# The unauthenticated tier shares a single, easily-exhausted rate-limit pool
# across everyone calling the API without a key, so 429s are common and
# transient — retry a couple of times with backoff before giving up.
MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 2


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
            data = await _get_with_retry(client, params, headers)
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


async def _get_with_retry(client: httpx.AsyncClient, params: dict, headers: dict) -> dict:
    """GET the search endpoint, retrying on 429 with backoff (honoring
    Retry-After when the API sends one) before giving up."""
    for attempt in range(MAX_RETRIES + 1):
        resp = await client.get(SEARCH_URL, params=params, headers=headers)
        if resp.status_code != 429 or attempt == MAX_RETRIES:
            resp.raise_for_status()
            return resp.json()

        retry_after = resp.headers.get("Retry-After")
        try:
            wait_seconds = float(retry_after) if retry_after else DEFAULT_BACKOFF_SECONDS * (attempt + 1)
        except ValueError:
            wait_seconds = DEFAULT_BACKOFF_SECONDS * (attempt + 1)
        await asyncio.sleep(wait_seconds)
