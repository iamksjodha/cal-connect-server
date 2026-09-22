import json
from datetime import datetime
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials

from app.integrations.openai_client import chat_completion
from app.services import calendar_service
from app.tools.calendar_tools import SYSTEM_PROMPT, TOOL_SCHEMAS


def handle_user_message(user_message: str, credentials: Credentials | None, timezone: str) -> dict:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        timezone = "Asia/Kolkata"
        tz = ZoneInfo(timezone)

    now = datetime.now(tz).isoformat(timespec="seconds")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(now=now, timezone=timezone)},
        {"role": "user", "content": user_message},
    ]

    response = chat_completion(messages, tools=TOOL_SCHEMAS)

    choice = response.choices[0]
    tool_calls = choice.message.tool_calls
    action_result = None

    if tool_calls:
        messages.append(choice.message)

        for tool_call in tool_calls:
            if tool_call.function.name not in ("create_calendar_event", "list_upcoming_events"):
                tool_output = {"error": f"Unknown tool {tool_call.function.name}"}
            elif credentials is None:
                tool_output = {
                    "error": (
                        "Google Calendar is not connected. Tell the user they need to "
                        "connect their calendar first before you can do this."
                    )
                }
            elif tool_call.function.name == "create_calendar_event":
                args = json.loads(tool_call.function.arguments)
                action_result = calendar_service.create_event(
                    credentials=credentials,
                    title=args["title"],
                    start_time=args["start_time"],
                    duration_minutes=args.get("duration_minutes", 30),
                    description=args.get("description", ""),
                    timezone=timezone,
                )
                tool_output = action_result
            else:
                args = json.loads(tool_call.function.arguments)
                tool_output = calendar_service.list_upcoming_events(
                    credentials=credentials,
                    timezone=timezone,
                    days_ahead=args.get("days_ahead", 7),
                )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_output),
                }
            )

        follow_up = chat_completion(messages)
        reply_text = follow_up.choices[0].message.content
    else:
        reply_text = choice.message.content

    return {
        "reply": reply_text,
        "action": action_result,
    }
