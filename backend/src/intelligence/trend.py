import json
import logging
from datetime import date, timedelta

from src.db.database import get_db
from src.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


async def judge_trends(feed_date: date, provider: LLMProvider) -> int:
    """Classify today's clusters as emerging / sustained / fading / noise.

    Heuristic filter first: only clusters with size ≥ 3 and ≥ 2 distinct
    sources, OR clusters whose topic_tag was 'emerging' / 'sustained'
    yesterday, are candidates for the LLM pass. Everything else is
    auto-classified as 'noise'.
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM topic_clusters WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        clusters = [dict(r) for r in await cursor.fetchall()]

        yesterday = (feed_date - timedelta(days=1)).isoformat()
        # If yesterday produced multiple clusters under the same tag,
        # prefer the strongest verdict (emerging/sustained beat fading
        # beats noise). Otherwise the dict order would be undefined.
        cursor = await db.execute(
            """
            SELECT topic_tag, verdict FROM trend_judgments
            WHERE feed_date = ?
            ORDER BY CASE verdict
                WHEN 'emerging' THEN 0
                WHEN 'sustained' THEN 1
                WHEN 'fading' THEN 2
                ELSE 3
            END
            """,
            (yesterday,),
        )
        prior: dict[str, str] = {}
        for r in await cursor.fetchall():
            prior.setdefault(r["topic_tag"], r["verdict"])

    if not clusters:
        return 0

    candidates = []
    noise_ids = []
    for c in clusters:
        item_ids = json.loads(c["item_ids"])
        size = len(item_ids)
        prior_verdict = prior.get(c["topic_tag"])
        if (
            (size >= 3 and (c["source_count"] or 0) >= 2)
            or prior_verdict in {"emerging", "sustained"}
        ):
            candidates.append({
                **c,
                "size": size,
                "prior_verdict": prior_verdict,
            })
        else:
            noise_ids.append(c["id"])

    # Auto-write the heuristic noise verdicts.
    async with get_db() as db:
        await db.execute(
            "DELETE FROM trend_judgments WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        for cid in noise_ids:
            c = next(x for x in clusters if x["id"] == cid)
            await db.execute(
                """
                INSERT INTO trend_judgments
                  (feed_date, cluster_id, topic_tag, verdict, rationale)
                VALUES (?, ?, ?, 'noise', 'Below trend candidate threshold.')
                """,
                (feed_date.isoformat(), cid, c["topic_tag"]),
            )
        await db.commit()

    if not candidates:
        return len(noise_ids)

    # LLM pass on the survivors.
    descs = []
    for i, c in enumerate(candidates):
        prior_str = (
            f" (prior verdict: {c['prior_verdict']})"
            if c["prior_verdict"] else ""
        )
        descs.append(
            f"[{i}] tag={c['topic_tag']} size={c['size']} "
            f"sources={c['source_count']}{prior_str} | label={c['topic_label']}"
        )
    prompt = (
        "Classify each cluster's trend status. Verdicts:\n"
        "  emerging — first appearing or accelerating; new development\n"
        "  sustained — continuing story, multiple days of signal\n"
        "  fading — was active but slowing\n"
        "  noise — coincidental co-occurrence, not a real trend\n\n"
        "Return JSON with 'verdicts': a list, one entry per index, each "
        "an object with 'verdict' and 'rationale' (≤ 1 sentence).\n\n"
        "CLUSTERS:\n" + "\n".join(descs)
    )
    schema = {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "verdict": {
                            "type": "string",
                            "enum": ["emerging", "sustained", "fading", "noise"],
                        },
                        "rationale": {"type": "string"},
                    },
                    "required": ["verdict", "rationale"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["verdicts"],
        "additionalProperties": False,
    }
    try:
        out = await provider.complete_json(prompt=prompt, schema=schema)
        verdicts = out.get("verdicts") or []
    except Exception:
        logger.exception("Trend judge LLM call failed; defaulting to noise")
        verdicts = []

    async with get_db() as db:
        for i, c in enumerate(candidates):
            v = verdicts[i] if i < len(verdicts) else {
                "verdict": "noise",
                "rationale": "Trend judge unavailable.",
            }
            await db.execute(
                """
                INSERT INTO trend_judgments
                  (feed_date, cluster_id, topic_tag, verdict, rationale)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    feed_date.isoformat(),
                    c["id"],
                    c["topic_tag"],
                    v["verdict"],
                    v.get("rationale"),
                ),
            )
        await db.commit()
    return len(noise_ids) + len(verdicts)
