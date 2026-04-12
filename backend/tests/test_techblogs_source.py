from pathlib import Path

import feedparser

from src.discovery.sources.tech_blogs import TechBlogsSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTechBlogsParsing:
    def setup_method(self):
        self.source = TechBlogsSource()
        rss_text = (FIXTURES_DIR / "rss_feed.xml").read_text()
        self.feed = feedparser.parse(rss_text)

    def test_parse_entry_produces_item(self):
        assert len(self.feed.entries) > 0
        item = self.source._parse_entry(self.feed.entries[0], "Test Blog")
        assert item is not None
        assert item.source == "techblogs"

    def test_item_has_required_fields(self):
        item = self.source._parse_entry(self.feed.entries[0], "Test Blog")
        assert item.source_id is not None
        assert item.title != ""
        assert item.fetch_date is not None

    def test_metadata_contains_blog_name(self):
        item = self.source._parse_entry(self.feed.entries[0], "Hugging Face Blog")
        assert item.metadata["blog"] == "Hugging Face Blog"

    def test_id_is_deterministic(self):
        entry = self.feed.entries[0]
        item1 = self.source._parse_entry(entry, "Test")
        item2 = self.source._parse_entry(entry, "Test")
        assert item1.id == item2.id

    def test_entry_without_title_returns_none(self):
        class FakeEntry:
            pass
        entry = FakeEntry()
        item = self.source._parse_entry(entry, "Test")
        assert item is None

    def test_content_truncation(self):
        class FakeEntry:
            title = "Long Content"
            link = "https://example.com/post"
            id = "long-1"
            summary = "x" * 3000
        item = self.source._parse_entry(FakeEntry(), "Test")
        assert item is not None
        assert len(item.content) <= 2003 + 1
