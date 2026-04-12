from pathlib import Path

from src.discovery.sources.arxiv import ArxivSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestArxivParsing:
    def setup_method(self):
        self.source = ArxivSource()
        self.xml = (FIXTURES_DIR / "arxiv_response.xml").read_text()

    def test_parse_produces_items(self):
        items = self.source._parse_atom_feed(self.xml, "cs.LG")
        assert len(items) > 0

    def test_item_has_required_fields(self):
        items = self.source._parse_atom_feed(self.xml, "cs.LG")
        item = items[0]
        assert item.source == "arxiv"
        assert item.source_id is not None
        assert len(item.source_id) > 0
        assert item.title != ""
        assert item.content is not None  # abstract
        assert item.fetch_date is not None

    def test_metadata_contains_arxiv_fields(self):
        items = self.source._parse_atom_feed(self.xml, "cs.LG")
        item = items[0]
        assert "arxiv_id" in item.metadata
        assert "categories" in item.metadata
        assert "primary_category" in item.metadata

    def test_id_is_deterministic(self):
        items1 = self.source._parse_atom_feed(self.xml, "cs.LG")
        items2 = self.source._parse_atom_feed(self.xml, "cs.LG")
        assert items1[0].id == items2[0].id

    def test_malformed_entry_skipped(self):
        """An entry missing the <id> tag should be silently skipped."""
        bad_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>No ID Paper</title>
            <summary>Abstract here</summary>
          </entry>
        </feed>"""
        items = self.source._parse_atom_feed(bad_xml, "cs.LG")
        assert len(items) == 0
