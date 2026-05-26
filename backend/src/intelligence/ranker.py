import json
import logging
from collections import defaultdict
from datetime import date

from src.config import settings
from src.db.database import get_db

logger = logging.getLogger(__name__)


async def rank_and_select(feed_date: date) -> int:
    """Score every brief and trim to the daily cap.

    - Per-lens adaptive volume: each lens gets at most FEED_PER_LENS_CAP
      briefs (default 4).
    - Hard total cap of FEED_DAILY_CAP (default 7).
    - Multi-lens briefs count toward each tagged lens's quota.

    Drops briefs that don't make either cut by setting final_rank to NULL
    and removing them from feed_item_lenses (cheap soft-delete).
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT
                fi.id, fi.cluster_id, fi.final_rank, fi.framing,
                fil.lens_id, fil.relevance_score,
                tj.verdict
            FROM feed_items fi
            JOIN feed_item_lenses fil ON fil.feed_item_id = fi.id
            LEFT JOIN trend_judgments tj ON tj.cluster_id = fi.cluster_id
                AND tj.feed_date = fi.feed_date
            WHERE fi.feed_date = ?
            """,
            (feed_date.isoformat(),),
        )
        rows = [dict(r) for r in await cursor.fetchall()]

        # Annotation rollup per cluster. We average each item's
        # best-lens score first (so an item annotated across N lenses
        # contributes once, not N times), then average those across
        # the cluster. `json_each` matches item_ids by value, not
        # substring, so a numeric id that's a prefix of another id
        # won't bleed across clusters.
        cursor = await db.execute(
            """
            WITH item_best AS (
                SELECT
                    a.item_id,
                    MAX(a.importance_score) AS importance,
                    MAX(a.novelty_score) AS novelty,
                    MAX(a.quality_score) AS quality
                FROM item_annotations a
                GROUP BY a.item_id
            )
            SELECT
                tc.id AS cluster_id,
                AVG(ib.importance) AS importance,
                AVG(ib.novelty) AS novelty,
                AVG(ib.quality) AS quality
            FROM topic_clusters tc
            JOIN json_each(tc.item_ids) je
            JOIN item_best ib ON ib.item_id = je.value
            WHERE tc.feed_date = ?
            GROUP BY tc.id
            """,
            (feed_date.isoformat(),),
        )
        cluster_stats = {
            r["cluster_id"]: dict(r) for r in await cursor.fetchall()
        }

    if not rows:
        return 0

    # Compute final_rank per (brief, lens). Briefs may appear under more
    # than one lens; they get the SUM-of-lens-rank, but per-lens caps see
    # only that lens's rank.
    per_brief_lens_rank: dict[tuple[str, str], float] = {}
    brief_to_lenses: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        stats = cluster_stats.get(r["cluster_id"]) or {}
        relevance = r["relevance_score"] or 0.0
        importance = stats.get("importance") or 0.0
        novelty = stats.get("novelty") or 0.0
        quality = stats.get("quality") or 0.0
        if r["verdict"] == "emerging":
            novelty = min(1.0, novelty + 0.2)

        rank = (
            0.40 * relevance
            + 0.20 * importance
            + 0.20 * novelty
            + 0.10 * quality
            + 0.10 * 0.5  # preference_weight placeholder (v1)
        )
        per_brief_lens_rank[(r["id"], r["lens_id"])] = rank
        brief_to_lenses[r["id"]].append(r["lens_id"])

    # Per-lens shortlist.
    per_lens_briefs: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (brief_id, lens_id), rank in per_brief_lens_rank.items():
        per_lens_briefs[lens_id].append((brief_id, rank))
    for lens_id in per_lens_briefs:
        per_lens_briefs[lens_id].sort(key=lambda x: x[1], reverse=True)

    keep_ids: set[str] = set()
    for lens_id, ranked in per_lens_briefs.items():
        for brief_id, _ in ranked[: settings.FEED_PER_LENS_CAP]:
            keep_ids.add(brief_id)

    # Apply the global cap on the union, ranked by each brief's best
    # per-lens rank.
    brief_best_rank: dict[str, float] = {}
    for (brief_id, _), rank in per_brief_lens_rank.items():
        if rank > brief_best_rank.get(brief_id, -1.0):
            brief_best_rank[brief_id] = rank
    keep_sorted = sorted(
        keep_ids, key=lambda b: brief_best_rank.get(b, 0.0), reverse=True
    )
    final_keep = set(keep_sorted[: settings.FEED_DAILY_CAP])

    # Persist final ranks; null out the rest.
    async with get_db() as db:
        for brief_id, best_rank in brief_best_rank.items():
            if brief_id in final_keep:
                await db.execute(
                    "UPDATE feed_items SET final_rank = ? WHERE id = ?",
                    (best_rank, brief_id),
                )
            else:
                await db.execute(
                    "UPDATE feed_items SET final_rank = NULL WHERE id = ?",
                    (brief_id,),
                )
        await db.commit()

    logger.info(
        "Ranker kept %d/%d briefs (cap=%d/lens=%d)",
        len(final_keep), len(brief_to_lenses),
        settings.FEED_DAILY_CAP, settings.FEED_PER_LENS_CAP,
    )
    return len(final_keep)
