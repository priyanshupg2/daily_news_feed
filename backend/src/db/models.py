from datetime import date, datetime
from typing import Literal

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


class Lens(BaseModel):
    id: str
    name: str
    accent_token: str
    thesis: str | None = None
    working_topics: list[str] = Field(default_factory=list)
    learning_topics: list[str] = Field(default_factory=list)
    active: bool = True
    sort_order: int = 0


class ItemAnnotation(BaseModel):
    item_id: str
    lens_id: str
    relevance_score: float | None = None
    quality_score: float | None = None
    novelty_score: float | None = None
    importance_score: float | None = None
    topic_tag: str | None = None
    rationale: str | None = None
    llm_model: str | None = None


class TopicCluster(BaseModel):
    id: str
    topic_label: str
    topic_tag: str
    item_ids: list[str]
    source_count: int | None = None
    feed_date: date


class TrendJudgment(BaseModel):
    feed_date: date
    cluster_id: str
    topic_tag: str
    verdict: Literal["emerging", "sustained", "fading", "noise"]
    rationale: str | None = None


class BriefClaim(BaseModel):
    n: int
    text: str
    source_item_id: str | None = None
    citation_text: str | None = None
    confidence: float | None = None


class FeedItem(BaseModel):
    id: str
    cluster_id: str | None = None
    final_rank: float | None = None
    presentation_mode: str = "news"
    framing: Literal["item_anchored", "synthesis"] | None = None
    title: str | None = None
    lead: str | None = None
    summary: str
    why_it_matters: str | None = None
    source_links: list[dict] = Field(default_factory=list)
    feed_date: date
    is_read: bool = False
    lenses: list[str] = Field(default_factory=list)
    primary_lens: str | None = None
    claims: list[BriefClaim] = Field(default_factory=list)


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
    lens_id: str | None = None
    field: str
    original_value: str | None = None
    user_value: str | None = None
    comment: str | None = None


class UserPrompt(BaseModel):
    prompt: str
    lens_id: str | None = None
