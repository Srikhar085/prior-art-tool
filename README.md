# Prior Art Tool

Search patent databases and academic literature for prior art related to a
patent idea, and rank the combined results by TF-IDF text similarity to the
idea description. No LLM is used — matches are surfaced for you to review.

## Sources

| Source | Covers | Key required |
|---|---|---|
| [PatentsView](https://patentsview.org/apis/keyrequest) | US patents (full text) | `PATENTSVIEW_API_KEY` |
| [EPO Open Patent Services](https://developers.epo.org) | International patents | `EPO_OPS_KEY` + `EPO_OPS_SECRET` |
| [Semantic Scholar](https://www.semanticscholar.org/product/api) | Academic papers / non-patent literature | none (optional `SEMANTIC_SCHOLAR_API_KEY` for higher limits) |

Sources without a configured key are skipped automatically — the app still
runs with just Semantic Scholar out of the box.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in any API keys you have
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000

## API

`GET /api/search?title=...&description=...` returns JSON with ranked results,
for scripting or integration with other internal tools.

## Docker

```bash
docker build -t prior-art-tool .
docker run -p 8000:8000 --env-file .env prior-art-tool
```

## Deploying to Render

1. Push this repo to GitHub (or GitLab/Bitbucket).
2. In the Render dashboard: **New > Blueprint**, point it at the repo. Render
   will read `render.yaml` and create the web service automatically.
3. Set the `PATENTSVIEW_API_KEY`, `EPO_OPS_KEY`, `EPO_OPS_SECRET` env vars in
   the Render dashboard (they're marked `sync: false` so Render prompts for
   them instead of storing secrets in the repo).
4. Deploy. Render builds with `pip install -r requirements.txt` and starts
   with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Alternatively, deploy the `Dockerfile` directly on Render, Railway, or Fly.io
as a container service — no code changes needed.
