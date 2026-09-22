from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import SESSION_COOKIE, get_session_id
from app.core.config import FRONTEND_URL, IS_HTTPS_DEPLOYMENT
from app.integrations import google_oauth
from app.schemas.auth import AuthStatusResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(request: Request):
    session_id = get_session_id(request)
    return AuthStatusResponse(connected=google_oauth.is_connected(session_id))


@router.get("/login")
def auth_login(request: Request):
    """Start the Google OAuth flow so the user connects their own calendar."""
    flow = google_oauth.build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session_id = get_session_id(request) or google_oauth.new_session_id()
    response = RedirectResponse(authorization_url)
    # The frontend (Netlify) and backend (Render) are different origins in production,
    # so the session cookie must be sent cross-site: that requires SameSite=None, which
    # in turn requires Secure (HTTPS-only cookie). Locally both run on http://localhost,
    # where SameSite=Lax works fine and Secure would block the cookie entirely.
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="none" if IS_HTTPS_DEPLOYMENT else "lax",
        secure=IS_HTTPS_DEPLOYMENT,
    )
    # Stash the whole Flow (it holds the PKCE code_verifier) so the callback can reuse it.
    google_oauth.store_pending_flow(session_id, state, flow)
    return response


@router.get("/callback")
def auth_callback(request: Request):
    session_id = get_session_id(request)
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session cookie")

    pending = google_oauth.pop_pending_flow(session_id)
    returned_state = request.query_params.get("state")
    if not pending or pending[0] != returned_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    _, flow = pending
    flow.fetch_token(authorization_response=str(request.url))

    google_oauth.store_credentials(session_id, flow.credentials)
    return RedirectResponse(f"{FRONTEND_URL}?connected=1")


@router.post("/logout")
def auth_logout(request: Request):
    session_id = get_session_id(request)
    google_oauth.disconnect(session_id)
    return {"connected": False}
