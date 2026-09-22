"""Defines the calendar actions the AI model is allowed to take, and the system
prompt that instructs it when to use them. Kept separate from the orchestration
logic in services/ai_service.py so "what actions exist" is easy to find and extend
without wading through the tool-dispatch loop.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Create a real event on the user's Google Calendar. "
                "Use this whenever the user asks to be reminded of something, "
                "or asks to schedule/add a meeting or event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the event, e.g. 'Call John'",
                    },
                    "start_time": {
                        "type": "string",
                        "description": (
                            "Event start date and time as a NAIVE local datetime in the "
                            "format YYYY-MM-DDTHH:MM:SS — no timezone offset and no 'Z' "
                            "suffix, even though the current time given in the system "
                            "prompt includes one. Resolved from the user's request "
                            "relative to the current date given in the system prompt."
                        ),
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of the event in minutes. Default to 30 if not specified.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional extra details about the event.",
                    },
                },
                "required": ["title", "start_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_events",
            "description": (
                "Look up the user's real, upcoming events on their Google Calendar. "
                "Use this whenever the user asks what's on their calendar, what they "
                "have scheduled, or similar — for today, tomorrow, or the coming days."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": (
                            "How many days ahead to look, starting from now. "
                            "Use 1 for 'today', 2 for 'tomorrow', 7 for 'this week', etc."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
]

SYSTEM_PROMPT = """You are Synq, a helpful, friendly AI assistant. Chat naturally like any
capable assistant would — answer questions, make conversation, help with whatever the user
brings up. The current date and time is: {now}, in the user's local time zone, {timezone}
(this is already local time, not UTC — treat any time the user mentions as being in this
same zone, and any start_time you compute for a tool call must also be a naive local
datetime in this same zone, not UTC).

You additionally have two abilities on the user's real Google Calendar:
- create_calendar_event: whenever the user asks to be reminded of something, or asks to
  schedule/add/book a meeting or event. Resolve a sensible title and an ISO 8601 start_time
  from their request (e.g. "tomorrow at 10 AM" -> compute the actual date from the current
  date above). Confirm what you did in plain language afterward.
- list_upcoming_events: whenever the user asks what's on their calendar, what they have
  scheduled, or similar. Summarize the real events returned in plain language — don't
  invent events that weren't returned, and say so plainly if none were found.

For everything else, just respond normally — don't mention the calendar tool, don't explain
your own capabilities unprompted, and don't steer the conversation toward scheduling. Reply the
way a real assistant would: naturally, concisely, and only about what the user actually asked.
"""
