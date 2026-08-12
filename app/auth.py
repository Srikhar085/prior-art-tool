"""HTTP Basic Auth gate for the whole app, supporting per-user logins.

The tool is meant to hold confidential, unfiled invention ideas, so once it's
reachable on the public internet (e.g. a Render URL) it must not be usable by
anyone who merely guesses/finds the link. Two credential sources are checked:

- APP_USERS: one bcrypt-hashed entry per colleague (email:hash), the
  recommended setup — see scripts/add_user.py. Each person's password is
  never visible to anyone else, including whoever manages the deployment.
- APP_USERNAME / APP_PASSWORD: a single shared plaintext pair, kept only as
  a quick fallback for solo local development.

If neither is configured, the app runs open and logs a warning so this
doesn't go unnoticed in production.
"""
import base64
import logging
import secrets

import bcrypt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from . import config

logger = logging.getLogger("prior_art_tool.auth")

UNAUTHENTICATED_PATHS = {"/health"}


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _auth_configured():
            return await call_next(request)

        if request.url.path in UNAUTHENTICATED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if self._is_authorized(auth_header):
            return await call_next(request)

        return Response(
            status_code=401,
            content="Authentication required.",
            headers={"WWW-Authenticate": 'Basic realm="Prior Art Tool"'},
        )

    @staticmethod
    def _is_authorized(auth_header: str) -> bool:
        scheme, _, encoded = auth_header.partition(" ")
        if scheme.lower() != "basic" or not encoded:
            return False
        try:
            username, _, password = base64.b64decode(encoded).decode().partition(":")
        except Exception:  # noqa: BLE001 - malformed header -> unauthorized
            return False

        stored_hash = config.APP_USERS.get(username.strip().lower())
        if stored_hash:
            try:
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            except ValueError:  # malformed stored hash -> unauthorized
                return False

        if config.APP_USERNAME and config.APP_PASSWORD:
            return secrets.compare_digest(username, config.APP_USERNAME) and (
                secrets.compare_digest(password, config.APP_PASSWORD)
            )

        return False


def _auth_configured() -> bool:
    return bool(config.APP_USERS) or bool(config.APP_USERNAME and config.APP_PASSWORD)


def warn_if_unprotected() -> None:
    if not _auth_configured():
        logger.warning(
            "No login is configured (APP_USERS / APP_USERNAME+APP_PASSWORD) — "
            "the app is running WITHOUT authentication. Anyone with the URL "
            "can submit and view searches. Set one of these before deploying "
            "anywhere reachable outside your own machine."
        )
