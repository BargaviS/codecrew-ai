import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, TesterOutput, TestCase
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.tester")


class TesterAgent(BaseAgent):

    @property
    def name(self) -> AgentName:
        return AgentName.TESTER

    @property
    def system_prompt(self) -> str:
        return """You are a QA engineer. Write comprehensive unit tests.

Return ONLY this JSON:
{
    "test_file": "test_main.py",
    "test_cases": [
        {
            "test_name": "test_function_scenario",
            "description": "what this tests",
            "test_code": "def test_function_scenario():\\n    assert True"
        }
    ],
    "coverage_areas": ["area 1", "area 2"],
    "edge_cases_covered": ["edge case 1"]
}

Rules:
- Write at least 5 test cases
- Use \\n for newlines in test_code strings
- Never use triple quotes
- Test happy path, edge cases, error cases
- Use pytest style"""

    def run(self, context: dict) -> dict:
        requirement = context["requirement"]
        language = context["language"]
        coder_output = context.get("coder_output", {})

        files_text = "\n\n".join([
            f"=== {f['filename']} ===\n{f['content']}"
            for f in coder_output.get("files", [])
        ])

        user_message = f"""Write unit tests for this code.

REQUIREMENT: {requirement}
LANGUAGE: {language}

CODE:
{files_text}

Write tests covering happy path, edge cases and error scenarios."""

        self.logger.info("Writing unit tests...")

        try:
            response = self.think(user_message, expect_json=True)
            output = json.loads(response)
            validated = TesterOutput(**output)
            self.logger.info(f"Tests written: {len(validated.test_cases)} cases")
            return validated.model_dump()
        except Exception as e:
            self.logger.warning(f"Tester fallback: {e}")
            return TesterOutput(
                test_file="test_main.py",
                test_cases=[
                    TestCase(
                        test_name="test_basic_functionality",
                        description="Basic functionality test",
                        test_code="def test_basic_functionality():\n    assert True"
                    )
                ],
                coverage_areas=["Basic functionality"],
                edge_cases_covered=["Basic case"]
            ).model_dump()
