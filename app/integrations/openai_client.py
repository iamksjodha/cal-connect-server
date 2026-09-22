from openai import OpenAI

from app.core.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


def chat_completion(messages: list[dict], tools: list[dict] | None = None, max_tokens: int = 1024):
    """Thin wrapper around the OpenRouter/OpenAI chat.completions call used by ai_service."""
    kwargs = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if tools is not None:
        kwargs["tools"] = tools

    return _client.chat.completions.create(**kwargs)
