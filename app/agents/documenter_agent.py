import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, DocumenterOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.documenter")


class DocumenterAgent(BaseAgent):

    @property
    def name(self) -> AgentName:
        return AgentName.DOCUMENTER

    @property
    def system_prompt(self) -> str:
        return """You are a technical writer. Write clear documentation.

Return ONLY this JSON object. No other text:
{
    "readme_section": "## Feature Name\\n\\nDescription here",
    "api_docs": "## API\\n\\nEndpoint docs here",
    "usage_examples": "## Usage\\n\\n```python\\ncode here\\n```",
    "setup_instructions": "## Setup\\n\\n1. Install\\n2. Run"
}

Rules:
- Use \\n for newlines inside JSON strings
- Never use triple quotes
- Keep content concise and clear
- Return valid JSON only"""

    def run(self, context: dict) -> dict:
        requirement = context["requirement"]
        language = context["language"]
        coder_output = context.get("coder_output", {})

        files_summary = "\n".join([
            f"- {f['filename']}: {f['description']}"
            for f in coder_output.get("files", [])
        ])

        user_message = f"""Write documentation for this feature.

FEATURE: {requirement}
LANGUAGE: {language}
FILES: {files_summary}

Return JSON with readme_section, api_docs, usage_examples, setup_instructions."""

        self.logger.info("Writing documentation...")

        try:
            response = self.think(user_message, expect_json=True)
            output = json.loads(response)
            validated = DocumenterOutput(**output)
            self.logger.info("Documentation complete")
            return validated.model_dump()
        except Exception as e:
            # Fallback documentation if LLM fails
            logger.warning(f"Documenter LLM failed, using fallback: {e}")
            return DocumenterOutput(
                readme_section=f"## {requirement}\n\nThis feature implements {requirement} in {language}.",
                api_docs="## API\n\nSee code files for endpoint details.",
                usage_examples=f"## Usage\n\nRun the application and use the provided endpoints.",
                setup_instructions=f"## Setup\n\n1. Install dependencies\n2. Run the application"
            ).model_dump()
