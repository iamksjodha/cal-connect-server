import json
import secrets

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import (
    GOOGLE_OAUTH_CLIENT_FILE,
    GOOGLE_OAUTH_CLIENT_JSON,
    GOOGLE_OAUTH_REDIRECT_URI,
)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# In-memory session store: session_id -> google.oauth2.credentials.Credentials
# A prototype-level substitute for a real session/database layer.
_sessions: dict[str, Credentials] = {}

# In-memory store of the in-progress OAuth Flow (which holds the PKCE code_verifier),
# keyed by session_id, so the same Flow object is reused between /auth/login and
# /auth/callback instead of rebuilding it (a fresh Flow has no code_verifier).
# Stored as (state, flow) so the callback can verify the state without reaching
# into the Flow's private attributes.
_pending_flows: dict[str, tuple[str, Flow]] = {}


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def store_pending_flow(session_id: str, state: str, flow: Flow) -> None:
    _pending_flows[session_id] = (state, flow)


def pop_pending_flow(session_id: str) -> tuple[str, Flow] | None:
    return _pending_flows.pop(session_id, None)


def build_flow() -> Flow:
    if GOOGLE_OAUTH_CLIENT_JSON:
        # Deployed environments (e.g. Render): the client secret is provided as a
        # full JSON blob in an env var, since there's no local file to read.
        client_config = json.loads(GOOGLE_OAUTH_CLIENT_JSON)
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
        )

    return Flow.from_client_secrets_file(
        GOOGLE_OAUTH_CLIENT_FILE,
        scopes=SCOPES,
        redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
    )


def store_credentials(session_id: str, credentials: Credentials) -> None:
    _sessions[session_id] = credentials


def get_credentials(session_id: str | None) -> Credentials | None:
    if not session_id:
        return None
    return _sessions.get(session_id)


def is_connected(session_id: str | None) -> bool:
    return get_credentials(session_id) is not None


def disconnect(session_id: str | None) -> None:
    if session_id:
        _sessions.pop(session_id, None)
