import json
import logging
import uuid
from datetime import date

from src.config import settings
from src.db.database import get_db
from src.intelligence.lenses import lens_context_block, load_active_lenses
from src.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "lead": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "minimum": 1},
                    "text": {"type": "string"},
                    "source_index": {"type": "integer", "minimum": 0},
                    "citation_text": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["n", "text", "source_index", "citation_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "lead", "why_it_matters", "claims"],
    "additionalProperties": False,
}


def _choose_framing(cluster_items: list[dict], trend_verdict: str | None) -> str:
    """Heuristic: pick item_anchored vs synthesis based on cluster shape."""
    if len(cluster_items) <= 1:
        return "item_anchored"

    sources = {it["source"] for it in cluster_items}
    if len(cluster_items) >= 3 and len(sources) >= 2:
        if trend_verdict in {"emerging", "sustained"}:
            return "synthesis"

    # Dominance check — one item far above the rest in relevance.
    scores = sorted(
        (it.get("best_relevance") or 0 for it in cluster_items),
        reverse=True,
    )
    if len(scores) >= 2 and scores[0] >= scores[1] + 0.3:
        return "item_anchored"

    if len(cluster_items) >= 3 and len(sources) >= 2:
        return "synthesis"
    return "item_anchored"


def _build_citation(item: dict) -> str:
    """Compact human-readable citation for the claim chip."""
    src = item.get("source") or "source"
    if src == "arxiv":
        meta = item.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        sid = (item.get("source_id") or "").split("v")[0]
        return f"arxiv.org · {sid}"
    if src == "hackernews":
        return "news.ycombinator.com"
    if src == "reddit":
        meta = item.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        sub = meta.get("subreddit") if isinstance(meta, dict) else None
        return f"reddit.com · r/{sub}" if sub else "reddit.com"
    if item.get("url"):
        from urllib.parse import urlparse
        try:
            return urlparse(item["url"]).netloc.removeprefix("www.")
        except Exception:
            pass
    return src


async def build_briefs(feed_date: date, provider: LLMProvider) -> int:
    """For each cluster, produce one multi-lens brief (if it clears the
    relevance bar for any active lens) and persist it with its claims."""
    lenses = await load_active_lenses()
    if not lenses:
        return 0
    lens_by_id = {l.id: l for l in lenses}

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM topic_clusters WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        clusters = [dict(r) for r in await cursor.fetchall()]
        cursor = await db.execute(
            "SELECT cluster_id, verdict, rationale FROM trend_judgments "
            "WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        trends = {r["cluster_id"]: dict(r) for r in await cursor.fetchall()}

        # Clear today's briefs (idempotent re-run).
        cursor = await db.execute(
            "SELECT id FROM feed_items WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        old_ids = [r["id"] for r in await cursor.fetchall()]
        for old in old_ids:
            await db.execute(
                "DELETE FROM feed_item_lenses WHERE feed_item_id = ?", (old,)
            )
            await db.execute(
                "DELETE FROM brief_claims WHERE feed_item_id = ?", (old,)
            )
        await db.execute(
            "DELETE FROM feed_items WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        await db.commit()

    written = 0
    for cluster in clusters:
        verdict = trends.get(cluster["id"], {}).get("verdict")
        if verdict == "noise":
            continue

        item_ids = json.loads(cluster["item_ids"])
        if not item_ids:
            continue

        # Pull each item plus its best per-lens relevance scores.
        async with get_db() as db:
            placeholders = ",".join(["?"] * len(item_ids))
            cursor = await db.execute(
                f"SELECT * FROM items WHERE id IN ({placeholders})",
                tuple(item_ids),
            )
            items = [dict(r) for r in await cursor.fetchall()]
            cursor = await db.execute(
                f"""
                SELECT item_id, lens_id, relevance_score, importance_score,
                       novelty_score, quality_score
                FROM item_annotations
                WHERE item_id IN ({placeholders})
                """,
                tuple(item_ids),
            )
            anns = [dict(r) for r in await cursor.fetchall()]

        # Best relevance per item (across lenses), and per (item, lens).
        by_item_best: dict[str, float] = {}
        per_lens: dict[str, dict[str, float]] = {}  # lens_id → item_id → score
        per_lens_imp: dict[str, dict[str, float]] = {}
        per_lens_nov: dict[str, dict[str, float]] = {}
        per_lens_qual: dict[str, dict[str, float]] = {}
        for a in anns:
            iid, lid = a["item_id"], a["lens_id"]
            score = a["relevance_score"] or 0.0
            if score > by_item_best.get(iid, -1.0):
                by_item_best[iid] = score
            per_lens.setdefault(lid, {})[iid] = score
            per_lens_imp.setdefault(lid, {})[iid] = a["importance_score"] or 0.0
            per_lens_nov.setdefault(lid, {})[iid] = a["novelty_score"] or 0.0
            per_lens_qual.setdefault(lid, {})[iid] = a["quality_score"] or 0.0

        # Which lenses pass the relevance bar for this cluster?
        qualifying_lenses: list[tuple[str, float]] = []
        for lens in lenses:
            best = max(
                (per_lens.get(lens.id, {}).get(iid, 0.0) for iid in item_ids),
                default=0.0,
            )
            if best >= settings.RELEVANCE_THRESHOLD:
                qualifying_lenses.append((lens.id, best))
        if not qualifying_lenses:
            continue

        # Annotate items with their best score for sorting + framing.
        for it in items:
            it["best_relevance"] = by_item_best.get(it["id"], 0.0)
        items.sort(key=lambda x: x["best_relevance"], reverse=True)
        top_items = items[:8]

        framing = _choose_framing(top_items, verdict)

        # Build the merge prompt.
        primary_lens_id = max(qualifying_lenses, key=lambda x: x[1])[0]
        primary_lens = lens_by_id[primary_lens_id]
        system = (
            "You produce one brief from a cluster of related items. The "
            "brief must hold up under multiple lenses; write the lead so "
            "it lands for each. Pull claims directly from the source items "
            "below — every claim must cite one source by index.\n\n"
            f"Primary {lens_context_block(primary_lens)}\n\n"
            f"Other qualifying lenses: "
            f"{', '.join(l for l, _ in qualifying_lenses if l != primary_lens_id) or '(none)'}\n"
            f"Trend verdict: {verdict or 'noise'}\n"
            f"Framing: {framing}"
        )

        sources_block = []
        for idx, it in enumerate(top_items):
            sources_block.append(
                f"[{idx}] source={it['source']} | "
                f"author={it.get('authors') or '(unknown)'} | "
                f"title={it['title']}\n"
                f"  content: {(it.get('content') or '')[:1200]}"
            )
        prompt = (
            f"FRAMING: {framing}\n"
            f"If 'item_anchored': anchor the brief on the highest-scoring "
            f"item; treat the rest as corroboration.\n"
            f"If 'synthesis': write a topic-level brief; no single author "
            f"leads.\n\n"
            f"Produce JSON with: title (≤80 chars), lead (≤280 chars), "
            f"why_it_matters (≤320 chars), claims (3–5 items). Each claim "
            f"has n (1-based), text (≤200 chars), source_index "
            f"(0-based into the SOURCES list), citation_text (short "
            f"human-readable, e.g. 'arxiv.org · 2401.12345'), and "
            f"confidence (0..1).\n\n"
            f"SOURCES:\n" + "\n\n".join(sources_block)
        )

        try:
            brief = await provider.complete_json(
                prompt=prompt, system=system, schema=BRIEF_SCHEMA
            )
        except Exception:
            logger.exception(
                "Merger failed for cluster %s", cluster["id"]
            )
            continue

        if not brief or "title" not in brief:
            continue

        # Persist.
        brief_id = str(uuid.uuid4())
        avg_relevance = sum(s for _, s in qualifying_lenses) / len(qualifying_lenses)
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO feed_items
                  (id, cluster_id, framing, title, lead, summary,
                   why_it_matters, source_links, feed_date, final_rank,
                   presentation_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'news')
                """,
                (
                    brief_id,
                    cluster["id"],
                    framing,
                    brief["title"][:200],
                    brief["lead"][:400],
                    brief["lead"][:400],  # `summary` legacy column; keep populated
                    brief["why_it_matters"][:400],
                    json.dumps([
                        {
                            "item_id": it["id"],
                            "url": it.get("url"),
                            "source": it["source"],
                            "title": it["title"],
                        } for it in top_items
                    ]),
                    feed_date.isoformat(),
                    avg_relevance,
                ),
            )
            for lens_id, score in qualifying_lenses:
                await db.execute(
                    """
                    INSERT INTO feed_item_lenses
                      (feed_item_id, lens_id, relevance_score)
                    VALUES (?, ?, ?)
                    """,
                    (brief_id, lens_id, score),
                )
            for claim in brief.get("claims") or []:
                idx = claim.get("source_index") or 0
                if idx < 0 or idx >= len(top_items):
                    idx = 0
                src_item = top_items[idx]
                await db.execute(
                    """
                    INSERT INTO brief_claims
                      (feed_item_id, n, text, source_item_id,
                       citation_text, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        brief_id,
                        claim.get("n", 1),
                        claim["text"][:300],
                        src_item["id"],
                        claim.get("citation_text")
                        or _build_citation(src_item),
                        claim.get("confidence", 0.7),
                    ),
                )
            await db.commit()
        written += 1
    return written
