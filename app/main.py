"""Prior Art Tool — FastAPI app.

Searches configured patent and academic-literature sources for a submitted
idea, ranks the combined results by TF-IDF similarity to the idea text, and
renders them (plus exposes a JSON API for programmatic use).
"""
import asyncio

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import config
from .auth import BasicAuthMiddleware, warn_if_unprotected
from .similarity import rank_results
from .sources import epo_ops, patentsview, semantic_scholar

app = FastAPI(title="Prior Art Tool")
app.add_middleware(BasicAuthMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
warn_if_unprotected()


class SearchRequest(BaseModel):
    title: str
    description: str = ""


SOURCE_STATUS = {
    "PatentsView (US patents)": bool(config.PATENTSVIEW_API_KEY),
    "EPO OPS (international patents)": bool(config.EPO_OPS_KEY and config.EPO_OPS_SECRET),
    "Semantic Scholar (academic literature)": True,
}


async def run_search(query: str) -> list:
    tasks = [
        patentsview.search(query),
        epo_ops.search(query),
        semantic_scholar.search(query),
    ]
    results_per_source = await asyncio.gather(*tasks)
    combined = [r for sub in results_per_source for r in sub]
    return rank_results(query, combined)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "source_status": SOURCE_STATUS}
    )


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, title: str = Form(...), description: str = Form("")):
    query = f"{title} {description}".strip()
    ranked = await run_search(query)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "title": title,
            "description": description,
            "results": ranked,
            "source_status": SOURCE_STATUS,
        },
    )


@app.post("/api/search")
async def api_search(payload: SearchRequest):
    """JSON API: POST /api/search with a {"title": ..., "description": ...} body.

    Deliberately a POST with a JSON body (not GET with query params) so idea
    text never ends up in a URL, browser history, or access log line.
    """
    query = f"{payload.title} {payload.description}".strip()
    ranked = await run_search(query)
    return {"query": query, "count": len(ranked), "results": [vars(r) for r in ranked]}


@app.get("/health")
async def health():
    return {"status": "ok"}
