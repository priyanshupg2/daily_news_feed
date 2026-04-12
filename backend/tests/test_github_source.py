import json
from pathlib import Path

from src.discovery.sources.github_trending import GitHubTrendingSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGitHubParsing:
    def setup_method(self):
        self.source = GitHubTrendingSource()
        with open(FIXTURES_DIR / "github_search_response.json") as f:
            self.data = json.load(f)
        self.repos = self.data.get("items", [])

    def test_parse_repo_produces_item(self):
        assert len(self.repos) > 0
        item = self.source._parse_repo(self.repos[0])
        assert item is not None
        assert item.source == "github"

    def test_item_has_required_fields(self):
        item = self.source._parse_repo(self.repos[0])
        assert item.source_id is not None
        assert "/" in item.source_id  # owner/repo
        assert item.title != ""
        assert item.url.startswith("https://github.com/")
        assert item.fetch_date is not None

    def test_metadata_contains_github_fields(self):
        item = self.source._parse_repo(self.repos[0])
        assert "repo" in item.metadata
        assert "stars" in item.metadata
        assert "github_url" in item.metadata

    def test_id_is_deterministic(self):
        item1 = self.source._parse_repo(self.repos[0])
        item2 = self.source._parse_repo(self.repos[0])
        assert item1.id == item2.id

    def test_repo_without_full_name_returns_none(self):
        item = self.source._parse_repo({"description": "no name"})
        assert item is None
