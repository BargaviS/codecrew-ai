import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, CoderOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.coder")


class CoderAgent(BaseAgent):

    @property
    def name(self) -> AgentName:
        return AgentName.CODER

    @property
    def system_prompt(self) -> str:
        return """You are an expert software engineer. Write clean, working code.

STRICT JSON RULES:
- Return ONLY valid JSON
- NEVER use triple quotes inside JSON strings
- Use single line # comments only, never docstrings
- Escape all special characters in strings
- Use \n for newlines inside JSON strings

Output ONLY this JSON:
{
    "files": [
        {
            "filename": "main.py",
            "content": "# complete file content here as single line string",
            "description": "what this file does"
        }
    ],
    "explanation": "brief explanation",
    "assumptions_made": ["assumption 1"]
}

Code standards:
- Add type hints on all functions
- Add error handling with try/except
- Validate inputs
- Handle edge cases
- Write clean readable code
- NEVER truncate code with comments like rest of code here"""

    def run(self, context: dict) -> dict:
        requirement = context["requirement"]
        language = context["language"]
        planner_output = context.get("planner_output", {})
        reviewer_feedback = context.get("reviewer_output")
        previous_code = context.get("coder_output")
        round_number = context.get("current_round", 1)

        if reviewer_feedback and previous_code and round_number > 1:
            issues = reviewer_feedback.get("issues", [])
            issues_text = "\n".join([
                f"- {i['severity'].upper()} in {i['file']}: {i['description']} -> Fix: {i['suggestion']}"
                for i in issues
            ])

            previous_files = "\n\n".join([
                f"File: {f['filename']}\n{f['content']}"
                for f in previous_code.get("files", [])
            ])

            user_message = f"""Fix this code based on reviewer feedback.

REQUIREMENT: {requirement}

PREVIOUS CODE:
{previous_files}

ISSUES TO FIX:
{issues_text}

Fix ALL issues. Return complete fixed files. No placeholders."""

        else:
            plan_steps = planner_output.get("plan", [])
            plan_text = "\n".join([
                f"Step {s['step_number']}: {s['title']} - {s['description']}"
                for s in plan_steps
            ])

            user_message = f"""Write production code for this requirement.

REQUIREMENT: {requirement}
LANGUAGE: {language}
TECH STACK: {', '.join(planner_output.get('tech_stack', []))}

PLAN:
{plan_text}

Write complete, working code. No placeholders."""

        self.logger.info(f"Coding round={round_number}")
        response = self.think(user_message, expect_json=True)
        output = json.loads(response)
        validated = CoderOutput(**output)
        self.logger.info(f"Code written: {len(validated.files)} files round={round_number}")
        return validated.model_dump()
