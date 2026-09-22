from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def create_event(
    credentials: Credentials,
    title: str,
    start_time: str,
    duration_minutes: int = 30,
    description: str = "",
    timezone: str = "Asia/Kolkata",
) -> dict:
    """Create a real event on the authenticated user's primary Google Calendar."""
    calendar = build("calendar", "v3", credentials=credentials)

    start_dt = datetime.fromisoformat(start_time)
    # The model sometimes echoes back a timezone offset (e.g. because "now" in the
    # prompt carried one). Google's API takes the timezone from the separate
    # `timeZone` field below, so a `dateTime` that also carries a UTC offset gets
    # double-applied (e.g. 9 AM IST becomes 3:30 AM). Normalize to naive local time.
    if start_dt.tzinfo is not None:
        start_dt = start_dt.replace(tzinfo=None)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone},
    }

    created_event = calendar.events().insert(
        calendarId="primary", body=event_body
    ).execute()

    return {
        "id": created_event.get("id"),
        "title": created_event.get("summary"),
        "start": created_event.get("start", {}).get("dateTime"),
        "end": created_event.get("end", {}).get("dateTime"),
        "link": created_event.get("htmlLink"),
    }


def list_upcoming_events(
    credentials: Credentials,
    timezone: str = "Asia/Kolkata",
    days_ahead: int = 7,
    max_results: int = 20,
) -> list[dict]:
    """List the authenticated user's upcoming events on their primary calendar."""
    calendar = build("calendar", "v3", credentials=credentials)

    now = datetime.now(ZoneInfo(timezone))
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    events_result = calendar.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    return [
        {
            "title": event.get("summary", "(no title)"),
            "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
            "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
            "link": event.get("htmlLink"),
        }
        for event in events
    ]
