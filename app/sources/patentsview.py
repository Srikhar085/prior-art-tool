"""PatentsView API client — US patents, full text search.

Docs: https://search.patentsview.org/docs/
Requires a free API key (PATENTSVIEW_API_KEY) sent as the 'X-Api-Key' header.
"""
import httpx

from .. import config
from .base import SearchResult

SEARCH_URL = "https://search.patentsview.org/api/v1/patent/"


async def search(query: str, limit: int = None) -> list[SearchResult]:
    if not config.PATENTSVIEW_API_KEY:
        return []

    limit = limit or config.RESULTS_PER_SOURCE
    params = {
        "q": (
            '{"_or":[{"_text_any":{"patent_title":"%s"}},'
            '{"_text_any":{"patent_abstract":"%s"}}]}' % (query, query)
        ),
        "f": '["patent_id","patent_title","patent_abstract","patent_date"]',
        "o": '{"size":%d}' % limit,
    }
    headers = {"X-Api-Key": config.PATENTSVIEW_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(SEARCH_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 - surface as a soft error, don't crash the search
        return [SearchResult(
            source="PatentsView", kind="patent", external_id="", title="",
            snippet="", url="", error=f"PatentsView request failed: {exc}",
        )]

    results = []
    for patent in data.get("patents", []) or []:
        patent_id = patent.get("patent_id", "")
        results.append(SearchResult(
            source="PatentsView",
            kind="patent",
            external_id=patent_id,
            title=patent.get("patent_title", "") or "",
            snippet=patent.get("patent_abstract", "") or "",
            url=f"https://patents.google.com/patent/US{patent_id}" if patent_id else "",
            date=patent.get("patent_date", "") or "",
        ))
    return results
