import json
from unittest.mock import MagicMock, patch

from app.services import ai_service


def _make_completion(content=None, tool_calls=None):
    completion = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    choice.message.tool_calls = tool_calls
    completion.choices = [choice]
    return completion


def _make_tool_call(name, arguments: dict, call_id="call_1"):
    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = name
    tool_call.function.arguments = json.dumps(arguments)
    return tool_call


@patch("app.services.ai_service.chat_completion")
def test_plain_message_does_not_call_any_tool(mock_chat_completion):
    mock_chat_completion.return_value = _make_completion(content="Hello! How can I help?")

    result = ai_service.handle_user_message("hi", credentials=MagicMock(), timezone="Asia/Kolkata")

    assert result["reply"] == "Hello! How can I help?"
    assert result["action"] is None
    # Only one call: no tool was invoked, so there's no follow-up completion.
    assert mock_chat_completion.call_count == 1


@patch("app.services.ai_service.calendar_service")
@patch("app.services.ai_service.chat_completion")
def test_create_calendar_event_tool_call_populates_action(mock_chat_completion, mock_calendar_service):
    tool_call = _make_tool_call(
        "create_calendar_event",
        {"title": "Call John", "start_time": "2026-09-24T09:00:00"},
    )
    first_response = _make_completion(tool_calls=[tool_call])
    follow_up_response = _make_completion(content="Done — I've added it to your calendar.")
    mock_chat_completion.side_effect = [first_response, follow_up_response]

    mock_calendar_service.create_event.return_value = {
        "id": "evt1",
        "title": "Call John",
        "start": "2026-09-24T09:00:00",
        "end": "2026-09-24T09:30:00",
        "link": "https://calendar.google.com/event?eid=evt1",
    }

    result = ai_service.handle_user_message(
        "Remind me tomorrow at 9 AM to call John",
        credentials=MagicMock(),
        timezone="Asia/Kolkata",
    )

    mock_calendar_service.create_event.assert_called_once()
    _, kwargs = mock_calendar_service.create_event.call_args
    assert kwargs["title"] == "Call John"
    assert kwargs["start_time"] == "2026-09-24T09:00:00"
    assert kwargs["timezone"] == "Asia/Kolkata"

    assert result["action"]["id"] == "evt1"
    assert result["reply"] == "Done — I've added it to your calendar."
    assert mock_chat_completion.call_count == 2


@patch("app.services.ai_service.calendar_service")
@patch("app.services.ai_service.chat_completion")
def test_list_upcoming_events_tool_call_does_not_populate_action(mock_chat_completion, mock_calendar_service):
    tool_call = _make_tool_call("list_upcoming_events", {"days_ahead": 2})
    first_response = _make_completion(tool_calls=[tool_call])
    follow_up_response = _make_completion(content="You have one event tomorrow.")
    mock_chat_completion.side_effect = [first_response, follow_up_response]

    mock_calendar_service.list_upcoming_events.return_value = [
        {"title": "Dentist", "start": "2026-09-24T09:00:00", "end": "2026-09-24T09:30:00", "link": "https://x"}
    ]

    result = ai_service.handle_user_message(
        "What's on my calendar tomorrow?", credentials=MagicMock(), timezone="Asia/Kolkata"
    )

    mock_calendar_service.list_upcoming_events.assert_called_once()
    assert result["action"] is None
    assert result["reply"] == "You have one event tomorrow."


@patch("app.services.ai_service.chat_completion")
def test_plain_message_works_without_calendar_credentials(mock_chat_completion):
    mock_chat_completion.return_value = _make_completion(content="Hello! How can I help?")

    result = ai_service.handle_user_message("hi", credentials=None, timezone="Asia/Kolkata")

    assert result["reply"] == "Hello! How can I help?"
    assert result["action"] is None


@patch("app.services.ai_service.calendar_service")
@patch("app.services.ai_service.chat_completion")
def test_calendar_tool_call_without_credentials_does_not_raise(mock_chat_completion, mock_calendar_service):
    tool_call = _make_tool_call("list_upcoming_events", {"days_ahead": 2})
    first_response = _make_completion(tool_calls=[tool_call])
    follow_up_response = _make_completion(
        content="You'll need to connect your Google Calendar first."
    )
    mock_chat_completion.side_effect = [first_response, follow_up_response]

    result = ai_service.handle_user_message(
        "What's on my calendar tomorrow?", credentials=None, timezone="Asia/Kolkata"
    )

    mock_calendar_service.list_upcoming_events.assert_not_called()
    assert result["action"] is None
    assert result["reply"] == "You'll need to connect your Google Calendar first."


@patch("app.services.ai_service.chat_completion")
def test_invalid_timezone_falls_back_to_asia_kolkata(mock_chat_completion):
    mock_chat_completion.return_value = _make_completion(content="ok")

    result = ai_service.handle_user_message(
        "hi", credentials=MagicMock(), timezone="Not/ARealZone"
    )

    assert result["reply"] == "ok"
    # First positional arg to chat_completion is the messages list; the system
    # prompt (messages[0]) should mention the fallback timezone, not the bad one.
    messages_arg = mock_chat_completion.call_args[0][0]
    assert "Asia/Kolkata" in messages_arg[0]["content"]
