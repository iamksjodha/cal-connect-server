import json
import os
import secrets
import threading

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import (
    GOOGLE_OAUTH_CLIENT_FILE,
    GOOGLE_OAUTH_CLIENT_JSON,
    GOOGLE_OAUTH_REDIRECT_URI,
)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Persist sessions to disk instead of keeping them only in a Python dict.
# On platforms like Render's free tier, the process can be restarted (spun down
# after inactivity, then cold-started again) in the middle of a user completing
# the Google login screen — an in-memory dict would lose the pending OAuth state
# and the connection would silently fail. A small JSON file survives that restart
# as long as the disk isn't wiped, which is enough for this prototype's traffic.
_STORE_FILE = os.getenv("SESSION_STORE_FILE", "sessions.json")
_lock = threading.Lock()


def _load_store() -> dict:
    if not os.path.exists(_STORE_FILE):
        return {"sessions": {}, "pending_flows": {}}
    try:
        with open(_STORE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"sessions": {}, "pending_flows": {}}


def _save_store(store: dict) -> None:
    with open(_STORE_FILE, "w") as f:
        json.dump(store, f)


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def store_pending_flow(session_id: str, state: str, flow: Flow) -> None:
    # A Flow object can't be JSON-serialized directly, so only the pieces needed
    # to reconstruct an equivalent Flow later are saved (see _rebuild_flow).
    with _lock:
        store = _load_store()
        store["pending_flows"][session_id] = {
            "state": state,
            "code_verifier": flow.code_verifier,
            "client_config": flow.client_config,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        }
        _save_store(store)


def pop_pending_flow(session_id: str) -> tuple[str, Flow] | None:
    with _lock:
        store = _load_store()
        entry = store["pending_flows"].pop(session_id, None)
        _save_store(store)

    if entry is None:
        return None

    flow = Flow.from_client_config(
        entry["client_config"],
        scopes=SCOPES,
        redirect_uri=entry["redirect_uri"],
    )
    flow.code_verifier = entry["code_verifier"]
    return entry["state"], flow


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
    with _lock:
        store = _load_store()
        store["sessions"][session_id] = json.loads(credentials.to_json())
        _save_store(store)


def get_credentials(session_id: str | None) -> Credentials | None:
    if not session_id:
        return None
    with _lock:
        store = _load_store()
    raw = store["sessions"].get(session_id)
    if raw is None:
        return None
    return Credentials.from_authorized_user_info(raw)


def is_connected(session_id: str | None) -> bool:
    return get_credentials(session_id) is not None


def disconnect(session_id: str | None) -> None:
    if not session_id:
        return
    with _lock:
        store = _load_store()
        store["sessions"].pop(session_id, None)
        _save_store(store)
