from fastapi import Request
from google.oauth2.credentials import Credentials

from app.exceptions import CalendarNotConnectedError
from app.integrations import google_oauth

SESSION_COOKIE = "synq_session"


def get_session_id(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def require_calendar_credentials(request: Request) -> Credentials:
    """FastAPI dependency: resolves the caller's Google credentials from their
    session cookie, or raises CalendarNotConnectedError (401) if not connected.
    """
    session_id = get_session_id(request)
    credentials = google_oauth.get_credentials(session_id)
    if credentials is None:
        raise CalendarNotConnectedError(
            "Google Calendar is not connected. Please connect it first."
        )
    return credentials
