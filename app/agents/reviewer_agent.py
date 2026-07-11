import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, ReviewerOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.reviewer")


class ReviewerAgent(BaseAgent):

    @property
    def name(self) -> AgentName:
        return AgentName.REVIEWER

    @property
    def system_prompt(self) -> str:
        return """You are a senior software engineer doing code review.

You review code and score it from 0-100.

Scoring guide:
- 90-100: Excellent code, approve immediately
- 75-89: Good code with minor issues, APPROVE with notes
- 60-74: Decent code, approve if no critical bugs
- Below 60: Poor code, reject

IMPORTANT RULES:
- Be FAIR and REASONABLE - most working code scores 70+
- Only reject if there are REAL bugs that would break the code
- Style issues, minor improvements = approve with notes
- Missing docstrings, minor naming = NOT a reason to reject
- If code works correctly and handles errors = APPROVE

ALWAYS CHECK FOR THESE SPECIFIC HIGH-SEVERITY ISSUES:
- Passwords or secrets stored/logged in plain text (must be hashed, e.g. bcrypt/passlib) — this is CRITICAL severity, always flag
- Broad `except Exception` blocks that would catch and mask an
  intentionally-raised HTTPException (e.g. a 404 getting silently
  turned into a 500) — this is a HIGH severity bug
- Database/file connections opened but never closed (resource leaks) — MEDIUM severity
- Error responses returned with a 200 status code instead of the
  correct HTTP status (e.g. auth failures returning 200 with an
  "error" field instead of 401/403) — HIGH severity
- Unused imports — LOW severity, note but don't reject solely for this

Output ONLY this JSON:
{
    "approved": true or false,
    "overall_quality_score": 0-100,
    "issues": [
        {
            "file": "filename.py",
            "line_hint": "function name or line number",
            "severity": "low|medium|high|critical",
            "category": "bug|security|performance|best_practice|completeness",
            "description": "What is wrong",
            "suggestion": "How to fix it"
        }
    ],
    "positive_aspects": ["What was done well"],
    "summary": "2 sentence assessment",
    "round_number": 1
}

Approve if score >= 65 and no critical bugs.
Reject only if score < 65 or critical bugs exist."""

    def run(self, context: dict) -> dict:
        requirement = context["requirement"]
        language = context["language"]
        coder_output = context.get("coder_output", {})
        round_number = context.get("current_round", 1)
        planner_output = context.get("planner_output", {})

        files_text = "\n\n".join([
            f"=== {f['filename']} ===\n{f['content']}"
            for f in coder_output.get("files", [])
        ])

        user_message = f"""Review this code for requirement: {requirement}
Language: {language}
Review Round: {round_number}

CODE:
{files_text}

Be fair. Working code that handles errors scores 70+. Only reject for real bugs."""

        self.logger.info(f"Reviewing code round={round_number}")
        response = self.think(user_message, expect_json=True)
        output = json.loads(response)
        output["round_number"] = round_number
        validated = ReviewerOutput(**output)
        self.logger.info(f"Review: approved={validated.approved} score={validated.overall_quality_score}")
        return validated.model_dump()
