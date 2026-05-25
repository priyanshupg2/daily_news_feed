# Prism backend — system design (v2)

> Companion to `DESIGN.md`. Where this contradicts the original, this
> wins; where it stays silent, the original holds. Supersedes the
> earlier draft of this file.

This is the slice that takes the product from "nothing on screen" to a
real daily brief: lens-tagged, claim-traceable, generated against your
thesis. The frontend already commits to the lens model. The backend
does not — yet. This document is the bridge.

The user (one human) operates under **four lenses** for v0:
**Founder, Engineer, Researcher, Operator**. Investor is in the
spectrum but not active. Every lens is a distinct identity view with
its own thesis, its own relevance bar, its own knowledge state. The
pipeline is built around that.

---

## 1. Where we are

What already exists in `backend/`:

- **Schema (v0)**: items, item_annotations, topic_clusters, feed_items,
  generated_content, user_profile, user_preferences, knowledge_log, the
  three feedback tables, user_prompts. Indexes in place.
- **Pydantic models** in `db/models.py`.
- **`DiscoveryEngine`** in `discovery/engine.py`: takes sources via DI,
  fetches them, stores items with dedup on `(source, source_id)`.
- **`OllamaProvider`** in `llm/ollama.py` against the contract in
  `provider.py`.
- **FastAPI app** in `main.py` with router stubs — every endpoint
  returns a placeholder.

What is missing (and what this doc covers):

- No real sources. Just the protocol.
- No annotator, clusterer, trend judge, merger, ranker, content
  generator. The entire intelligence layer.
- No Claude provider.
- No scheduler.
- The endpoints don't read or write anything real.
- The schema needs the lens model and a claims table.

---

## 2. The lens model — schema delta

One human user. **Four active lenses** under that user, each a saved
persona with its own thesis, working topics, learning topics, and
feedback history. A single piece of intelligence (a cluster of
related items in the world) gets framed **once** into one brief, but
that brief can carry **multiple lens tags** when the world is
genuinely refracting across more than one of your hats. A
speculative-decoding reference implementation is one brief — tagged
Engineer + Researcher, surfacing under either filter.

Schema delta (additive — no destructive migration):

```sql
CREATE TABLE lenses (
    id TEXT PRIMARY KEY,                   -- 'founder', 'engineer', ...
    name TEXT NOT NULL,                    -- display name
    accent_token TEXT NOT NULL,            -- 'lens-founder' (frontend CSS var)
    thesis TEXT,                           -- "agentic workflows for SMB payroll in India"
    working_topics TEXT,                   -- JSON array of strings
    learning_topics TEXT,                  -- JSON array of strings
    active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Annotation is per (item, lens).
ALTER TABLE item_annotations ADD COLUMN lens_id TEXT REFERENCES lenses(id);
-- UNIQUE(item_id) becomes UNIQUE(item_id, lens_id) on a fresh DB.
-- Also add a rationale column for the raw-data browser tooltip.
ALTER TABLE item_annotations ADD COLUMN rationale TEXT;

-- A brief carries a *set* of lenses. The join table is the source of
-- truth; no lens_id column on feed_items. Highest relevance_score
-- across the set determines the primary lens in the eyebrow.
CREATE TABLE feed_item_lenses (
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id) ON DELETE CASCADE,
    lens_id TEXT NOT NULL REFERENCES lenses(id),
    relevance_score REAL NOT NULL,
    PRIMARY KEY (feed_item_id, lens_id)
);

-- Brief structure that lives outside the existing summary column.
ALTER TABLE feed_items ADD COLUMN title TEXT;
ALTER TABLE feed_items ADD COLUMN lead TEXT;
ALTER TABLE feed_items ADD COLUMN framing TEXT;  -- 'item_anchored' | 'synthesis'

-- Knowledge and preferences are per-lens.
ALTER TABLE knowledge_log ADD COLUMN lens_id TEXT REFERENCES lenses(id);
ALTER TABLE user_preferences ADD COLUMN lens_id TEXT REFERENCES lenses(id);
-- Uniqueness becomes (topic_tag, lens_id).

-- Claims are first-class. The brand promise is traceability —
-- claims with citations should not live as JSON inside summary.
CREATE TABLE brief_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id) ON DELETE CASCADE,
    n INTEGER NOT NULL,                    -- 1-based display order
    text TEXT NOT NULL,
    source_item_id TEXT REFERENCES items(id),  -- primary source
    citation_text TEXT,                    -- "arxiv.org · 2405.12345 · §3"
    confidence REAL,                       -- model confidence 0..1
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_item_id, n)
);

CREATE TABLE brief_claim_corroborations (
    claim_id INTEGER NOT NULL REFERENCES brief_claims(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES items(id),
    PRIMARY KEY (claim_id, item_id)
);

-- Trend judgments survive across days so the next day's trend pass
-- can use yesterday's list as a consistency anchor.
CREATE TABLE trend_judgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_date DATE NOT NULL,
    cluster_id TEXT REFERENCES topic_clusters(id),
    topic_tag TEXT NOT NULL,
    verdict TEXT NOT NULL,                 -- 'emerging' | 'sustained' | 'fading' | 'noise'
    rationale TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_date, cluster_id)
);

-- "3 sources auto-muted this week" — the endnote on the brief.
CREATE TABLE muted_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,                 -- domain, subreddit, author
    pattern_type TEXT NOT NULL,            -- 'domain' | 'subreddit' | 'author'
    lens_id TEXT REFERENCES lenses(id),    -- NULL = mute globally
    reason TEXT,                           -- 'auto' or free text
    muted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

`user_profile` stays — it holds the human's top-level goals and
email, sitting above the lenses.

---

## 3. The pipeline

Six steps. One scheduled run per day at 06:00. No mid-day regenerate;
time-of-day theming in the UI is cosmetic only.

```
discovery → annotation → clustering → trend judgment → merge + claims → ranking
   (I/O)     (Sonnet,        (LLM,          (Opus,         (Opus,           (cheap)
            per lens)     heuristic-fed)  heuristic-fed)  per cluster)
```

Heuristics gate every LLM step. The LLM is invoked only where
deterministic logic isn't enough.

### 3.1 Discovery (`discovery/sources/`)

Three sources in v0:

- **arXiv** — Atom API on cs.AI / cs.LG / cs.CL. Last 24h. Polite UA,
  3s between batches. No auth.
- **Hacker News** — Algolia API. Stories above a score threshold from
  the last 24h. No auth.
- **Reddit** — public `.json` endpoints on r/MachineLearning,
  r/LocalLLaMA, r/singularity (the AI-adjacent subreddits the lenses
  care about). Keyless, rate-limited; one request per subreddit per
  run is plenty.

Each source is one file under `discovery/sources/` implementing the
`Source` protocol. v1 adds founder-flavored sources (TechCrunch,
TheInformation funding desk, indie-hacker feeds) and operator-flavored
ones (DevOps newsletters, ops-focused subreddits).

### 3.2 Annotation (`intelligence/annotator.py`)

For each `(new item, active lens)` pair:

**Heuristic pre-gate**: skip the LLM call if the item shows zero
keyword overlap with the lens's thesis, working topics, or learning
topics. Record a stub annotation with `relevance_score = 0.0` so the
raw-data browser still sees it.

If the gate lets it through, call **Sonnet 4.6** with:

- The item (title, content, source metadata)
- The lens (thesis, working topics, learning topics)
- The user's last K annotation corrections for this lens (in the
  cached portion of the system prompt — this is how the model learns
  from feedback without retraining)

Output (JSON):
```json
{
  "relevance_score": 0.0..1.0,
  "quality_score": 0.0..1.0,
  "novelty_score": 0.0..1.0,
  "importance_score": 0.0..1.0,
  "topic_tag": "snake_case_normalized",
  "rationale": "one sentence, raw-data browser tooltip"
}
```

Concurrency: `asyncio.Semaphore(8)`. Cost driver of the pipeline;
prompt caching takes ~80% of the input tokens back.

### 3.3 Clustering (`intelligence/clusterer.py`)

**Heuristic candidates** first: group items in the last 24h by
`topic_tag`, then within each tag look for URL overlap, shared
arxiv-id, source-native tag overlap, or token-Jaccard above 0.4 on
titles. Build candidate cluster groups.

**LLM pass (Sonnet)**: for each candidate group with > 1 item,
confirm / split / merge. Given the candidate group as a list of
`(title, source, snippet)` tuples, the LLM returns a partition into
final clusters. Single-item candidates pass through as singleton
clusters without an LLM call.

A second LLM pass merges close-but-not-identical topic_tags
(`flash_attention_3` and `flash_attn_v3`) once per day across the
full tag list. This is where the "100 tweets about Open Claw" case
resolves.

### 3.4 Trend judgment (`intelligence/trend.py`)

**Heuristic candidate filter**: a cluster is a trend candidate if
size ≥ 3 items AND source diversity ≥ 2 distinct sources, OR if its
topic_tag appears in yesterday's `trend_judgments` with verdict in
{`emerging`, `sustained`}.

**LLM pass (Opus 4.7)**: given the candidate clusters (with size,
source set, item titles, prior verdicts) and yesterday's trend list
as an anchor, classify each as `emerging`, `sustained`, `fading`, or
`noise`. The rationale is stored on `trend_judgments` for the
explainer mode and for next-day input.

This produces no user-visible output on its own. It feeds the
merger's framing decision and the ranker's novelty term.

### 3.5 Merge + claim extract (`intelligence/merger.py`)

For each cluster where the highest cross-lens `relevance_score ≥ 0.5`:

**Framing heuristic** (no LLM):

- If cluster has 1 item, or one item dominates by score and the rest
  are weak corroborations → **item_anchored** brief (title from
  source, author surfaced, the other items become corroborating
  citations).
- If cluster has ≥ 3 items from ≥ 2 sources of comparable score, or
  trend verdict is `emerging` / `sustained` → **synthesis** brief
  (title from trend rationale, no single author, claims drawn from
  across items).
- Otherwise → **item_anchored** with the highest-scoring item as
  anchor.

**LLM pass (Opus 4.7)** within the chosen framing:

- Inputs: framing mode, cluster items (top 5–8 by score), the union
  of lenses where the cluster passes the relevance bar, the cached
  voice block.
- Outputs: `title`, `lead`, `why_it_matters`, `claims[]` (each with
  text + primary `source_item_id` + citation string + confidence).

Persisted: one `feed_items` row, N `brief_claims` rows, plus
`feed_item_lenses` rows for every lens that cleared `relevance_score
≥ 0.5` on at least one item in the cluster.

### 3.6 Ranking (`intelligence/ranker.py`)

For each lens, score every brief tagged with it:

```
final_rank = 0.4 * relevance_for_this_lens
           + 0.2 * importance
           + 0.2 * novelty            (weighted up if trend = 'emerging')
           + 0.1 * quality
           + 0.1 * preference_weight(topic_tag, lens)
           + boost_from_user_prompts(topic_tag, lens, now)
           - mute_penalty(source)
```

Adaptive volume per lens: 0–4 briefs depending on signal quality.
Hard total cap of 7 across all lenses. A quiet lens contributes zero
on a quiet day. Multi-lens briefs count toward each tagged lens's
quota.

---

## 4. Heuristic catalog

Every place where deterministic logic precedes or replaces an LLM
call, listed for grep:

| Stage | Heuristic | Purpose |
|---|---|---|
| Annotation | keyword overlap vs lens context | skip LLM for obviously-irrelevant items |
| Clustering | tag equality + URL/arxiv-id match + title Jaccard ≥ 0.4 | build cluster candidates |
| Clustering | single-item candidate → singleton cluster | skip LLM confirm |
| Trend | size ≥ 3 ∧ sources ≥ 2 ∨ yesterday emerging/sustained | trend candidate filter |
| Merger | 1 item or dominant score → item_anchored | framing decision |
| Merger | ≥ 3 items, ≥ 2 sources, trend ∈ {emerging, sustained} → synthesis | framing decision |
| Ranker | top-K with adaptive K | volume control |
| Ranker | total cap 7 | no firehose |
| Auto-mute | 3 negative-feedback hits / 7d / same source / same lens | source muting |
| Source authority | per-source quality prior (arXiv = 0.8, HN = 0.6, …) | quality bootstrap |
| Voice | linter pass over generated text — blocklist words, length caps | brand enforcement |

---

## 5. LLM strategy

- **Default**: Claude. Two model channels.
  - **Sonnet 4.6** — annotation (high volume), cluster confirm/merge,
    voice linter, prompt parsing.
  - **Opus 4.7** — trend judgment, merge + claim extraction, brief
    titles. Editorial steps where quality compounds.
- **Fallback**: Ollama. Auto-engaged if `ANTHROPIC_API_KEY` is empty.
  Same `complete` / `complete_json` contract. Lower fidelity, fine
  for dev.
- **Prompt caching**: the voice block, lens definitions, and recent
  annotation corrections sit in the cached portion of the system
  prompt. Per-item content is the dynamic part. Highest leverage in
  annotation (hundreds of calls, same system context).
- **Concurrency**: `asyncio.Semaphore(8)`. Honors Anthropic default
  org tier.

Provider classes go in `llm/claude.py`. The factory in
`llm/provider.py` already has the switch case stubbed.

---

## 6. API shape

```
GET  /api/feed?date=2026-05-25&lens=engineer    # filter to lens (omit → all)
GET  /api/feed/:brief_id                         # one brief incl. claims
POST /api/feed/refresh                           # re-run pipeline now
POST /api/feed/:brief_id/generate                # on-demand explainer/discussion
POST /api/feed/:brief_id/read                    # mark read + time spent

GET  /api/raw?date=...&lens=...&source=...&topic=...
POST /api/feedback/item                          # like / dislike / save / mute
POST /api/feedback/annotation                    # correct an annotation
POST /api/prompt                                 # "more CUDA this week"

GET  /api/lenses                                 # list with active state
POST /api/lenses                                 # create
PUT  /api/lenses/:id                             # edit thesis / topics
DELETE /api/lenses/:id                           # archive (keeps history)

GET  /api/profile
PUT  /api/profile
GET  /api/profile/onboarding-needed
GET  /api/profile/knowledge?lens=...
GET  /api/profile/preferences?lens=...

GET  /api/health
```

`GET /api/feed` returns the shape the frontend already consumes —
`{briefs: [{id, lenses[], primary_lens, title, lead, why,
source_count, read_min, sources[], claims[]}]}`. The `lenses` array
drives the multi-lens eyebrow; `primary_lens` is the highest-relevance
tag for sort/grouping. The fixtures in
`frontend/src/app/_brief/data.ts` get deleted in v0.

---

## 7. Voice enforcement

Every prompt producing user-visible text gets the same cached system
fragment:

```
Write in Prism's voice: editorial, precise, slightly dry, never
breathless. Direct address — "you", never "we" or "users". Verbs do
the work: reads, extracts, verifies, tunes, mutes. No hype
adjectives — revolutionary, game-changing, seamless, AI-powered,
intelligent. Sentence case. Em-dashes to set off clauses. No emoji,
no unicode pictograms.

Vocabulary: lens, brief, signal, noise, source, claim, thesis.
Never: channel, feed, digest, newsletter, summary, hits, citation
(as a verb), interests.

Length: lead ≤ 280 chars, why_it_matters ≤ 320 chars, each claim ≤
200 chars.
```

A post-generation linter pass rejects outputs that violate the
length caps or contain blocklist words, and triggers one regeneration
attempt with the violations called out. Failure twice → drop to
Sonnet draft + log to a `voice_violations` table for review.

The merger gets a few-shot block of canonical brand copy lifted from
the design-system README, cached. Single highest-leverage prompt in
the system.

---

## 8. Use cases

### UC-1 — Morning brief generation (06:00 daily)

Scheduler kicks the pipeline. Discovery has been running every 2h
since the prior morning, so `items` has the last 24h of raw signal.
Annotator walks new items × active lenses, scoring each (Sonnet,
prompt-cached). Clusterer groups by `topic_tag`, then LLM-confirms
candidates from URL/title overlap. Trend judge classifies clusters.
Merger produces multi-lens briefs with extracted claims, each pinned
to its primary source item. Ranker selects up to 7 across lenses.
Frontend at 06:01 fetches `/api/feed?date=today` and renders.

### UC-2 — Reader expands a brief

Tap the title. Frontend already has the claims — no extra fetch.
Each claim shows its primary source as a citation chip. Tapping the
chip opens the original item in a new tab. "+ N more" opens the full
source list panel.

### UC-3 — Reader corrects an annotation

Raw-data browser. User disagrees with a score — relevance 0.2 for
Engineer, but they say 0.8. Posts the correction; lands in
`feedback_annotations`. Next annotation run for that lens injects the
last 30 corrections into the cached system prompt. The model adjusts
without fine-tuning.

### UC-4 — Free-text prompt: "more CUDA this week"

User types. Sonnet parses intent + topic. Stored as a `user_prompts`
row with effect `{"action": "boost", "topic_tag": "cuda", "lens_id":
"engineer", "ttl_days": 7}`. Ranker adds the boost term during the
TTL window. Effect is logged so the user sees what was done.

### UC-5 — Auto-mute kicks in

Three dislikes from `substack.com/some-vc-newsletter` for the
Engineer lens within 7 days. Background task writes a `muted_sources`
row scoped to that lens. Future items from the domain skip clustering
for that lens (still visible in raw data). The brief endnote reads
"3 sources auto-muted this week" — that number is `COUNT(*)` over
`muted_sources` with `reason = 'auto'` and `muted_at >= now() - 7d`.

### UC-6 — Adding a fifth lens

User goes to profile → "Add lens" → picks Investor. Onboarding
collects thesis + working/learning topics. Saved as a new `lenses`
row. Next pipeline run also scores items against the new lens. The
frontend lens switcher picks it up via `GET /api/lenses`.

---

## 9. Phasing

**v0 — the slice that replaces the fixtures and proves the pipeline.**
This is what gets built now.
- Lens schema + the four seed lenses (Founder, Engineer, Researcher,
  Operator) with editable thesis stubs
- arXiv + HN + Reddit sources (real, running)
- Claude provider with Sonnet + Opus channels, prompt caching, Ollama
  fallback
- Annotation per (item, lens) with heuristic pre-gate
- Clustering with heuristic candidates + LLM confirm
- Trend judgment with heuristic candidates + LLM verdict
- Framing heuristic + Opus merge with claim extraction
- Ranker with adaptive volume + hard cap
- Feed + raw-data + lenses endpoints backing the frontend
- Scheduler: 2h discovery, 06:00 pipeline
- Frontend swap: delete `data.ts`, fetch from `/api/feed`

**v1 — feedback closes the loop.**
- Feedback endpoints update preferences and proficiency
- Annotation corrections folded into next run
- Free-text prompt parsing → ranker boosts
- Auto-mute heuristic running
- Explainer (basics / delta) and Discussion on-demand modes
- Reading history → per-lens proficiency
- Onboarding UI (today: seeded lenses; v1: real wizard)

**v2 — depth.**
- Remaining sources from DESIGN.md (TechCrunch, indie-hacker, etc.)
- Topic graph + quiz revision
- PDF / markdown export of a day's briefs
- Multi-tenant: add nullable `owner_id` if/when needed

---

## 10. Defaults baked into v0

These were open questions; the answers below ship with v0.

- **API key**: read `ANTHROPIC_API_KEY` from `.env`. Empty → Ollama
  fallback. No circuit breaker in v0 (add when there's real budget to
  protect).
- **Reddit auth**: public `.json` endpoints, no PRAW, no credentials.
- **Auto-mute threshold**: 3 negative feedbacks in 7 days, scoped per
  source × per lens.
- **Frontend cutover**: yes, in v0. Fixtures deleted.
- **Multi-tenant**: deferred. No `owner_id` columns yet.
- **Onboarding**: the four lenses are seeded with editable template
  theses. Real onboarding wizard is v1.
- **Daily brief cap**: 7 total, 0–4 per lens, adaptive.
