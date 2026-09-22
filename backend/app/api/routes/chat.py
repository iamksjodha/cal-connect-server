from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import get_calendar_credentials
from app.core.logging import get_logger
from app.exceptions import AIServiceError
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import handle_user_message

router = APIRouter(tags=["chat"])
logger = get_logger("synq.chat")


@router.post("/chat", response_model=ChatResponse)
def chat(request: Request, body: ChatRequest):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    credentials = get_calendar_credentials(request)

    try:
        result = handle_user_message(body.message, credentials, body.timezone)
    except Exception as exc:
        logger.exception("chat request failed")
        raise AIServiceError(str(exc)) from exc

    return ChatResponse(**result)
