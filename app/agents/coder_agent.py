import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, CoderOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.coder")


class CoderAgent(BaseAgent):
    """
    The Coder Agent — Second agent in the pipeline.

    Responsibility:
    - Read the Planner's technical plan
    - Write clean, production-grade code
    - Follow all coding standards
    - Fix issues when Reviewer rejects the code

    Design decision: Coder always reads the Reviewer's feedback
    when rewriting — it doesn't start fresh, it improves the existing code.
    This mirrors how real developers handle code review.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.CODER

    @property
    def system_prompt(self) -> str:
        return """You are the Coder Agent in a multi-agent software development system.

Your job is to write clean, production-grade code based on the Planner's technical plan.

Coding standards you MUST follow:
1. Type hints on ALL functions and methods
2. Docstrings on ALL classes and functions
3. Proper error handling with try/except where needed
4. No hardcoded values — use constants or config
5. Meaningful variable and function names
6. Single responsibility principle — each function does ONE thing
7. Input validation where user data is involved
8. Proper imports organized (stdlib → third-party → local)

Output format — respond with ONLY this JSON structure:
{
    "files": [
        {
            "filename": "main.py",
            "content": "# Complete file content here",
            "description": "What this file does"
        }
    ],
    "explanation": "Brief explanation of implementation decisions",
    "assumptions_made": ["Assumption 1", "Assumption 2"]
}

Rules:
- CRITICAL: Never use triple quotes in code, use single line comments for docstrings
- Write COMPLETE files — never truncate with comments like "# rest of code here"
- Handle ALL edge cases mentioned in the plan
- If fixing reviewer feedback, address EVERY issue mentioned
- Code must be immediately runnable — no placeholders"""

    def run(self, context: dict) -> dict:
        """
        Write code based on the plan. If reviewer feedback exists,
        fix the issues in the existing code.
        """
        requirement = context["requirement"]
        language = context["language"]
        planner_output = context.get("planner_output", {})
        reviewer_feedback = context.get("reviewer_output")
        previous_code = context.get("coder_output")
        round_number = context.get("current_round", 1)

        if reviewer_feedback and previous_code:
            # This is a fix round — reviewer rejected the code
            self.logger.info(f"Fix round {round_number} — addressing reviewer feedback")

            issues = reviewer_feedback.get("issues", [])
            issues_text = "\n".join([
                f"- [{i['severity'].upper()}] {i['file']} line {i['line_hint']}: "
                f"{i['description']} → Fix: {i['suggestion']}"
                for i in issues
            ])

            previous_files = "\n\n".join([
                f"File: {f['filename']}\n```{language}\n{f['content']}\n```"
                for f in previous_code.get("files", [])
            ])

            user_message = f"""TASK: Fix the code based on reviewer feedback.

ORIGINAL REQUIREMENT: {requirement}

YOUR PREVIOUS CODE:
{previous_files}

REVIEWER REJECTION REASON:
{reviewer_feedback.get('summary', '')}

SPECIFIC ISSUES TO FIX:
{issues_text}

Fix ALL issues listed above. Keep working code unchanged. Return complete fixed files."""

        else:
            # First round — write code from scratch
            self.logger.info("Round 1 — writing code from plan")

            plan_steps = planner_output.get("plan", [])
            plan_text = "\n".join([
                f"Step {s['step_number']}: {s['title']}\n  {s['description']}\n  Files: {', '.join(s['files_to_create'])}"
                for s in plan_steps
            ])

            tech_stack = ", ".join(planner_output.get("tech_stack", []))

            user_message = f"""TASK: Write production-grade code for this requirement.

REQUIREMENT: {requirement}
LANGUAGE: {language}
TECH STACK: {tech_stack}

TECHNICAL PLAN:
{plan_text}

Write complete, runnable code following all coding standards."""

        response = self.think(user_message, expect_json=True)
        output = json.loads(response)

        # Validate with Pydantic
        validated = CoderOutput(**output)

        self.logger.info(
            f"Code written — {len(validated.files)} files, "
            f"round={round_number}"
        )

        return validated.model_dump()
# patch applied below in class
