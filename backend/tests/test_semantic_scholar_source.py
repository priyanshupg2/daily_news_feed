import json
from pathlib import Path

from src.discovery.sources.semantic_scholar import SemanticScholarSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestSemanticScholarParsing:
    def setup_method(self):
        self.source = SemanticScholarSource()
        with open(FIXTURES_DIR / "semantic_scholar_response.json") as f:
            self.data = json.load(f)
        self.papers = self.data.get("data", [])

    def test_parse_paper_produces_item(self):
        assert len(self.papers) > 0
        item = self.source._parse_paper(self.papers[0])
        assert item is not None
        assert item.source == "semanticscholar"

    def test_item_has_required_fields(self):
        item = self.source._parse_paper(self.papers[0])
        assert item.source_id is not None
        assert item.title != ""
        assert item.url is not None
        assert item.fetch_date is not None

    def test_metadata_contains_s2_fields(self):
        item = self.source._parse_paper(self.papers[0])
        assert "paper_id" in item.metadata
        assert "citation_count" in item.metadata
        assert "s2_url" in item.metadata

    def test_id_is_deterministic(self):
        item1 = self.source._parse_paper(self.papers[0])
        item2 = self.source._parse_paper(self.papers[0])
        assert item1.id == item2.id

    def test_paper_without_id_returns_none(self):
        item = self.source._parse_paper({"title": "No ID"})
        assert item is None

    def test_paper_without_title_returns_none(self):
        item = self.source._parse_paper({"paperId": "abc123"})
        assert item is None

    def test_authors_extracted(self):
        item = self.source._parse_paper(self.papers[0])
        # Should have authors as comma-separated string
        if item.authors:
            assert isinstance(item.authors, str)
