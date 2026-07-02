import json
from app.agents.base_agent import BaseAgent
from app.schemas.models import AgentName, TesterOutput
from app.core.logger import get_logger

logger = get_logger("codecrew.agent.tester")


class TesterAgent(BaseAgent):
    """
    The Tester Agent — Fourth agent in the pipeline.

    Responsibility:
    - Write comprehensive unit tests for the approved code
    - Cover happy paths, edge cases, and error scenarios
    - Think of cases the Coder might have missed

    Design decision: Tester only runs AFTER Reviewer approves.
    No point writing tests for code that will be rewritten.
    """

    @property
    def name(self) -> AgentName:
        return AgentName.TESTER

    @property
    def system_prompt(self) -> str:
        return """You are the Tester Agent in a multi-agent software development system.

Your job is to write comprehensive unit tests for approved code.

Think like a QA engineer who wants to break the code:
1. HAPPY PATH — Normal expected usage
2. EDGE CASES — Empty inputs, boundary values, max/min
3. ERROR CASES — Invalid inputs, exceptions, failures
4. SECURITY CASES — SQL injection, XSS, auth bypass attempts
5. PERFORMANCE CASES — Large inputs, concurrent requests

Output format — respond with ONLY this JSON structure:
{
    "test_file": "test_main.py",
    "test_cases": [
        {
            "test_name": "test_function_name_scenario",
            "description": "What this test verifies",
            "test_code": "Complete test function code"
        }
    ],
    "coverage_areas": ["Area 1 covered", "Area 2 covered"],
    "edge_cases_covered": ["Edge case 1", "Edge case 2"]
}

Rules:
- Test names must be descriptive: test_login_with_wrong_password not test_login2
- Each test must be independent — no shared state between tests
- Use pytest style
- Mock external dependencies (database, APIs)
- Write at least 6 test cases
- Include at least 2 edge cases and 1 error case"""

    def run(self, context: dict) -> dict:
        """
        Write unit tests for the approved code.
        """
        requirement = context["requirement"]
        language = context["language"]
        coder_output = context.get("coder_output", {})
        reviewer_output = context.get("reviewer_output", {})

        files_text = "\n\n".join([
            f"=== {f['filename']} ===\n```{language}\n{f['content']}\n```"
            for f in coder_output.get("files", [])
        ])

        positive_aspects = "\n".join([
            f"- {p}" for p in reviewer_output.get("positive_aspects", [])
        ])

        user_message = f"""Write comprehensive unit tests for this approved code.

REQUIREMENT: {requirement}
LANGUAGE: {language}

APPROVED CODE:
{files_text}

REVIEWER NOTED THESE STRENGTHS:
{positive_aspects}

Write tests that cover happy paths, edge cases, and error scenarios.
Think about what could go wrong and test for it."""

        self.logger.info("Writing unit tests...")

        response = self.think(user_message, expect_json=True)
        output = json.loads(response)

        # Validate with Pydantic
        validated = TesterOutput(**output)

        self.logger.info(
            f"Tests written — {len(validated.test_cases)} test cases, "
            f"coverage={len(validated.coverage_areas)} areas"
        )

        return validated.model_dump()
