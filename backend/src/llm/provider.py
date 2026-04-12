from typing import Protocol, runtime_checkable

from src.config import Settings


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, prompt: str, system: str = "") -> str: ...

    async def complete_json(
        self, prompt: str, system: str = "", schema: dict | None = None
    ) -> dict: ...


def get_llm_provider(config: Settings) -> LLMProvider:
    """Factory that returns the appropriate LLM provider based on config."""
    if config.LLM_PROVIDER == "ollama":
        from src.llm.ollama import OllamaProvider

        return OllamaProvider(
            base_url=config.LLM_BASE_URL,
            model=config.LLM_MODEL,
        )
    elif config.LLM_PROVIDER == "claude":
        raise NotImplementedError("Claude provider not yet implemented")
    elif config.LLM_PROVIDER == "openai":
        raise NotImplementedError("OpenAI provider not yet implemented")
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")
