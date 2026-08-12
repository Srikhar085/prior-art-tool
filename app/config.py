"""Configuration loaded from environment variables (see .env.example)."""
import os

from dotenv import load_dotenv

load_dotenv()

PATENTSVIEW_API_KEY = os.getenv("PATENTSVIEW_API_KEY", "").strip()
EPO_OPS_KEY = os.getenv("EPO_OPS_KEY", "").strip()
EPO_OPS_SECRET = os.getenv("EPO_OPS_SECRET", "").strip()
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()

# Company email domain each individual login must belong to.
REQUIRED_EMAIL_DOMAIN = os.getenv("REQUIRED_EMAIL_DOMAIN", "bmwtechworks.in").strip().lower()

# Single shared credential pair — kept only as a quick local-dev fallback.
# Prefer APP_USERS below for anything more than one person on your own machine.
APP_USERNAME = os.getenv("APP_USERNAME", "").strip()
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()

# Per-user logins: "email1:bcrypt_hash1,email2:bcrypt_hash2,...". Each
# colleague generates their own hash with scripts/add_user.py (their real
# password is never typed into or stored in this file/repo) and only their
# own "email:hash" entry gets appended here — nobody else's password is ever
# visible to them.
APP_USERS = {}
for _entry in os.getenv("APP_USERS", "").split(","):
    _entry = _entry.strip()
    if not _entry or ":" not in _entry:
        continue
    _email, _hash = _entry.split(":", 1)
    APP_USERS[_email.strip().lower()] = _hash.strip()

# How many results to request from each source.
RESULTS_PER_SOURCE = 15
