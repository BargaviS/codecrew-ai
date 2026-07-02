import json
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
                "\n\nCRITICAL: Return ONLY a valid JSON object."
                "\nDo NOT write any code or text outside the JSON."
                "\nDo NOT use triple quotes inside JSON."
                "\nUse \\n for newlines in code strings."
                "\nThe entire response must start with { and end with }"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Try up to 3 times
        for attempt in range(3):
            logger.info(f"LLM call attempt {attempt+1}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content.strip()

            if not expect_json:
                return content

            # Clean up common issues
            # Remove markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Remove any text before first {
            if "{" in content:
                content = content[content.index("{"):]

            # Remove any text after last }
            if "}" in content:
                content = content[:content.rindex("}")+1]

            try:
                json.loads(content)
                return content
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt+1} JSON failed: {e}")
                if attempt < 2:
                    # Ask again with stronger instruction
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Your response was not valid JSON. Return ONLY the JSON object starting with { and ending with }. No other text."})
                    continue
                raise ValueError(f"LLM failed to return valid JSON after 3 attempts: {e}")

        return content


from functools import lru_cache

@lru_cache()
def get_llm_client() -> LLMClient:
    return LLMClient()
