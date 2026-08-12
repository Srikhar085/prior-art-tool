# Prior Art Tool

Search patent databases and academic literature for prior art related to a
patent idea, and rank the combined results by TF-IDF text similarity to the
idea description. No LLM is used — matches are surfaced for you to review.

Built to keep unfiled ideas confidential: the app stores nothing (no
database — each search happens in memory and is discarded after the
response), and the whole app is gated behind a login before it's deployed
anywhere public. See [Privacy & security](#privacy--security) below.

## Running the tool

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets (API keys + login credentials)
cp .env.example .env
# then edit .env and fill in the values — see "Sources" and
# "Privacy & security" below for what each one does

# 4. Start the app
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser. Stop the server with `Ctrl+C`.

Next time, you only need: `source .venv/bin/activate` then
`uvicorn app.main:app --reload`.

## Sources

| Source | Covers | Key required |
|---|---|---|
| [PatentsView](https://patentsview.org/apis/keyrequest) | US patents (full text) | `PATENTSVIEW_API_KEY` |
| [EPO Open Patent Services](https://developers.epo.org) | International patents | `EPO_OPS_KEY` + `EPO_OPS_SECRET` |
| [Semantic Scholar](https://www.semanticscholar.org/product/api) | Academic papers / non-patent literature | none (optional `SEMANTIC_SCHOLAR_API_KEY` for higher limits) |

Sources without a configured key are skipped automatically — the app still
runs with just Semantic Scholar out of the box.

## Privacy & security

This tool exists to protect your organization's ideas, so keep these in mind:

- **No storage.** There is no database. Submitted ideas and search results
  only ever live in server memory for the duration of one request, then
  they're gone. Nothing is written to disk or logged by the app itself.
- **Login required once deployed.** Set `APP_USERS` (recommended — one
  entry per colleague) or `APP_USERNAME`/`APP_PASSWORD` (a single shared
  fallback pair) before deploying anywhere reachable outside your own
  machine — e.g. Render. This puts the whole app behind HTTP Basic Auth so
  only people with credentials can use it. If none of these are set, the
  app logs a warning and runs **without** auth — fine for local development
  only. See [Adding a colleague](#adding-a-colleague) below.
- **The idea text is sent to the external APIs you configure.** To find
  prior art, the title/description you submit is used as the search query
  sent to PatentsView, EPO OPS, and/or Semantic Scholar. Those are the
  official (US, European, and academic) search providers, and this is
  unavoidable for any tool that checks external prior art. To minimize
  exposure: search with descriptive/functional keywords rather than pasting
  verbatim draft claim language, and only enable the sources you actually
  need (unused sources are skipped automatically when their key is blank).
- **Always use HTTPS in production** (Render provides this by default) so
  credentials and idea text aren't sent in plaintext over the network.
- **Keep `.env` out of git.** It's already listed in `.gitignore` — never
  commit real API keys or the app password.

## API

`POST /api/search` with a JSON body `{"title": "...", "description": "..."}`
returns ranked results — for scripting or integration with other internal
tools. Using POST with a JSON body (instead of GET with query params) keeps
idea text out of URLs and access logs.

```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -u "you@bmwtechworks.in:yourpassword" \
  -d '{"title": "Self-cleaning solar panel coating", "description": "..."}'
```

(Omit `-u "..."` if you haven't set up any login for local development.)

## Docker

```bash
docker build -t prior-art-tool .
docker run -p 8000:8000 --env-file .env prior-art-tool
```

## Git repository

The code lives in a **private** GitHub repository:
https://github.com/Srikhar085/prior-art-tool. Since it's private, only
accounts explicitly added as collaborators (GitHub repo Settings →
**Collaborators**) can see the source — this has no bearing on who can log
into the running app itself, which is controlled by `APP_USERS` (below).

## Adding a colleague

The app is currently only running on this machine — it isn't reachable by
anyone else until it's deployed (see below). Once it is deployed, here's how
to give a colleague their own login (nobody, including you, ever sees their
password):

1. **They generate their own credential locally:**
   ```bash
   git clone https://github.com/Srikhar085/prior-art-tool.git
   cd prior-art-tool
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python scripts/add_user.py
   ```
   They enter their `@bmwtechworks.in` email and choose their own password.
   The script prints a single line: `email:bcrypt_hash` — it never reveals
   or transmits their plaintext password.
2. **They send you only that printed line** (e.g. over Slack/email) —
   sharing a bcrypt hash is safe, it can't be reversed back into the
   password.
3. **You append it** to the `APP_USERS` environment variable on the
   deployment (Render dashboard → your service → **Environment**),
   comma-separated after any existing entries, e.g.:
   ```
   alice@bmwtechworks.in:$2b$12$abc...,bob@bmwtechworks.in:$2b$12$xyz...
   ```
4. **Redeploy** (Render redeploys automatically when env vars change). Your
   colleague can now log in at the app's URL with their own email/password.

To remove someone's access, delete their entry from `APP_USERS` and redeploy.

## Deploying to Render

1. In the Render dashboard: **New > Blueprint**, point it at
   https://github.com/Srikhar085/prior-art-tool (grant Render access to the
   private repo when prompted). Render reads `render.yaml` and creates the
   web service automatically.
2. In the Render dashboard, set these environment variables:
   - `APP_USERS` — **required**, one `email:bcrypt_hash` entry per person
     (see [Adding a colleague](#adding-a-colleague)).
   - `PATENTSVIEW_API_KEY`, `EPO_OPS_KEY`, `EPO_OPS_SECRET` — optional,
     enables those sources.
   (They're marked `sync: false` in `render.yaml` so Render prompts you for
   them instead of storing secrets in the repo.)
3. Deploy. Render builds with `pip install -r requirements.txt` and starts
   with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Alternatively, deploy the `Dockerfile` directly on Render, Railway, or Fly.io
as a container service — no code changes needed.
