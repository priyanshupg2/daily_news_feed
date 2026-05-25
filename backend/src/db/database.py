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

CREATE TABLE IF NOT EXISTS lenses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    accent_token TEXT NOT NULL,
    thesis TEXT,
    working_topics TEXT,
    learning_topics TEXT,
    active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS item_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id),
    lens_id TEXT REFERENCES lenses(id),
    relevance_score REAL,
    quality_score REAL,
    novelty_score REAL,
    importance_score REAL,
    topic_tag TEXT,
    rationale TEXT,
    annotated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,
    UNIQUE(item_id, lens_id)
);
CREATE INDEX IF NOT EXISTS idx_annotations_topic ON item_annotations(topic_tag);
CREATE INDEX IF NOT EXISTS idx_annotations_lens ON item_annotations(lens_id, relevance_score);

CREATE TABLE IF NOT EXISTS topic_clusters (
    id TEXT PRIMARY KEY,
    topic_label TEXT NOT NULL,
    topic_tag TEXT NOT NULL,
    item_ids TEXT NOT NULL,
    source_count INTEGER,
    feed_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clusters_date ON topic_clusters(feed_date);

CREATE TABLE IF NOT EXISTS trend_judgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_date DATE NOT NULL,
    cluster_id TEXT REFERENCES topic_clusters(id),
    topic_tag TEXT NOT NULL,
    verdict TEXT NOT NULL,
    rationale TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_date, cluster_id)
);
CREATE INDEX IF NOT EXISTS idx_trends_date_verdict ON trend_judgments(feed_date, verdict);

CREATE TABLE IF NOT EXISTS feed_items (
    id TEXT PRIMARY KEY,
    cluster_id TEXT REFERENCES topic_clusters(id),
    final_rank REAL,
    presentation_mode TEXT NOT NULL DEFAULT 'news',
    framing TEXT,
    title TEXT,
    lead TEXT,
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

CREATE TABLE IF NOT EXISTS feed_item_lenses (
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id) ON DELETE CASCADE,
    lens_id TEXT NOT NULL REFERENCES lenses(id),
    relevance_score REAL NOT NULL,
    PRIMARY KEY (feed_item_id, lens_id)
);
CREATE INDEX IF NOT EXISTS idx_feed_lens ON feed_item_lenses(lens_id);

CREATE TABLE IF NOT EXISTS brief_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id) ON DELETE CASCADE,
    n INTEGER NOT NULL,
    text TEXT NOT NULL,
    source_item_id TEXT REFERENCES items(id),
    citation_text TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_item_id, n)
);

CREATE TABLE IF NOT EXISTS brief_claim_corroborations (
    claim_id INTEGER NOT NULL REFERENCES brief_claims(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES items(id),
    PRIMARY KEY (claim_id, item_id)
);

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
    topic_tag TEXT NOT NULL,
    lens_id TEXT REFERENCES lenses(id),
    interest_weight REAL DEFAULT 0.5,
    proficiency_level TEXT DEFAULT 'beginner',
    articles_read INTEGER DEFAULT 0,
    last_feedback_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(topic_tag, lens_id)
);

CREATE TABLE IF NOT EXISTS knowledge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag TEXT NOT NULL,
    lens_id TEXT REFERENCES lenses(id),
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
    lens_id TEXT REFERENCES lenses(id),
    field TEXT NOT NULL,
    original_value TEXT,
    user_value TEXT,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    lens_id TEXT REFERENCES lenses(id),
    processed BOOLEAN DEFAULT FALSE,
    effect TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS muted_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    lens_id TEXT REFERENCES lenses(id),
    reason TEXT,
    muted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_muted_recent ON muted_sources(muted_at);

CREATE TABLE IF NOT EXISTS voice_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT REFERENCES feed_items(id),
    field TEXT NOT NULL,
    violation TEXT NOT NULL,
    text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


# The four lenses ship as defaults. Theses are template stubs the user
# edits — they're explicitly first-person and a little stilted so the
# user feels the seam and writes their own.
SEED_LENSES = [
    {
        "id": "founder",
        "name": "Founder",
        "accent_token": "lens-founder",
        "thesis": "I'm building something that needs to find paying users. Market shape, GTM signal, and what other founders are learning matter more than the underlying tech.",
        "working_topics": ["distribution", "pricing", "fundraising", "product_market_fit"],
        "learning_topics": ["b2b_sales", "indie_hacker_playbooks", "growth_loops"],
        "sort_order": 0,
    },
    {
        "id": "engineer",
        "name": "Engineer",
        "accent_token": "lens-engineer",
        "thesis": "I ship systems. I want what works in production — reference implementations, benchmarks against real workloads, libraries with traction, gotchas other engineers hit.",
        "working_topics": ["inference", "agents", "evals", "tooling"],
        "learning_topics": ["cuda", "compilers", "distributed_systems"],
        "sort_order": 1,
    },
    {
        "id": "researcher",
        "name": "Researcher",
        "accent_token": "lens-researcher",
        "thesis": "I'm trying to understand what's true about how these systems work. I want methods, mechanism, ablations, and disagreement between groups — not press releases.",
        "working_topics": ["interpretability", "scaling_laws", "reasoning"],
        "learning_topics": ["mechanistic_interp", "rlhf", "agent_theory"],
        "sort_order": 2,
    },
    {
        "id": "operator",
        "name": "Operator",
        "accent_token": "lens-operator",
        "thesis": "I'm running a team or a system that has to keep working. I want what's failing, what's getting cheaper, what's getting faster, and what the next 90 days will demand of my org.",
        "working_topics": ["cost", "reliability", "team_workflows", "vendor_landscape"],
        "learning_topics": ["incident_response", "evals_in_prod", "compliance"],
        "sort_order": 3,
    },
]


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
    """Create all tables, indexes, and seed the four default lenses."""
    import json

    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    async with get_db() as db:
        await db.executescript(SCHEMA_SQL)
        for lens in SEED_LENSES:
            await db.execute(
                """
                INSERT OR IGNORE INTO lenses
                  (id, name, accent_token, thesis, working_topics,
                   learning_topics, active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    lens["id"],
                    lens["name"],
                    lens["accent_token"],
                    lens["thesis"],
                    json.dumps(lens["working_topics"]),
                    json.dumps(lens["learning_topics"]),
                    lens["sort_order"],
                ),
            )
        await db.commit()
