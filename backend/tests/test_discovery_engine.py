import hashlib
from datetime import date, datetime, timezone

from src.db.database import get_db
from src.db.models import RawItem
from src.discovery.engine import DiscoveryEngine


def _make_raw_item(source_id: str = "test_1", source: str = "test") -> RawItem:
    item_id = hashlib.sha256(f"{source}:{source_id}".encode()).hexdigest()[:16]
    return RawItem(
        id=item_id,
        source=source,
        source_id=source_id,
        title=f"Test Item {source_id}",
        url=f"https://example.com/{source_id}",
        content="Test content",
        authors="Author",
        published_at=datetime(2026, 4, 12, 8, 0, 0, tzinfo=timezone.utc),
        fetch_date=date(2026, 4, 12),
    )


class MockSource:
    source_name = "mock"

    def __init__(self, items: list[RawItem]):
        self._items = items

    async def fetch(self) -> list[RawItem]:
        return self._items


class FailingSource:
    source_name = "failing"

    async def fetch(self) -> list[RawItem]:
        raise RuntimeError("Source failed")


class TestDiscoveryEngine:
    async def test_stores_items(self, test_db):
        items = [_make_raw_item("a"), _make_raw_item("b")]
        engine = DiscoveryEngine(sources=[MockSource(items)])

        stored = await engine.run()

        assert stored == 2
        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) FROM items")
            row = await cursor.fetchone()
            assert row[0] == 2

    async def test_dedup_on_rerun(self, test_db):
        items = [_make_raw_item("dup_1")]
        engine = DiscoveryEngine(sources=[MockSource(items)])

        first = await engine.run()
        second = await engine.run()

        assert first == 1
        assert second == 0

        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) FROM items")
            row = await cursor.fetchone()
            assert row[0] == 1

    async def test_source_failure_doesnt_block_others(self, test_db):
        good = MockSource([_make_raw_item("good_1")])
        bad = FailingSource()
        engine = DiscoveryEngine(sources=[bad, good])

        stored = await engine.run()

        assert stored == 1

    async def test_empty_sources(self, test_db):
        engine = DiscoveryEngine(sources=[MockSource([])])

        stored = await engine.run()

        assert stored == 0

    async def test_multiple_sources(self, test_db):
        src1 = MockSource([_make_raw_item("s1_a", "source1")])
        src2 = MockSource([_make_raw_item("s2_a", "source2")])
        engine = DiscoveryEngine(sources=[src1, src2])

        stored = await engine.run()

        assert stored == 2
