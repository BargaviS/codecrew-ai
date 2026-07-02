import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, DocumenterOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.documenter")


class DocumenterAgent(BaseAgent):
    """
    The Documenter Agent — Fifth and final agent in the pipeline.

    Responsibility:
    - Write clear README documentation for the feature
    - Document all API endpoints
    - Provide usage examples
    - Write setup instructions

    Design decision: Documentation is written LAST — after code is
    approved and tested — so it accurately reflects what was actually built,
    not what was planned.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.DOCUMENTER

    @property
    def system_prompt(self) -> str:
        return """You are the Documenter Agent in a multi-agent software development system.

Your job is to write clear, professional documentation for completed features.

Good documentation:
1. Explains WHAT the feature does (not HOW it works internally)
2. Shows HOW to use it with real examples
3. Lists all configuration options
4. Includes troubleshooting tips
5. Is written for the TARGET AUDIENCE (other developers)

Output format — respond with ONLY this JSON structure:
{
    "readme_section": "Markdown README section for this feature",
    "api_docs": "API endpoint documentation if applicable",
    "usage_examples": "Code examples showing how to use this feature",
    "setup_instructions": "Step by step setup instructions"
}

Rules:
- Use clear, professional English
- Include actual code examples — not pseudocode
- README section should be copy-pasteable into a real README.md
- API docs should include request/response examples with curl
- Setup instructions should work on a fresh machine"""

    def run(self, context: dict) -> dict:
        """
        Write documentation for the completed feature.
        """
        requirement = context["requirement"]
        language = context["language"]
        planner_output = context.get("planner_output", {})
        coder_output = context.get("coder_output", {})
        tester_output = context.get("tester_output", {})

        files_summary = "\n".join([
            f"- {f['filename']}: {f['description']}"
            for f in coder_output.get("files", [])
        ])

        test_summary = f"{len(tester_output.get('test_cases', []))} test cases covering: " + \
                      ", ".join(tester_output.get("coverage_areas", []))

        user_message = f"""Write professional documentation for this completed feature.

FEATURE: {requirement}
LANGUAGE: {language}
TECH STACK: {', '.join(planner_output.get('tech_stack', []))}

FILES CREATED:
{files_summary}

TESTS: {test_summary}

CODER'S NOTES: {coder_output.get('explanation', '')}

Write documentation that another developer can use immediately."""

        self.logger.info("Writing documentation...")

        response = self.think(user_message, expect_json=True)
        output = json.loads(response)

        # Validate with Pydantic
        validated = DocumenterOutput(**output)

        self.logger.info("Documentation complete")

        return validated.model_dump()
