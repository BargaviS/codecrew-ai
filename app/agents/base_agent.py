from abc import ABC, abstractmethod
from app.services.llm_client import LLMClient
from app.schemas.models import AgentName
from app.core.logger import get_logger


class BaseAgent(ABC):
    """
    Base class for all CodeCrew agents.

    Every agent has:
    - A name (from AgentName enum)
    - A system prompt defining its role and behaviour
    - Access to the shared LLM client
    - A run() method that takes context and returns output

    Design decision: All agents share the same LLM client (singleton)
    but have different system prompts — specialization through prompting,
    not through different models.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.logger = get_logger(f"codecrew.agent.{self.name.value.lower()}")
        self.logger.info(f"{self.name.value} agent initialized")

    @property
    @abstractmethod
    def name(self) -> AgentName:
        """Each agent must declare its name."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Each agent must define its role and behaviour."""
        pass

    @abstractmethod
    def run(self, context: dict) -> dict:
        """
        Execute the agent's task.

        Args:
            context: Shared context containing all previous agent outputs,
                     session info, and the original requirement.

        Returns:
            dict: Agent's structured output
        """
        pass

    def think(self, user_message: str, expect_json: bool = True) -> str:
        """
        Send a message to the LLM using this agent's system prompt.
        This is the core action every agent takes.
        """
        self.logger.info(f"Thinking... (expect_json={expect_json})")
        return self.llm.chat(
            system_prompt=self.system_prompt,
            user_message=user_message,
            expect_json=expect_json,
        )
