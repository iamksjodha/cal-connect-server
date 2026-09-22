from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    timezone: Optional[str] = "Asia/Kolkata"


class ChatResponse(BaseModel):
    reply: Optional[str] = None
    action: Optional[dict] = None
