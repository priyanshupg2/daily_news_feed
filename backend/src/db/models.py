from datetime import date, datetime

from pydantic import BaseModel, Field


class RawItem(BaseModel):
    id: str
    source: str
    source_id: str | None = None
    title: str
    url: str | None = None
    content: str | None = None
    authors: str | None = None
    published_at: datetime | None = None
    fetch_date: date
    metadata: dict | None = None


class ItemAnnotation(BaseModel):
    item_id: str
    relevance_score: float | None = None
    quality_score: float | None = None
    novelty_score: float | None = None
    importance_score: float | None = None
    topic_tag: str | None = None


class TopicCluster(BaseModel):
    id: str
    topic_label: str
    topic_tag: str
    item_ids: list[str]
    source_count: int | None = None
    feed_date: date


class FeedItem(BaseModel):
    id: str
    cluster_id: str | None = None
    final_rank: float | None = None
    presentation_mode: str = "news"
    summary: str
    why_it_matters: str | None = None
    source_links: list[dict] = Field(default_factory=list)
    feed_date: date
    is_read: bool = False


class GeneratedContent(BaseModel):
    feed_item_id: str
    mode: str
    content: str


class UserProfile(BaseModel):
    goals: list[str] = Field(default_factory=list)
    working_topics: list[str] = Field(default_factory=list)
    learning_topics: list[str] = Field(default_factory=list)


class FeedbackItem(BaseModel):
    feed_item_id: str
    action: str
    comment: str | None = None


class FeedbackAnnotation(BaseModel):
    item_id: str
    field: str
    original_value: str | None = None
    user_value: str | None = None
    comment: str | None = None


class UserPrompt(BaseModel):
    prompt: str
