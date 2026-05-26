import logging
from typing import Protocol, runtime_checkable

from src.config import Settings, settings

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, prompt: str, system: str = "") -> str: ...

    async def complete_json(
        self, prompt: str, system: str = "", schema: dict | None = None
    ) -> dict: ...


class Providers:
    """Two-channel dispatcher used by the intelligence layer.

    `sonnet` — high-volume calls (annotation, cluster confirm).
    `opus`   — editorial calls (trend judgment, merge, claim extract).

    Both implement the `LLMProvider` Protocol. In Claude mode they're
    `ClaudeProvider` instances against different models. In fallback
    mode they're the same `OllamaProvider` reused — quality is lower
    but the contract holds.
    """

    def __init__(self, sonnet: LLMProvider, opus: LLMProvider):
        self.sonnet = sonnet
        self.opus = opus


def get_providers(config: Settings = settings) -> Providers:
    """Construct the (sonnet, opus) provider pair from configuration.

    Falls back to Ollama (same provider on both channels) when no
    Anthropic key is set. The fallback is for dev, not production.
    """
    if config.LLM_PROVIDER == "claude" and config.ANTHROPIC_API_KEY:
        from src.llm.claude import ClaudeProvider

        return Providers(
            sonnet=ClaudeProvider(
                api_key=config.ANTHROPIC_API_KEY,
                model=config.CLAUDE_SONNET_MODEL,
                max_concurrency=config.LLM_CONCURRENCY,
            ),
            opus=ClaudeProvider(
                api_key=config.ANTHROPIC_API_KEY,
                model=config.CLAUDE_OPUS_MODEL,
                max_concurrency=max(2, config.LLM_CONCURRENCY // 2),
            ),
        )

    logger.warning(
        "Falling back to Ollama on both channels — no ANTHROPIC_API_KEY set"
    )
    from src.llm.ollama import OllamaProvider

    ollama = OllamaProvider(
        base_url=config.OLLAMA_BASE_URL,
        model=config.OLLAMA_MODEL,
    )
    return Providers(sonnet=ollama, opus=ollama)


def get_llm_provider(config: Settings = settings) -> LLMProvider:
    """Backwards-compat single-provider factory for older call sites."""
    return get_providers(config).sonnet
