from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: str = "claude"  # claude | ollama | openai

    # Claude — primary path.
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_SONNET_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_OPUS_MODEL: str = "claude-opus-4-7"

    # Ollama — dev fallback when ANTHROPIC_API_KEY is empty.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Older fields kept so existing call sites don't break.
    LLM_MODEL: str = "llama3.2"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_API_KEY: str = ""

    DATABASE_PATH: str = "data/news_feed.db"
    FEED_DAILY_CAP: int = 7
    FEED_PER_LENS_CAP: int = 4
    RELEVANCE_THRESHOLD: float = 0.5
    LLM_CONCURRENCY: int = 8

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
