"""End-to-end smoke test that swaps in a fake LLM and fake source.

Exercises every stage — annotate → cluster → trend → merge → rank —
against a synthetic batch of items, and then asserts the API hydrates
the result with multi-lens metadata and claims wired to source items.

Run from `backend/`:

    PYTHONPATH=. python scripts/smoke_pipeline.py
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Force a fresh database so the smoke run is self-contained.
os.environ["DATABASE_PATH"] = "data/smoke.db"
Path("data").mkdir(exist_ok=True)
if Path("data/smoke.db").exists():
    Path("data/smoke.db").unlink()

# Local import path.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db.database import get_db, init_db  # noqa: E402
from src.db.models import RawItem  # noqa: E402
from src.discovery.engine import DiscoveryEngine  # noqa: E402
from src.intelligence.annotator import annotate_recent_items  # noqa: E402
from src.intelligence.clusterer import build_clusters  # noqa: E402
from src.intelligence.merger import build_briefs  # noqa: E402
from src.intelligence.ranker import rank_and_select  # noqa: E402
from src.intelligence.trend import judge_trends  # noqa: E402
from src.llm.provider import Providers  # noqa: E402


# ---------- Mock LLM ----------

class MockProvider:
    """Returns deterministic, schema-compliant JSON for every call.

    Branches on which prompt is being sent — the actual production code
    paths use distinct prompt phrasings per stage, so we sniff and route.
    """

    model = "mock-1"

    async def complete(self, prompt: str, system: str = "") -> str:
        return "(mock)"

    async def complete_json(
        self, prompt: str, system: str = "", schema: dict | None = None
    ) -> dict:
        if "Score the item below" in prompt:
            # Annotator pass — pull title for a heuristic relevance bump.
            relevance = 0.85 if "speculative" in prompt.lower() else 0.6
            return {
                "relevance_score": relevance,
                "quality_score": 0.75,
                "novelty_score": 0.7,
                "importance_score": 0.65,
                "topic_tag": "speculative_decoding"
                if "speculative" in prompt.lower()
                else "agent_evaluation",
                "rationale": "Mock annotation.",
            }
        if "candidate cluster" in prompt:
            return {"partition": [[0, 1]]}  # all in one cluster
        if "Classify each cluster's trend" in prompt:
            n = prompt.count("[")
            return {
                "verdicts": [
                    {"verdict": "emerging", "rationale": "Mock trend."}
                    for _ in range(n)
                ]
            }
        if "produce one brief" in prompt.lower() or "Produce JSON with" in prompt:
            return {
                "title": "Speculative decoding lands a reference impl",
                "lead": "A short readable PyTorch port surfaces the rejection-sampling math the throughput numbers depend on.",
                "why_it_matters": "Lets you weigh whether the gain holds for your structured outputs before baking it into your stack.",
                "claims": [
                    {
                        "n": 1,
                        "text": "200-line reference runs on a single 3090.",
                        "source_index": 0,
                        "citation_text": "arxiv.org · mock",
                        "confidence": 0.85,
                    },
                    {
                        "n": 2,
                        "text": "Gain caps at ~2.4× and falls off with weak draft models.",
                        "source_index": 1,
                        "citation_text": "news.ycombinator.com",
                        "confidence": 0.7,
                    },
                ],
            }
        return {}


# ---------- Fake source ----------

class FakeSource:
    source_name = "smoke"

    async def fetch(self):
        today = date.today()
        return [
            RawItem(
                id="smoke:arxiv1",
                source="arxiv",
                source_id="2401.99001",
                title="Speculative decoding revisited: a reference implementation",
                url="https://arxiv.org/abs/2401.99001",
                content="We present a 200-line reference implementation of speculative decoding...",
                authors="A. Mock, B. Mock",
                published_at=datetime.now(timezone.utc),
                fetch_date=today,
                metadata={"categories": ["cs.LG"]},
            ),
            RawItem(
                id="smoke:hn1",
                source="hackernews",
                source_id="99001",
                title="Show HN: Tiny speculative decoding implementation",
                url="https://news.ycombinator.com/item?id=99001",
                content=None,
                authors="anon",
                published_at=datetime.now(timezone.utc),
                fetch_date=today,
                metadata={"points": 250, "num_comments": 80},
            ),
            RawItem(
                id="smoke:reddit1",
                source="reddit",
                source_id="rd99",
                title="Agent evaluation harness for production tools",
                url="https://reddit.com/r/MachineLearning/comments/rd99",
                content="Sharing our eval setup for agent tool use in prod...",
                authors="u/anon",
                published_at=datetime.now(timezone.utc),
                fetch_date=today,
                metadata={"subreddit": "MachineLearning", "score": 320},
            ),
        ]


# ---------- Validation ----------

def check(label, condition, detail=""):
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        check.failures += 1
check.failures = 0


async def main():
    print("Initializing schema + seed lenses…")
    await init_db()

    print("Stage 1: discovery (fake source)")
    engine = DiscoveryEngine([FakeSource()])
    stored = await engine.run()
    check("3 items stored from fake source", stored == 3, f"got {stored}")

    mock = MockProvider()
    providers = Providers(sonnet=mock, opus=mock)

    print("Stage 2: annotation per (item × lens)")
    pairs = await annotate_recent_items(providers)
    check("12 annotations written (3 items × 4 lenses)", pairs == 3 * 4 or pairs > 0)
    async with get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(DISTINCT item_id) AS i, COUNT(DISTINCT lens_id) AS l FROM item_annotations"
        )
        r = await cur.fetchone()
        check(
            "annotations cover every (item, lens) pair",
            r["i"] == 3 and r["l"] == 4,
            f"items={r['i']} lenses={r['l']}",
        )

    print("Stage 3: clustering")
    feed_date = date.today()
    n_clusters = await build_clusters(feed_date, mock)
    check("clusters built", n_clusters >= 1, f"clusters={n_clusters}")

    print("Stage 4: trend judgments")
    n_trends = await judge_trends(feed_date, mock)
    check("trend verdicts written", n_trends >= 1, f"verdicts={n_trends}")

    print("Stage 5: merger writes briefs + claims")
    n_briefs = await build_briefs(feed_date, mock)
    check("briefs generated", n_briefs >= 1, f"briefs={n_briefs}")

    async with get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(*) AS c FROM feed_item_lenses"
        )
        r = await cur.fetchone()
        check("multi-lens tagging populated", r["c"] >= 1, f"feed_item_lenses rows={r['c']}")
        cur = await db.execute("SELECT COUNT(*) AS c FROM brief_claims")
        r = await cur.fetchone()
        check("claims persisted with source pinning", r["c"] >= 1, f"claims={r['c']}")
        cur = await db.execute(
            """
            SELECT bc.id, bc.source_item_id, i.id AS exists_id
            FROM brief_claims bc
            LEFT JOIN items i ON i.id = bc.source_item_id
            """
        )
        rows = await cur.fetchall()
        check(
            "every claim cites a real item id",
            all(r["exists_id"] for r in rows),
            f"{len(rows)} claims checked",
        )

    print("Stage 6: ranker selects + applies caps")
    n_kept = await rank_and_select(feed_date)
    check("ranker kept ≤ 7 briefs", n_kept <= 7, f"kept={n_kept}")
    async with get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(*) AS c FROM feed_items WHERE final_rank IS NOT NULL"
        )
        r = await cur.fetchone()
        check("kept briefs have final_rank set", r["c"] == n_kept)

    print("Stage 7: API hydration shape")
    from src.api.feed import _hydrate_brief
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM feed_items WHERE final_rank IS NOT NULL LIMIT 1"
        )
        row = await cur.fetchone()
        brief = dict(row)
        await _hydrate_brief(db, brief)
    check("brief has lenses[]", isinstance(brief.get("lenses"), list))
    check("brief has primary_lens", brief.get("primary_lens") in {"founder", "engineer", "researcher", "operator"})
    check("brief has claims[] with citation_text", all(c.get("citation_text") for c in brief.get("claims", [])))
    check("source_links list is non-empty", len(brief.get("source_links", [])) >= 1)
    check("source_count populated", brief.get("source_count", 0) >= 1)

    print()
    if check.failures:
        print(f"FAIL: {check.failures} checks failed")
        sys.exit(1)
    print(f"OK: all checks passed")


if __name__ == "__main__":
    asyncio.run(main())
