import json
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.db.database import init_db, get_db
from src.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest_asyncio.fixture
async def test_db(tmp_path):
    """Point DATABASE_PATH to a temp file and init schema."""
    settings.DATABASE_PATH = str(tmp_path / "test.db")
    await init_db()
    yield


@pytest_asyncio.fixture
async def client(test_db):
    """Async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _make_item(source: str, source_id: str, title: str, fetch_date: str = "2026-04-12"):
    """Helper to build an item tuple for DB insertion."""
    item_id = hashlib.sha256(f"{source}:{source_id}".encode()).hexdigest()[:16]
    return (
        item_id,
        source,
        source_id,
        title,
        f"https://example.com/{source_id}",
        f"Content for {title}",
        "Test Author",
        datetime(2026, 4, 12, 8, 0, 0, tzinfo=timezone.utc).isoformat(),
        fetch_date,
        json.dumps({"test": True}),
    )


@pytest_asyncio.fixture
async def seeded_db(test_db):
    """DB pre-loaded with 5 arxiv + 5 hn + 5 reddit items for 2026-04-12."""
    items = []
    for i in range(5):
        items.append(_make_item("arxiv", f"arxiv_{i}", f"arXiv Paper {i}"))
        items.append(_make_item("hackernews", f"hn_{i}", f"HN Story {i}"))
        items.append(_make_item("reddit", f"reddit_{i}", f"Reddit Post {i}"))

    async with get_db() as db:
        await db.executemany(
            """INSERT INTO items (id, source, source_id, title, url, content, authors, published_at, fetch_date, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            items,
        )
        await db.commit()
    yield
