import json
from pathlib import Path

from src.discovery.sources.hackernews import HackerNewsSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestHNParsing:
    def setup_method(self):
        self.source = HackerNewsSource()
        with open(FIXTURES_DIR / "hn_search_response.json") as f:
            self.search_data = json.load(f)
        with open(FIXTURES_DIR / "hn_frontpage_response.json") as f:
            self.frontpage_data = json.load(f)

    def test_parse_hit_produces_item(self):
        hits = self.search_data.get("hits", [])
        assert len(hits) > 0
        item = self.source._parse_hit(hits[0])
        assert item is not None
        assert item.source == "hackernews"

    def test_item_has_required_fields(self):
        hit = self.search_data["hits"][0]
        item = self.source._parse_hit(hit)
        assert item.source_id is not None
        assert item.title != ""
        assert item.url is not None
        assert item.fetch_date is not None

    def test_metadata_contains_hn_fields(self):
        hit = self.search_data["hits"][0]
        item = self.source._parse_hit(hit)
        assert "hn_id" in item.metadata
        assert "points" in item.metadata
        assert "num_comments" in item.metadata
        assert "hn_url" in item.metadata

    def test_id_is_deterministic(self):
        hit = self.search_data["hits"][0]
        item1 = self.source._parse_hit(hit)
        item2 = self.source._parse_hit(hit)
        assert item1.id == item2.id

    def test_hit_without_title_returns_none(self):
        item = self.source._parse_hit({"objectID": "123"})
        assert item is None

    def test_hit_without_id_returns_none(self):
        item = self.source._parse_hit({"title": "Some Title"})
        assert item is None
