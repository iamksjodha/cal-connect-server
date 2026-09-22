from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import FRONTEND_URL
from app.exceptions import SynqError


def create_app() -> FastAPI:
    app = FastAPI(title="Synq AI Assistant Prototype")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(SynqError)
    def handle_synq_error(request: Request, exc: SynqError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(api_router)

    return app


app = create_app()
