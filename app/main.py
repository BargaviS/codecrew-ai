from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.api.routes.main import router
from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.llm_client import get_llm_client
from app.services.session_manager import get_session_manager

logger = get_logger("codecrew.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} [{settings.ENV}]")
    get_llm_client()
    get_session_manager()
    logger.info("All services ready")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-agent AI system that plans, codes, reviews, tests and documents software",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def root():
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"app": settings.APP_NAME, "docs": "/docs"}

    return app


app = create_app()
