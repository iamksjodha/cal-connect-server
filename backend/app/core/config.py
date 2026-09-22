import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

GOOGLE_OAUTH_CLIENT_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE", "oauth_client.json")
# In deployed environments (e.g. Render) there's no local file to read — the whole
# oauth_client.json content is pasted into this env var instead. When set, it takes
# priority over GOOGLE_OAUTH_CLIENT_FILE.
GOOGLE_OAUTH_CLIENT_JSON = os.getenv("GOOGLE_OAUTH_CLIENT_JSON")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")
# Comma-separated list of extra allowed CORS origins (e.g. a local dev frontend
# while testing against a deployed backend). FRONTEND_URL is always included.
_extra_origins = os.getenv("EXTRA_CORS_ORIGINS", "")
ALLOWED_ORIGINS = [FRONTEND_URL] + [
    origin.strip() for origin in _extra_origins.split(",") if origin.strip()
]
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-secret-change-me")

IS_HTTPS_DEPLOYMENT = GOOGLE_OAUTH_REDIRECT_URI.startswith("https://")

# google-auth-oauthlib refuses to exchange tokens over plain http by default.
# This is a local prototype running on http://localhost, not a public deployment,
# so the check is safe to relax here (never do this for a real https deployment).
if not IS_HTTPS_DEPLOYMENT:
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill in your key."
    )
