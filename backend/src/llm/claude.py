import asyncio
import json
import logging

import anthropic

logger = logging.getLogger(__name__)


# Prism's voice block is the highest-leverage cached prefix in the system.
# Every prompt that produces user-visible text gets this prepended.
VOICE_BLOCK = """Write in Prism's voice: editorial, precise, slightly dry, never breathless.
Direct address — "you", never "we" or "users". Verbs do the work: reads,
extracts, verifies, tunes, mutes. No hype adjectives — revolutionary,
game-changing, seamless, AI-powered, intelligent. Sentence case. Em-dashes
to set off clauses. No emoji, no unicode pictograms.

Vocabulary: lens, brief, signal, noise, source, claim, thesis.
Never: channel, feed, digest, newsletter, summary (as a noun for a brief),
hits, citation (as a verb), interests.

Length: lead ≤ 280 chars, why_it_matters ≤ 320 chars, each claim ≤ 200 chars.
"""


class ClaudeProvider:
    """Anthropic API provider, single-model.

    Two instances are typically wired up — one for Sonnet 4.6 (bulk
    annotation, cluster confirm) and one for Opus 4.7 (editorial merge,
    trend judgment).

    Honors the same `complete` / `complete_json` contract as
    `OllamaProvider` so the rest of the pipeline doesn't care which
    backend is active.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_concurrency: int = 8,
        include_voice_block: bool = True,
    ):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.include_voice_block = include_voice_block

    def _build_system(self, system: str) -> list[dict] | None:
        """Compose the cached voice block + caller-provided system text.

        Returns the multi-block list the API expects when cache_control
        is set per block. Returns None if there's nothing to send.
        """
        blocks: list[dict] = []
        if self.include_voice_block:
            blocks.append(
                {
                    "type": "text",
                    "text": VOICE_BLOCK,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        if system:
            # Cache the caller's system too — for the annotator and
            # clusterer this is the lens definitions block, stable
            # across every call in a batch.
            blocks.append(
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        return blocks or None

    async def complete(self, prompt: str, system: str = "") -> str:
        """Plain text completion. No structured-output guarantee."""
        system_blocks = self._build_system(system)
        async with self.semaphore:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_blocks if system_blocks else anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": prompt}],
            )
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    async def complete_json(
        self,
        prompt: str,
        system: str = "",
        schema: dict | None = None,
    ) -> dict:
        """JSON completion. Uses `output_config.format` for schema-bound
        outputs when a schema is supplied; falls back to a prompt-engineered
        JSON request otherwise.
        """
        system_blocks = self._build_system(system)

        kwargs: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_blocks:
            kwargs["system"] = system_blocks

        if schema is not None:
            kwargs["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            }

        async with self.semaphore:
            response = await self.client.messages.create(**kwargs)

        text = next(
            (b.text for b in response.content if b.type == "text"),
            "",
        )
        if not text:
            logger.warning("Empty text response from Claude")
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.exception("Claude returned non-JSON text: %s", text[:200])
            # Strip a fenced code block if the model wrapped it.
            stripped = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return {}


class Providers:
    """Two-channel dispatcher: Sonnet for bulk, Opus for editorial."""

    def __init__(self, sonnet: "ClaudeProvider | object", opus: "ClaudeProvider | object"):
        self.sonnet = sonnet
        self.opus = opus
