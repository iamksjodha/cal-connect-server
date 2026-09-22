from unittest.mock import MagicMock, patch

from app.services import calendar_service


@patch("app.services.calendar_service.build")
def test_create_event_sends_correct_payload(mock_build):
    mock_calendar = MagicMock()
    mock_build.return_value = mock_calendar
    mock_calendar.events().insert().execute.return_value = {
        "id": "evt123",
        "summary": "Call John",
        "start": {"dateTime": "2026-09-24T09:00:00+05:30"},
        "end": {"dateTime": "2026-09-24T09:30:00+05:30"},
        "htmlLink": "https://calendar.google.com/event?eid=evt123",
    }

    result = calendar_service.create_event(
        credentials=MagicMock(),
        title="Call John",
        start_time="2026-09-24T09:00:00",
        duration_minutes=30,
        timezone="Asia/Kolkata",
    )

    insert_call = mock_calendar.events().insert
    _, kwargs = insert_call.call_args
    body = kwargs["body"]

    assert body["summary"] == "Call John"
    assert body["start"]["dateTime"] == "2026-09-24T09:00:00"
    assert body["start"]["timeZone"] == "Asia/Kolkata"
    assert body["end"]["dateTime"] == "2026-09-24T09:30:00"
    assert kwargs["calendarId"] if "calendarId" in kwargs else True


@patch("app.services.calendar_service.build")
def test_create_event_strips_offset_from_start_time(mock_build):
    """Regression test: if the model echoes back a UTC offset in start_time
    (e.g. "2026-09-24T09:00:00+05:30"), Google would double-apply the timezone
    (offset + the separate timeZone field), shifting a 9 AM request to 3:30 AM.
    The offset must be stripped so only the `timeZone` field controls the zone.
    """
    mock_calendar = MagicMock()
    mock_build.return_value = mock_calendar
    mock_calendar.events().insert().execute.return_value = {}

    calendar_service.create_event(
        credentials=MagicMock(),
        title="Call John",
        start_time="2026-09-24T09:00:00+05:30",
        duration_minutes=30,
        timezone="Asia/Kolkata",
    )

    _, kwargs = mock_calendar.events().insert.call_args
    body = kwargs["body"]

    assert body["start"]["dateTime"] == "2026-09-24T09:00:00"
    assert body["end"]["dateTime"] == "2026-09-24T09:30:00"


@patch("app.services.calendar_service.build")
def test_list_upcoming_events_maps_results(mock_build):
    mock_calendar = MagicMock()
    mock_build.return_value = mock_calendar
    mock_calendar.events().list().execute.return_value = {
        "items": [
            {
                "summary": "Team standup",
                "start": {"dateTime": "2026-09-23T10:00:00+05:30"},
                "end": {"dateTime": "2026-09-23T10:30:00+05:30"},
                "htmlLink": "https://calendar.google.com/event?eid=evt456",
            }
        ]
    }

    events = calendar_service.list_upcoming_events(
        credentials=MagicMock(), timezone="Asia/Kolkata", days_ahead=1
    )

    assert len(events) == 1
    assert events[0]["title"] == "Team standup"
    assert events[0]["start"] == "2026-09-23T10:00:00+05:30"


@patch("app.services.calendar_service.build")
def test_list_upcoming_events_returns_empty_list_when_no_items(mock_build):
    mock_calendar = MagicMock()
    mock_build.return_value = mock_calendar
    mock_calendar.events().list().execute.return_value = {}

    events = calendar_service.list_upcoming_events(credentials=MagicMock())

    assert events == []
