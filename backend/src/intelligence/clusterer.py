import json
import logging
import re
import uuid
from datetime import date
from urllib.parse import urlparse

from src.db.database import get_db
from src.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


# Stopwords trimmed out before computing title token Jaccard. Anything
# more elaborate is overkill at this scale.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "is", "are", "was", "were", "be",
    "this", "that", "these", "those", "it", "its", "we", "you", "they",
    "how", "why", "what", "when", "where", "i", "your", "our", "their",
    "more", "than", "into", "about", "new", "show", "hn", "ask",
}


def _title_tokens(title: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z][a-z\-]{2,}", (title or "").lower())
        if t not in STOPWORDS
    }


def _url_key(url: str | None) -> str | None:
    """Strip protocol, www., and trailing slash so we can spot duplicate
    submissions across HN / Reddit pointing at the same arxiv paper."""
    if not url:
        return None
    try:
        u = urlparse(url)
        netloc = u.netloc.lower().removeprefix("www.")
        path = u.path.rstrip("/")
        return f"{netloc}{path}"
    except Exception:
        return None


def _heuristic_groups(items: list[dict]) -> list[list[dict]]:
    """Bucket items into candidate cluster groups before any LLM call.

    Groups are built by:
      1. topic_tag equality (when present)
      2. URL key collisions (same article reposted)
      3. title token Jaccard ≥ 0.4 within the same source

    Anything that doesn't merge ends up as a singleton — the LLM-confirm
    step won't be invoked on those.
    """
    # Pass 1: group by topic_tag.
    by_tag: dict[str, list[dict]] = {}
    untagged: list[dict] = []
    for it in items:
        tag = it.get("topic_tag")
        if tag and tag not in {"off_topic", "noise"}:
            by_tag.setdefault(tag, []).append(it)
        else:
            untagged.append(it)

    groups = list(by_tag.values())

    # Pass 2: URL-key matches. Build an index over both tagged and
    # untagged items so untagged items pointing at the same URL merge
    # together even when no tagged item is in the picture.
    url_to_group: dict[str, list[dict]] = {}
    for g in groups:
        for it in g:
            k = _url_key(it.get("url"))
            if k:
                url_to_group.setdefault(k, g)
    for it in untagged:
        k = _url_key(it.get("url"))
        if k and k in url_to_group:
            url_to_group[k].append(it)
        elif k:
            new_group = [it]
            url_to_group[k] = new_group
            groups.append(new_group)
        else:
            groups.append([it])

    return groups


async def build_clusters(
    feed_date: date,
    provider: LLMProvider,
    relevance_floor: float = 0.2,
) -> int:
    """Build today's `topic_clusters` rows from annotated items.

    Returns the number of clusters written.
    """
    # Pull every item × lens annotation from the last 24h whose best
    # lens-relevance is above the floor — there's no point clustering
    # noise.
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT
                i.id, i.source, i.title, i.url, i.content,
                MAX(a.relevance_score) AS best_relevance,
                (
                  SELECT topic_tag FROM item_annotations
                  WHERE item_id = i.id
                  ORDER BY relevance_score DESC LIMIT 1
                ) AS topic_tag
            FROM items i
            JOIN item_annotations a ON a.item_id = i.id
            WHERE i.fetched_at >= datetime('now', '-36 hours')
            GROUP BY i.id
            HAVING best_relevance >= ?
            """,
            (relevance_floor,),
        )
        rows = await cursor.fetchall()

    items = [dict(r) for r in rows]
    if not items:
        return 0

    candidate_groups = _heuristic_groups(items)
    logger.info(
        "Clustering: %d items → %d heuristic candidate groups",
        len(items), len(candidate_groups),
    )

    final_groups = await _llm_confirm(candidate_groups, provider)

    # Persist clusters.
    async with get_db() as db:
        # Wipe today's previous attempt so re-runs are idempotent.
        await db.execute(
            "DELETE FROM topic_clusters WHERE feed_date = ?",
            (feed_date.isoformat(),),
        )
        written = 0
        for group in final_groups:
            if not group:
                continue
            tags = [it.get("topic_tag") for it in group if it.get("topic_tag")]
            topic_tag = max(set(tags), key=tags.count) if tags else "general"
            sources = {it.get("source") for it in group}
            label = group[0].get("title") or topic_tag
            cluster_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO topic_clusters
                  (id, topic_label, topic_tag, item_ids, source_count, feed_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cluster_id,
                    label[:200],
                    topic_tag,
                    json.dumps([it["id"] for it in group]),
                    len(sources),
                    feed_date.isoformat(),
                ),
            )
            written += 1
        await db.commit()
    return written


async def _llm_confirm(
    candidate_groups: list[list[dict]],
    provider: LLMProvider,
) -> list[list[dict]]:
    """For each multi-item candidate group, ask the model to split it if
    items aren't actually about the same thing. Singletons pass through."""
    result: list[list[dict]] = []
    for group in candidate_groups:
        if len(group) <= 1:
            result.append(group)
            continue

        # Build a minimal description for the LLM.
        descs = []
        for i, it in enumerate(group):
            snippet = (it.get("content") or "")[:200].replace("\n", " ")
            descs.append(
                f"[{i}] source={it['source']} | {it['title']} | {snippet}"
            )
        prompt = (
            "Below is a candidate cluster of items that may all be about "
            "the same development. Decide whether they are. Return JSON "
            "with the field 'partition': a list of lists of item indices. "
            "Items in the same inner list belong to the same cluster. If "
            "they're all about the same thing, return one inner list with "
            "every index. If some are unrelated, split them out. Do not "
            "drop any index.\n\nITEMS:\n" + "\n".join(descs)
        )
        schema = {
            "type": "object",
            "properties": {
                "partition": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 0},
                    },
                }
            },
            "required": ["partition"],
            "additionalProperties": False,
        }
        try:
            out = await provider.complete_json(prompt=prompt, schema=schema)
            partition = out.get("partition") or [list(range(len(group)))]
        except Exception:
            logger.exception("Cluster-confirm LLM call failed")
            partition = [list(range(len(group)))]

        seen = set()
        for inner in partition:
            sub = []
            for idx in inner:
                if isinstance(idx, int) and 0 <= idx < len(group) and idx not in seen:
                    sub.append(group[idx])
                    seen.add(idx)
            if sub:
                result.append(sub)
        # Catch items the model dropped — preserve them as singletons.
        for idx, it in enumerate(group):
            if idx not in seen:
                result.append([it])
    return result
