import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, PlannerOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.planner")


class PlannerAgent(BaseAgent):
    """
    The Planner Agent — First agent in the pipeline.

    Responsibility:
    - Understand the user's requirement deeply
    - Identify any ambiguities
    - Break the requirement into clear technical steps
    - Define the tech stack
    - Create a plan the Coder can follow precisely

    Design decision: Planner never writes code — it only plans.
    Separation of concerns makes each agent better at its job.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.PLANNER

    @property
    def system_prompt(self) -> str:
        return """You are the Planner Agent in a multi-agent software development system.

Your ONLY job is to understand requirements and create a clear technical plan.
You NEVER write code — that is the Coder's job.

Your responsibilities:
1. Understand exactly what the user wants to build
2. Identify any unclear or missing information
3. Break the requirement into numbered technical steps
4. Define what files need to be created
5. Specify the tech stack clearly

Output format — respond with ONLY this JSON structure:
{
    "understood_requirement": "Clear restatement of what needs to be built",
    "clarifying_questions": [
        {
            "question": "What question would you ask?",
            "reason": "Why this information is needed"
        }
    ],
    "plan": [
        {
            "step_number": 1,
            "title": "Short title",
            "description": "Detailed description of what to implement",
            "files_to_create": ["filename.py"]
        }
    ],
    "tech_stack": ["FastAPI", "SQLite", "Pydantic"],
    "estimated_complexity": "low|medium|high"
}

Rules:
- If the requirement is clear, clarifying_questions can be empty list []
- Be specific in descriptions — the Coder reads this plan exactly
- List ALL files that need to be created
- Think about error handling, validation, and edge cases in your plan"""

    def run(self, context: dict) -> dict:
        """
        Create a technical plan from the user's requirement.
        """
        requirement = context["requirement"]
        language = context["language"]
        framework = context.get("framework", "")
        additional_context = context.get("additional_context", "")

        user_message = f"""Create a technical plan for this requirement and return as JSON.

REQUIREMENT: {requirement}
LANGUAGE: {language}
FRAMEWORK: {framework if framework else "Choose the best one"}

Return JSON with plan array containing at least 3-5 steps."""

        self.logger.info(f"Planning requirement: {requirement[:60]}...")

        response = self.think(user_message, expect_json=True)
        output = json.loads(response)

        # Fix empty or missing fields
        if not output.get("plan"):
            output["plan"] = [{"step_number":1,"title":"Implement requirement","description":requirement,"files_to_create":["main.py"]}]
        if not output.get("tech_stack"):
            output["tech_stack"] = [language]
        if not output.get("estimated_complexity"):
            output["estimated_complexity"] = "medium"
        if not output.get("understood_requirement"):
            output["understood_requirement"] = requirement
        if not output.get("clarifying_questions"):
            output["clarifying_questions"] = []

        # Validate with Pydantic
        validated = PlannerOutput(**output)

        self.logger.info(
            f"Plan created — {len(validated.plan)} steps, "
            f"complexity={validated.estimated_complexity}"
        )

        return validated.model_dump()
