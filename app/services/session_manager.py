import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from functools import lru_cache

from app.core.config import get_settings
from app.core.logger import get_logger
from app.schemas.models import SessionResult, SessionStatus, AgentMessage

logger = get_logger("codecrew.session")


class SessionManager:
    """
    Manages session storage — saves every agent output and message
    to disk so sessions are fully auditable.
    """

    def __init__(self):
        settings = get_settings()
        self.session_dir = Path(settings.SESSION_DIR)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SessionManager ready — dir={self.session_dir}")

    def create_session(self, requirement: str, language: str) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())[:8]  # Short ID for readability

        session_data = {
            "session_id": session_id,
            "status": SessionStatus.PENDING,
            "requirement": requirement,
            "language": language,
            "created_at": datetime.now().isoformat(),
            "agent_messages": [],
            "total_review_rounds": 0,
            "initial_quality_score": 0,
            "final_quality_score": 0,
        }

        self._save(session_id, session_data)
        logger.info(f"Session created: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Load session from disk."""
        path = self._path(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def update_status(self, session_id: str, status: SessionStatus):
        """Update session status."""
        data = self.get_session(session_id)
        if data:
            data["status"] = status
            self._save(session_id, data)

    def add_message(self, session_id: str, message: AgentMessage):
        """Add an agent message to the session log."""
        data = self.get_session(session_id)
        if data:
            data["agent_messages"].append(message.model_dump())
            self._save(session_id, data)

    def save_agent_output(self, session_id: str, agent: str, output: dict):
        """Save a specific agent's output."""
        data = self.get_session(session_id)
        if data:
            key = f"{agent.lower()}_output"
            data[key] = output
            self._save(session_id, data)

    def update_scores(
        self,
        session_id: str,
        initial: int = None,
        final: int = None,
        rounds: int = None,
    ):
        """Update quality scores and review rounds."""
        data = self.get_session(session_id)
        if data:
            if initial is not None:
                data["initial_quality_score"] = initial
            if final is not None:
                data["final_quality_score"] = final
            if rounds is not None:
                data["total_review_rounds"] = rounds
            self._save(session_id, data)

    def list_sessions(self) -> list:
        """List all sessions sorted by creation time."""
        sessions = []
        for path in self.session_dir.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
                requirement = data["requirement"]
                truncated = requirement[:60] + ("..." if len(requirement) > 60 else "")
                sessions.append({
                    "session_id": data["session_id"],
                    "status": data["status"],
                    "requirement": truncated,
                    "created_at": data.get("created_at", ""),
                    "language": data.get("language", ""),
                })
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def _path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"

    def _save(self, session_id: str, data: dict):
        with open(self._path(session_id), "w") as f:
            json.dump(data, f, indent=2)


@lru_cache()
def get_session_manager() -> SessionManager:
    return SessionManager()