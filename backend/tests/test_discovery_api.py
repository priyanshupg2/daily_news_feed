import hashlib
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

from src.db.database import get_db


class TestDiscoveryStatsAPI:
    async def test_stats_empty_db(self, client):
        resp = await client.get("/api/discovery/stats", params={"date": "2026-04-12"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["sources"] == []
        assert data["date"] == "2026-04-12"

    async def test_stats_with_data(self, client, seeded_db):
        resp = await client.get("/api/discovery/stats", params={"date": "2026-04-12"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 15  # 5 arxiv + 5 hn + 5 reddit
        sources_map = {s["source"]: s["count"] for s in data["sources"]}
        assert sources_map["arxiv"] == 5
        assert sources_map["hackernews"] == 5
        assert sources_map["reddit"] == 5

    async def test_stats_different_date_returns_zero(self, client, seeded_db):
        resp = await client.get("/api/discovery/stats", params={"date": "2026-04-11"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestDiscoveryItemsAPI:
    async def test_requires_source_param(self, client, seeded_db):
        resp = await client.get("/api/discovery/items")
        assert resp.status_code == 422

    async def test_returns_items_for_source(self, client, seeded_db):
        resp = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-12"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    async def test_returns_only_lightweight_fields(self, client, seeded_db):
        resp = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-12"})
        item = resp.json()["items"][0]
        assert "id" in item
        assert "title" in item
        assert "published_at" in item
        # Should NOT contain heavy fields
        assert "content" not in item
        assert "metadata" not in item
        assert "authors" not in item

    async def test_pagination(self, client, seeded_db):
        resp1 = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-12", "limit": 2, "offset": 0})
        resp2 = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-12", "limit": 2, "offset": 2})
        items1 = resp1.json()["items"]
        items2 = resp2.json()["items"]
        assert len(items1) == 2
        assert len(items2) == 2
        assert items1[0]["id"] != items2[0]["id"]

    async def test_wrong_date_returns_empty(self, client, seeded_db):
        resp = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-11"})
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []


class TestDiscoveryItemDetailAPI:
    async def test_returns_full_item(self, client, seeded_db):
        # Get an item ID first
        list_resp = await client.get("/api/discovery/items", params={"source": "arxiv", "date": "2026-04-12"})
        item_id = list_resp.json()["items"][0]["id"]

        resp = await client.get(f"/api/discovery/items/{item_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == item_id
        assert "content" in data
        assert "metadata" in data
        assert "authors" in data
        assert "url" in data

    async def test_not_found_returns_404(self, client, test_db):
        resp = await client.get("/api/discovery/items/nonexistent")
        assert resp.status_code == 404


class TestDiscoveryRunAPI:
    async def test_triggers_engine(self, client, test_db):
        with patch("src.api.discovery.DiscoveryEngine") as MockEngine:
            instance = MockEngine.return_value
            instance.run = AsyncMock(return_value=10)

            resp = await client.post("/api/discovery/run")

            assert resp.status_code == 200
            data = resp.json()
            assert data["stored"] == 10
            assert "10" in data["message"]

    async def test_single_source(self, client, test_db):
        with patch("src.api.discovery.DiscoveryEngine") as MockEngine:
            instance = MockEngine.return_value
            instance.run = AsyncMock(return_value=5)

            resp = await client.post("/api/discovery/run", params={"source": "arxiv"})

            assert resp.status_code == 200
            assert resp.json()["stored"] == 5

    async def test_unknown_source_returns_400(self, client, test_db):
        resp = await client.post("/api/discovery/run", params={"source": "unknown"})
        assert resp.status_code == 400
