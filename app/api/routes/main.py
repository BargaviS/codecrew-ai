import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.models import (
    SessionRequest, SessionResponse, SessionStatus, HealthResponse
)
from app.services.session_manager import get_session_manager
from app.agents.orchestrator import Orchestrator
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("codecrew.routes")
router = APIRouter()

# Single orchestrator instance reused across requests
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        env=settings.ENV,
        agents=["Planner", "Coder", "Reviewer", "Tester", "Documenter"],
    )


@router.post("/session", response_model=SessionResponse, tags=["Sessions"])
def create_session(request: SessionRequest):
    """
    Create a new coding session.
    Returns session_id — use this to stream results.
    """
    if not request.requirement.strip():
        raise HTTPException(status_code=400, detail="Requirement cannot be empty")

    sm = get_session_manager()
    session_id = sm.create_session(
        requirement=request.requirement,
        language=request.language.value,
    )

    logger.info(f"Session created: {session_id} — {request.requirement[:50]}")

    return SessionResponse(
        session_id=session_id,
        status=SessionStatus.PENDING,
        message="Session created. Call /session/{id}/stream to start.",
    )


@router.get("/session/{session_id}/stream", tags=["Sessions"])
async def stream_session(session_id: str, framework: str = "", additional_context: str = ""):
    """
    Stream agent outputs in real-time using Server-Sent Events.

    This endpoint runs the full agent pipeline and streams each
    agent's progress as it happens — users watch agents work live.
    """
    sm = get_session_manager()
    session = sm.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Use the requirement/language saved when the session was created —
    # not re-accepted here — so the two can never disagree with each other.
    context = {
        "requirement": session["requirement"],
        "language": session["language"],
        "framework": framework,
        "additional_context": additional_context,
    }

    orchestrator = get_orchestrator()

    async def event_generator():
        async for event in orchestrator.run(session_id, context):
            # Format as SSE
            data = json.dumps(event)
            yield f"data: {data}\n\n"
            await asyncio.sleep(0)  # Allow other tasks to run

        yield "data: {\"event_type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/session/{session_id}", tags=["Sessions"])
def get_session(session_id: str):
    """Get full session result including all agent outputs."""
    sm = get_session_manager()
    session = sm.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return session


@router.get("/sessions", tags=["Sessions"])
def list_sessions():
    """List all sessions with their status."""
    sm = get_session_manager()
    return {"sessions": sm.list_sessions()}
