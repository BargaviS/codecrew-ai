from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CodeCrew AI"
    ENV: str = "development"

    # Groq LLM
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1

    # Agent behaviour
    MAX_REVIEW_ITERATIONS: int = 3

    # Storage paths
    SESSION_DIR: str = "data/sessions"
    CODEBASE_DIR: str = "data/codebase"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings — loaded once, reused everywhere."""
    return Settings()
