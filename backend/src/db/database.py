import os
from contextlib import asynccontextmanager

import aiosqlite

from src.config import settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT,
    title TEXT NOT NULL,
    url TEXT,
    content TEXT,
    authors TEXT,
    published_at DATETIME,
    fetch_date DATE NOT NULL,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE(source, source_id)
);
CREATE INDEX IF NOT EXISTS idx_items_fetch_date ON items(fetch_date);
CREATE INDEX IF NOT EXISTS idx_items_source ON items(source, fetch_date);

CREATE TABLE IF NOT EXISTS item_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id),
    relevance_score REAL,
    quality_score REAL,
    novelty_score REAL,
    importance_score REAL,
    topic_tag TEXT,
    annotated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,
    UNIQUE(item_id)
);
CREATE INDEX IF NOT EXISTS idx_annotations_topic ON item_annotations(topic_tag);

CREATE TABLE IF NOT EXISTS topic_clusters (
    id TEXT PRIMARY KEY,
    topic_label TEXT NOT NULL,
    topic_tag TEXT NOT NULL,
    item_ids TEXT NOT NULL,
    source_count INTEGER,
    feed_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_items (
    id TEXT PRIMARY KEY,
    cluster_id TEXT REFERENCES topic_clusters(id),
    final_rank REAL,
    presentation_mode TEXT NOT NULL DEFAULT 'news',
    summary TEXT NOT NULL,
    why_it_matters TEXT,
    source_links TEXT,
    feed_date DATE NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    time_spent_seconds INTEGER,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feed_date ON feed_items(feed_date);

CREATE TABLE IF NOT EXISTS generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT REFERENCES feed_items(id),
    mode TEXT NOT NULL,
    content TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,
    UNIQUE(feed_item_id, mode)
);

CREATE TABLE IF NOT EXISTS user_profile (
    id TEXT PRIMARY KEY DEFAULT 'default',
    goals TEXT NOT NULL,
    working_topics TEXT,
    learning_topics TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag TEXT NOT NULL UNIQUE,
    interest_weight REAL DEFAULT 0.5,
    proficiency_level TEXT DEFAULT 'beginner',
    articles_read INTEGER DEFAULT 0,
    last_feedback_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag TEXT NOT NULL,
    feed_item_id TEXT REFERENCES feed_items(id),
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id),
    action TEXT NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id),
    field TEXT NOT NULL,
    original_value TEXT,
    user_value TEXT,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    effect TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


@asynccontextmanager
async def get_db():
    """Async context manager that yields an aiosqlite connection."""
    db = await aiosqlite.connect(settings.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        yield db
    finally:
        await db.close()


async def init_db():
    """Create all tables and indexes from the schema."""
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    async with get_db() as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
