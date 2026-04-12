from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: str = "ollama"  # ollama | claude | openai
    LLM_MODEL: str = "llama3.2"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_API_KEY: str = ""  # for claude/openai
    DATABASE_PATH: str = "data/news_feed.db"
    FEED_ITEMS_PER_DAY: int = 5
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
