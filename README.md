# Synq AI Assistant Prototype

A small prototype demonstrating: **User → Voice/Text → AI → Response → Action**.

The user types (or speaks) a request such as *"Remind me tomorrow at 10 AM to call John"*. The request goes to an
LLM (Claude, via OpenRouter) with tools for reading and creating events on the user's own Google Calendar. When
the model decides the request needs a calendar action, it calls the relevant tool, and the backend performs a
**real read or write on the user's actual Google Calendar** (connected via their own Google login, not a shared
account).

---

## Architecture

```
Browser (voice/text)
      │
      ▼
POST /chat  ──────────────────►  api/routes/chat.py        (HTTP concerns, validation)
                                        │
                                        ▼
                                 services/ai_service.py     (tool-calling orchestration)
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                              ▼
          integrations/openai_client.py      services/calendar_service.py
          (OpenRouter / Claude call)          (Google Calendar business logic)
                                                          │
                                                          ▼
                                              integrations/google_oauth.py
                                              (per-user OAuth credentials)
                                                          │
                                                          ▼
                                                Google Calendar API
```

The model is given two tools, defined in `tools/calendar_tools.py`
(`create_calendar_event`, `list_upcoming_events`). When it decides a request needs
one, `ai_service` dispatches to `calendar_service`, which performs the real Google
Calendar read/write and returns a structured result back up the chain.

## Project structure

```
kk-task/
├── backend/
│   ├── app/
│   │   ├── main.py                    # App factory: CORS, exception handler, router mount
│   │   │
│   │   ├── api/
│   │   │   ├── router.py              # Combines all route modules
│   │   │   ├── dependencies.py        # require_calendar_credentials (session → Google creds)
│   │   │   └── routes/
│   │   │       ├── health.py          # GET /health
│   │   │       ├── auth.py            # /auth/status, /auth/login, /auth/callback, /auth/logout
│   │   │       └── chat.py            # POST /chat
│   │   │
│   │   ├── core/
│   │   │   ├── config.py              # Env var loading
│   │   │   └── logging.py             # get_logger() — one configured logger for the app
│   │   │
│   │   ├── schemas/
│   │   │   ├── chat.py                # ChatRequest / ChatResponse
│   │   │   └── auth.py                # AuthStatusResponse
│   │   │
│   │   ├── services/
│   │   │   ├── ai_service.py          # Tool-calling orchestration (the "brain")
│   │   │   └── calendar_service.py    # Calendar business logic (create/list events)
│   │   │
│   │   ├── integrations/
│   │   │   ├── openai_client.py       # OpenRouter/OpenAI client + chat_completion() wrapper
│   │   │   └── google_oauth.py        # OAuth flow + in-memory session/credential store
│   │   │
│   │   ├── tools/
│   │   │   └── calendar_tools.py      # Tool JSON schemas + system prompt (what the AI can do)
│   │   │
│   │   └── exceptions.py              # SynqError, CalendarNotConnectedError, AIServiceError
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   └── unit/
│   │       ├── test_ai_service.py       # Tool-dispatch branching (mocked OpenAI + calendar_service)
│   │       └── test_calendar_service.py # Calendar request/response shape (mocked Google API)
│   │
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── .gitignore
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js                  # Chat UI, Google Calendar connect button, Web Speech API voice input
```

Each layer only talks to the one below it: routes handle HTTP and validation,
services hold business logic, integrations wrap external providers (OpenRouter,
Google). `tools/` is kept separate from `services/ai_service.py` because it
defines *what actions exist* (schemas + prompt), while the service defines *how
a request flows through them* — the two change for different reasons.

---

## Setup

### 1. Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a new project.
2. Enable the **Google Calendar API** (APIs & Services → Library).
3. Configure the **OAuth consent screen** (APIs & Services → OAuth consent screen): choose **External**, fill in
   an app name, and add your own Google account (and anyone else who'll try the demo) under **Test users** — the
   app runs in Google's "Testing" publishing status, so only accounts listed there can sign in without going
   through Google's full verification process (not needed for a prototype).
4. Create an **OAuth Client ID** (APIs & Services → Credentials → Create Credentials → OAuth client ID):
   - Application type: **Web application**
   - Authorized redirect URI: `http://localhost:8010/auth/callback` (match whatever port you run the backend on)
   - Download the resulting JSON and save it as `backend/oauth_client.json`

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env       # Windows (use `cp` on macOS/Linux)
```

Edit `.env`:

```
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-sonnet-4.5
GOOGLE_OAUTH_CLIENT_FILE=oauth_client.json
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8010/auth/callback
FRONTEND_URL=http://localhost:5500
SESSION_SECRET=any-random-string
```

Run the server:

```bash
uvicorn app.main:app --port 8010
```

Verify it's up: open `http://localhost:8010/health` → should return `{"status": "ok"}`.

### 3. Run the tests

```bash
cd backend
pytest
```

Unit tests mock the OpenAI/OpenRouter client and the Google Calendar API — no real network calls
or credentials are needed to run them.

### 4. Frontend

No build step — plain HTML/CSS/JS. Serve it (don't open the file directly — cookies/CORS need a real origin):

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`.

> Voice input uses the browser's built-in Web Speech API (Chrome recommended). It requires no extra
> setup or API key — it runs entirely client-side.

### 5. Try it

1. Click **"Connect Google Calendar"** and sign in with a Google account listed as a test user.
2. Type or speak: *"Remind me tomorrow at 10 AM to call John"* — a real event is created on your Google
   Calendar, and a confirmation card with a link appears in the chat.
3. Try: *"What's on my calendar tomorrow?"* — the assistant reads and summarizes your real upcoming events.
4. Ask it anything else — it's also a normal conversational assistant outside of scheduling requests.

---

## API overview

| Method | Path             | Description                                              |
|--------|------------------|------------------------------------------------------------|
| GET    | `/health`        | Liveness check.                                            |
| GET    | `/auth/status`   | Whether the current session has a connected Google Calendar. |
| GET    | `/auth/login`    | Redirects to Google's OAuth consent screen.                |
| GET    | `/auth/callback` | OAuth redirect target; exchanges the code for credentials.  |
| POST   | `/auth/logout`   | Drops the session's stored Google credentials.              |
| POST   | `/chat`          | `{ message, timezone }` → `{ reply, action }`. Runs the AI + tool-calling loop; `action` is populated only when `create_calendar_event` was called. |

Errors are returned as `{"detail": "..."}` with a matching HTTP status code (400 for
invalid input, 401 when Calendar isn't connected, 500 for upstream AI/Calendar failures) —
handled centrally by one `SynqError` exception hierarchy (`app/exceptions.py`) and a single
FastAPI exception handler in `main.py`, rather than scattered `raise HTTPException(...)` calls.

---

## Technical decisions

- **Backend: FastAPI, in a layered structure.** Routes (`api/routes/`) only handle HTTP concerns —
  parsing, validation, calling a service, returning a response. Business logic lives in `services/`,
  external providers are isolated in `integrations/`, and the AI's available actions are defined in
  `tools/`. This keeps each file's responsibility obvious and makes it clear where to add the next
  tool or provider without touching unrelated code. Pydantic schemas (`schemas/`) give free
  request/response validation.

- **AI provider: Claude via OpenRouter.** OpenRouter exposes an OpenAI-compatible `chat.completions` API, so the
  standard `openai` Python SDK works unmodified — just point `base_url` at OpenRouter and pass the model name
  (`anthropic/claude-sonnet-4.5`). This keeps the integration provider-agnostic: swapping models later is a
  one-line config change.

- **Tool/function calling for actions.** Rather than parsing dates/intents with regex, the model is given two
  tools: `create_calendar_event` and `list_upcoming_events`, each with a JSON schema. The model decides *when*
  to call which one and extracts/normalizes the arguments (e.g. resolving "tomorrow at 10 AM" to an actual ISO
  datetime, using the current date and the user's timezone passed in the system prompt). This is the standard,
  reliable pattern for turning natural language into a structured action.

- **The actions are real, not simulated.** `create_calendar_event` creates an actual event on Google Calendar;
  `list_upcoming_events` reads real upcoming events back. Both are independently verifiable — the created event
  shows up (and links out to) the user's real calendar, and the assistant's "what's on my calendar" answers
  reflect real data, not invented ones.

- **Google Calendar via per-user OAuth (not a shared service account).** Each user connects their *own* Google
  account through a standard "Sign in with Google" flow (Authorization Code + PKCE), so events are created on
  and read from *their* calendar — not a calendar the developer owns. Credentials are kept in memory per session
  (via an httpOnly cookie), scoped to `calendar.events` only (not full calendar access). Because the OAuth
  consent screen hasn't gone through Google's full verification (out of scope for a prototype), only accounts
  added as "test users" in Google Cloud Console can sign in — a real deployment would complete that verification
  to open it up to any Google account.

- **Timezone-aware by design.** The frontend detects the browser's IANA timezone (`Intl.DateTimeFormat().resolvedOptions().timeZone`)
  and sends it with every chat request. The backend uses it both to tell the model "now" in the user's actual
  local time (so "tomorrow at 9 AM" resolves correctly) and to tag the created Calendar event with the correct
  zone — so this works correctly for a user anywhere in the world, not just in one hardcoded timezone.

- **Voice input: Web Speech API, no backend involvement.** Speech-to-text happens entirely in the browser via
  `SpeechRecognition`, which fills the same text input the user would otherwise type into. No audio is uploaded,
  no extra API key or library is needed, and it keeps the "voice or text" paths sharing one code path server-side.

- **Secure credential handling.** `OPENROUTER_API_KEY` and the Google OAuth client secret (`oauth_client.json`)
  are read from local, git-ignored files via `python-dotenv`, and are only ever used server-side. Per-user Google
  access/refresh tokens live only in server memory, keyed by an httpOnly session cookie — never exposed to
  frontend JavaScript or sent back to the browser.

- **Frontend: plain HTML/CSS/JS.** No framework/build step needed for a single chat view with a text input, a
  mic button, a connect-calendar control, and a message list.

### Known simplifications (intentional, given the "few hours" scope)

- Sessions are stored in memory (a dict), not a real session store/database — they reset whenever the backend
  restarts. Fine for a demo; a real deployment would use a persistent, encrypted session/token store.
- No retry/rate-limit handling on the OpenRouter or Calendar API calls beyond surfacing errors to the UI.
- The OAuth consent screen is unverified by Google, so only "test user" accounts can sign in (see setup step 1.3).

---

## Deploying the backend to Render

1. Push this repo to GitHub, then in Render: **New → Web Service**, connect the repo, set **Root Directory**
   to `backend`.
2. Build/start commands:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Render assigns `$PORT` at runtime — don't
     hardcode a port).
3. Environment variables (Render dashboard → Environment):
   ```
   OPENROUTER_API_KEY=...
   OPENROUTER_MODEL=anthropic/claude-sonnet-4.5
   GOOGLE_OAUTH_CLIENT_JSON={"web":{"client_id":"...","client_secret":"...","...":"..."}}
   GOOGLE_OAUTH_REDIRECT_URI=https://your-service.onrender.com/auth/callback
   FRONTEND_URL=https://your-frontend-url
   SESSION_SECRET=some-long-random-string
   ```
   `GOOGLE_OAUTH_CLIENT_JSON` is the entire content of your local `oauth_client.json`, pasted as one line —
   there's no local file on Render, so `google_oauth.build_flow()` reads this env var instead when it's set
   (see `app/integrations/google_oauth.py`). Generate `SESSION_SECRET` with something like
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
4. In Google Cloud Console (Credentials → your OAuth client → Authorized redirect URIs), add
   `https://your-service.onrender.com/auth/callback` — Google validates this exactly, so it must match
   `GOOGLE_OAUTH_REDIRECT_URI` above.
5. Once deployed over `https://`, `OAUTHLIB_INSECURE_TRANSPORT` is not set (see `app/core/config.py` — it
   only applies when the redirect URI starts with `http://`), so no extra config is needed there.
6. Update `frontend/app.js`'s `API_URL` to point at your Render URL (or serve the frontend from the same
   origin) before using the deployed backend.

Sessions still live in memory, so a Render restart (deploy, scale event, free-tier spin-down) clears
everyone's connected-calendar state — acceptable for a prototype, called out above as a known limitation.
