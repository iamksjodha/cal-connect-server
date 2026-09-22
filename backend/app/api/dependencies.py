from fastapi import Request
from google.oauth2.credentials import Credentials

from app.integrations import google_oauth

SESSION_COOKIE = "synq_session"


def get_session_id(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def get_calendar_credentials(request: Request) -> Credentials | None:
    """FastAPI dependency: resolves the caller's Google credentials from their
    session cookie, or None if calendar isn't connected. Chat should still work
    without calendar access — only the calendar tools need credentials.
    """
    session_id = get_session_id(request)
    return google_oauth.get_credentials(session_id)
