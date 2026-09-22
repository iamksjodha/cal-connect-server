from pydantic import BaseModel


class AuthStatusResponse(BaseModel):
    connected: bool
