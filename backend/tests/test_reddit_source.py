import json
from pathlib import Path

from src.discovery.sources.reddit import RedditSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestRedditParsing:
    def setup_method(self):
        self.source = RedditSource()
        with open(FIXTURES_DIR / "reddit_response.json") as f:
            data = json.load(f)
        self.posts = [child["data"] for child in data.get("data", {}).get("children", [])]

    def test_parse_post_produces_item(self):
        assert len(self.posts) > 0
        item = self.source._parse_post(self.posts[0], "MachineLearning")
        # May be None if stickied, so find a non-stickied one
        for post in self.posts:
            item = self.source._parse_post(post, "MachineLearning")
            if item is not None:
                break
        assert item is not None
        assert item.source == "reddit"

    def test_item_has_required_fields(self):
        for post in self.posts:
            item = self.source._parse_post(post, "MachineLearning")
            if item is not None:
                assert item.source_id is not None
                assert item.title != ""
                assert item.fetch_date is not None
                break

    def test_metadata_contains_reddit_fields(self):
        for post in self.posts:
            item = self.source._parse_post(post, "MachineLearning")
            if item is not None:
                assert "reddit_id" in item.metadata
                assert "subreddit" in item.metadata
                assert "score" in item.metadata
                assert "num_comments" in item.metadata
                break

    def test_stickied_posts_excluded(self):
        stickied_post = {"id": "stk1", "title": "Rules", "stickied": True}
        item = self.source._parse_post(stickied_post, "MachineLearning")
        assert item is None

    def test_post_without_id_returns_none(self):
        item = self.source._parse_post({"title": "No ID"}, "MachineLearning")
        assert item is None

    def test_post_without_title_returns_none(self):
        item = self.source._parse_post({"id": "abc"}, "MachineLearning")
        assert item is None

    def test_selftext_truncation(self):
        long_post = {
            "id": "long1",
            "title": "Long Post",
            "selftext": "x" * 3000,
            "is_self": True,
            "permalink": "/r/test/comments/long1/long_post/",
        }
        item = self.source._parse_post(long_post, "MachineLearning")
        assert item is not None
        assert len(item.content) <= 2003 + 1  # 2000 + "..."

    def test_self_post_uses_permalink(self):
        self_post = {
            "id": "self1",
            "title": "Self Post",
            "url": "https://www.reddit.com/r/test/comments/self1/self_post/",
            "selftext": "Body text",
            "is_self": True,
            "permalink": "/r/test/comments/self1/self_post/",
        }
        item = self.source._parse_post(self_post, "MachineLearning")
        assert item is not None
        assert "reddit.com" in item.url

    def test_link_post_uses_external_url(self):
        link_post = {
            "id": "link1",
            "title": "Link Post",
            "url": "https://arxiv.org/abs/2401.12345",
            "is_self": False,
            "permalink": "/r/test/comments/link1/link_post/",
        }
        item = self.source._parse_post(link_post, "MachineLearning")
        assert item is not None
        assert "arxiv.org" in item.url

    def test_id_is_deterministic(self):
        for post in self.posts:
            item1 = self.source._parse_post(post, "MachineLearning")
            item2 = self.source._parse_post(post, "MachineLearning")
            if item1 is not None:
                assert item1.id == item2.id
                break
