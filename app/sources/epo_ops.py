"""EPO Open Patent Services (OPS) client — international patent search.

Docs: https://developers.epo.org/OPS-v3-2
Requires a free consumer key/secret (EPO_OPS_KEY / EPO_OPS_SECRET) exchanged
for a short-lived OAuth2 access token.
"""
import base64

import httpx

from .. import config
from .base import SearchResult

TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"


async def _get_access_token(client: httpx.AsyncClient) -> str:
    credentials = base64.b64encode(
        f"{config.EPO_OPS_KEY}:{config.EPO_OPS_SECRET}".encode()
    ).decode()
    resp = await client.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _text(node) -> str:
    """Extract text from a parsed-JSON EPO node that may be a dict, list, or str."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return node.get("$", "")
    if isinstance(node, list):
        return " ".join(_text(item) for item in node)
    return ""


async def search(query: str, limit: int = None) -> list[SearchResult]:
    if not config.EPO_OPS_KEY or not config.EPO_OPS_SECRET:
        return []

    limit = limit or config.RESULTS_PER_SOURCE
    cql = f'ti="{query}" or ab="{query}"'

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token = await _get_access_token(client)
            resp = await client.get(
                SEARCH_URL,
                params={"q": cql, "Range": f"1-{limit}"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 - soft error, don't crash the whole search
        return [SearchResult(
            source="EPO", kind="patent", external_id="", title="",
            snippet="", url="", error=f"EPO OPS request failed: {exc}",
        )]

    results = []
    try:
        search_result = (
            data.get("ops:world-patent-data", {})
            .get("ops:biblio-search", {})
            .get("ops:search-result", {})
        )
        documents = search_result.get("exchange-documents", [])
        if isinstance(documents, dict):
            documents = [documents]

        for doc_wrapper in documents:
            doc = doc_wrapper.get("exchange-document", {})
            doc_id = doc.get("@doc-number", "") or ""
            country = doc.get("@country", "") or ""
            kind = doc.get("@kind", "") or ""
            biblio = doc.get("bibliographic-data", {})

            title = ""
            for t in biblio.get("invention-title", []) if isinstance(
                biblio.get("invention-title"), list
            ) else [biblio.get("invention-title")]:
                if t:
                    title = _text(t)
                    break

            abstract = ""
            abstract_node = doc.get("abstract")
            if isinstance(abstract_node, list):
                abstract_node = abstract_node[0] if abstract_node else None
            if abstract_node:
                abstract = _text(abstract_node.get("p"))

            pub_number = f"{country}{doc_id}{kind}"
            results.append(SearchResult(
                source="EPO",
                kind="patent",
                external_id=pub_number,
                title=title,
                snippet=abstract,
                url=f"https://worldwide.espacenet.com/patent/search/family/publication/{pub_number}"
                    if pub_number else "",
            ))
    except Exception as exc:  # noqa: BLE001 - EPO's response shape varies; degrade gracefully
        results.append(SearchResult(
            source="EPO", kind="patent", external_id="", title="",
            snippet="", url="", error=f"EPO OPS response could not be parsed: {exc}",
        ))

    return results
