import json
import re
from groq import Groq
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("codecrew.llm")


class LLMClient:
    def __init__(self):
        settings = get_settings()
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set in .env file")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        logger.info(f"LLM client ready — model={self.model}")

    def chat(self, system_prompt: str, user_message: str, expect_json: bool = False) -> str:
        if expect_json:
            system_prompt += (
                "\n\nCRITICAL JSON RULES:"
                "\n1. Respond with ONLY valid JSON — no markdown, no backticks"
                "\n2. NEVER use triple quotes (\"\"\" or ''') inside JSON strings"
                "\n3. Use single line comments (#) instead of docstrings"
                "\n4. Escape all special characters in strings"
                "\n5. The response must be parseable by json.loads()"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        logger.info(f"LLM call — expect_json={expect_json}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        content = response.choices[0].message.content.strip()

        if expect_json:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]).strip()

            # Try to parse — if fails, attempt cleanup
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed, attempting cleanup: {e}")
                # Remove triple quotes
                content = content.replace('"""', '"')
                content = content.replace("'''", "'")
                try:
                    json.loads(content)
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON cleanup failed: {e2}")
                    raise ValueError(f"LLM returned invalid JSON: {e2}\nContent: {content[:300]}")

        return content


from functools import lru_cache

@lru_cache()
def get_llm_client() -> LLMClient:
    return LLMClient()
