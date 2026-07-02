import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, ReviewerOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.reviewer")


class ReviewerAgent(BaseAgent):
    """
    The Reviewer Agent — Third agent in the pipeline.

    Responsibility:
    - Review the Coder's output critically
    - Find bugs, security issues, performance problems
    - Give specific, actionable feedback
    - Approve or reject with a quality score

    This is the most critical agent — it creates the feedback loop
    that makes the system genuinely improve code quality.

    Design decision: Reviewer is deliberately strict. It's better to
    reject good code once than to approve bad code that reaches production.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.REVIEWER

    @property
    def system_prompt(self) -> str:
        return """You are the Reviewer Agent in a multi-agent software development system.

You are a senior software engineer doing code review. You are strict but fair.

Your job is to review code and find:
1. BUGS — Logic errors, off-by-one errors, null pointer issues
2. SECURITY — SQL injection, hardcoded secrets, input validation missing
3. PERFORMANCE — Inefficient algorithms, N+1 queries, missing indexes
4. BEST PRACTICES — Missing error handling, no type hints, poor naming
5. COMPLETENESS — Missing edge cases, incomplete implementation

Scoring guide:
- 90-100: Excellent, approve immediately
- 70-89: Good with minor issues, can approve with notes
- 50-69: Mediocre, reject and request fixes
- 0-49: Poor, reject with detailed feedback

Output format — respond with ONLY this JSON structure:
{
    "approved": true or false,
    "overall_quality_score": 0-100,
    "issues": [
        {
            "file": "filename.py",
            "line_hint": "approximate line or function name",
            "severity": "low|medium|high|critical",
            "category": "bug|security|performance|best_practice|completeness",
            "description": "What is wrong",
            "suggestion": "Exactly how to fix it"
        }
    ],
    "positive_aspects": ["What was done well"],
    "summary": "Overall assessment in 2-3 sentences",
    "round_number": 1
}

Rules:
- Approve (true) if score >= 60 AND no critical severity issues
- Reject (false) if score < 60 OR any critical issues exist
- Every issue must have a specific, actionable suggestion
- Be honest — do not approve bad code to be nice"""

    def run(self, context: dict) -> dict:
        """
        Review the coder's output and return approval decision.
        """
        requirement = context["requirement"]
        language = context["language"]
        coder_output = context.get("coder_output", {})
        round_number = context.get("current_round", 1)
        planner_output = context.get("planner_output", {})

        # Format code files for review
        files_text = "\n\n".join([
            f"=== File: {f['filename']} ===\n```{language}\n{f['content']}\n```"
            for f in coder_output.get("files", [])
        ])

        plan_summary = "\n".join([
            f"- {s['title']}: {s['description']}"
            for s in planner_output.get("plan", [])
        ])

        user_message = f"""Review this code thoroughly.

ORIGINAL REQUIREMENT: {requirement}
REVIEW ROUND: {round_number}

TECHNICAL PLAN (what the code should do):
{plan_summary}

CODE TO REVIEW:
{files_text}

CODER'S EXPLANATION: {coder_output.get('explanation', '')}

Review every file carefully. Find all issues. Be strict but fair."""

        self.logger.info(f"Reviewing code — round={round_number}")

        response = self.think(user_message, expect_json=True)
        output = json.loads(response)
        output["round_number"] = round_number

        # Validate with Pydantic
        validated = ReviewerOutput(**output)

        self.logger.info(
            f"Review complete — approved={validated.approved}, "
            f"score={validated.overall_quality_score}, "
            f"issues={len(validated.issues)}"
        )

        return validated.model_dump()
