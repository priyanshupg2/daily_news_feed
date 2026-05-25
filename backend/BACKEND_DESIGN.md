# Prism backend — system design

> Companion to `DESIGN.md`. Where this contradicts the original, this wins;
> where it stays silent, the original holds.

This document picks up after the design system landed and the lens model
became the product's organizing idea. DESIGN.md predates that. The backend
schema is already there in skeleton form, but no pipeline runs end to end —
no sources are wired, no annotator exists, no merger, no claim extractor.
This is the plan for the slice that gets us from "nothing on screen" to
"five briefs, lens-tagged, with traceable claims, generated against your
thesis" — and the questions you need to answer before I build it.

---

## 1. Where we are

What already exists in `backend/`:

- **Schema**: items, item_annotations, topic_clusters, feed_items,
  generated_content, user_profile, user_preferences, knowledge_log, plus
  the three feedback tables and a user_prompts table. Indexes in place.
- **Pydantic models** for each entity in `db/models.py`.
- **`DiscoveryEngine`** in `discovery/engine.py`: takes sources via DI,
  fetches them, stores items with dedup on `(source, source_id)`. Works.
- **`OllamaProvider`** in `llm/ollama.py`: completes JSON and free text
  against a local Ollama server. Works against the contract in `provider.py`.
- **FastAPI app** in `main.py` with router stubs (`feed`, `profile`,
  `feedback`, `raw_data`) — every endpoint returns a placeholder.

What is missing:

- No registered sources. `discovery/sources/` only holds the protocol.
  arXiv, HN, Reddit fetchers haven't been written.
- No annotator, clusterer, merger, ranker, content generator. The two
  intelligence layers are entirely unimplemented.
- No Claude or OpenAI provider — only Ollama.
- No scheduler. APScheduler is in pyproject but nothing schedules.
- No tests.
- The endpoints don't read or write anything real.

And the mismatch that drove this document: DESIGN.md models the user as
**one person with one set of goals**. The frontend that just shipped
commits to the **lens model** — Founder, Engineer, Researcher, plus
Operator and Investor in the spectrum. Each lens is a distinct identity
view with its own thesis, its own relevance bar, its own knowledge state.
The schema does not yet reflect this. The first decision is how to fix it.

---

## 2. The lens model — what changes in the schema

One human user. Multiple **lenses** under that user. Each lens is a saved
persona with its own thesis, working topics, learning topics, and feedback
history. Relevance is identity-relative — the same arXiv paper is a 0.9
for Researcher and a 0.1 for Founder — so annotation, ranking, and merging
are lens-conditioned. Clusters stay lens-agnostic (a fact about the world
is a fact about the world); a single cluster can produce up to one brief
per lens that finds it relevant, with lens-specific framing.

Schema delta (additive — no destructive migration):

```sql
CREATE TABLE lenses (
    id TEXT PRIMARY KEY,                   -- 'founder', 'engineer', ...
    name TEXT NOT NULL,                    -- display name
    accent_token TEXT NOT NULL,            -- 'lens-founder' (frontend CSS var)
    thesis TEXT,                           -- "agentic workflows for SMB payroll in India"
    working_topics TEXT,                   -- JSON
    learning_topics TEXT,                  -- JSON
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Annotation becomes (item, lens). UNIQUE(item_id) → UNIQUE(item_id, lens_id).
ALTER TABLE item_annotations ADD COLUMN lens_id TEXT REFERENCES lenses(id);

-- A brief belongs to one lens.
ALTER TABLE feed_items ADD COLUMN lens_id TEXT REFERENCES lenses(id);

-- Knowledge and preferences are per-lens.
ALTER TABLE knowledge_log ADD COLUMN lens_id TEXT REFERENCES lenses(id);
ALTER TABLE user_preferences ADD COLUMN lens_id TEXT REFERENCES lenses(id);
-- UNIQUE(topic_tag, lens_id)

-- Claims are first-class. The brand promise is traceability — claims with
-- citations should not live as JSON inside summary.
CREATE TABLE brief_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id),
    n INTEGER NOT NULL,                    -- 1-based display order
    text TEXT NOT NULL,                    -- "Round closed in *nine days*..."
    source_item_id TEXT REFERENCES items(id),  -- the primary source
    citation_text TEXT,                    -- "theinformation.com · funding desk · ¶3"
    confidence REAL,                       -- model confidence 0..1
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_item_id, n)
);

CREATE TABLE brief_claim_corroborations (
    claim_id INTEGER NOT NULL REFERENCES brief_claims(id),
    item_id TEXT NOT NULL REFERENCES items(id),
    PRIMARY KEY (claim_id, item_id)
);

-- The frontend already says "3 sources auto-muted this week". Model it.
CREATE TABLE muted_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,                 -- domain, subreddit, author
    pattern_type TEXT NOT NULL,            -- 'domain' | 'subreddit' | 'author'
    lens_id TEXT REFERENCES lenses(id),    -- NULL = mute globally
    reason TEXT,                           -- 'auto' or free text
    muted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

`user_profile` stays — it holds the human's top-level goals and email,
which sit above the lenses.

---

## 3. The pipeline

Five steps. The first three run in batch, the last two are also batch but
can be re-run on demand. Each step has a clear contract so we can replace
or extend pieces in isolation.

```
discovery → annotation → clustering → per-lens merge + claim extract → ranking
   (I/O)    (LLM, per lens)   (LLM)     (LLM, per lens × cluster)      (cheap)
```

### 3.1 Discovery (`discovery/sources/`)

Three sources in v0:

- **arXiv** — REST API, cs.AI / cs.LG / cs.CL categories. Daily diff.
  Polite UA + 3s between batches. No auth.
- **Hacker News** — Algolia API. Fetch front-page + stories with score
  threshold from the last 24h. No auth, no rate limit issue.
- **Reddit** — PRAW against r/MachineLearning, r/LocalLLaMA. Read-only
  app credentials in `.env` (the only Reddit-side auth we need).

Each source is one file under `discovery/sources/` implementing the
`Source` protocol. Progressive fetching is just "run discovery every two
hours instead of once at 6 AM" — handled by the scheduler, not by the
source. Drives `items` table growth throughout the day.

### 3.2 Annotation (`intelligence/annotator.py`)

For each (new item, active lens) pair, call the LLM with:

- The item (title, content, source metadata)
- The lens (thesis, working topics, learning topics)
- The user's last K annotation corrections for this lens (cached system
  prompt; this is how the model learns from feedback without retraining)

Output is a JSON object:
```json
{
  "relevance_score": 0.0..1.0,
  "quality_score": 0.0..1.0,
  "novelty_score": 0.0..1.0,
  "importance_score": 0.0..1.0,
  "topic_tag": "snake_case_normalized",
  "rationale": "one sentence, used only for raw-data browser tooltip"
}
```

Concurrency capped at 8 parallel calls. Items below
`relevance_score < 0.2 AND importance_score < 0.4` get marked but not
clustered — they're still visible in the raw-data browser.

### 3.3 Clustering (`intelligence/clusterer.py`)

Group annotated items by `topic_tag` within the last 24h. Cheap.

Optionally, run a second LLM pass over close-but-not-identical tags
(`flash_attention_3` and `flash_attn_v3`) to merge them — once per day,
on the full tag list. This is where the "100 tweets about Open Claw" case
gets handled.

### 3.4 Merge + claim extract (`intelligence/merger.py`)

For each `(lens, cluster)` where any item in the cluster has
`relevance_score ≥ 0.5` for that lens:

- Feed the merged text of the top 5-8 items to the LLM along with the
  lens context.
- Generate: `title`, `lead`, `why_it_matters`, and **claims** — numbered
  statements, each pinned to one primary `source_item_id` with a
  citation string.
- Store as a `feed_items` row + N `brief_claims` rows.

This is the most editorial step. It's where the brand voice is enforced
(see §6). Use Opus here; the quality difference shows up in this step
more than anywhere else.

### 3.5 Ranking (`intelligence/ranker.py`)

For each lens, score every brief from §3.4:

```
final_rank = 0.4 * relevance + 0.2 * importance + 0.2 * novelty
           + 0.1 * quality   + 0.1 * preference_weight(topic_tag, lens)
```

Top-K per lens (default 2 each across 3 active lenses = ~6 briefs total,
matching what the frontend renders). Lenses with no eligible briefs
contribute zero — no padding with weak signals.

---

## 4. LLM strategy

- **Default**: Claude. Annotation → Sonnet 4.6 (fast, cheap, sufficient
  for scoring). Merge + claim extract → Opus 4.7 (this is where editorial
  voice and citation precision pay off).
- **Fallback**: Ollama. Auto-engaged if `LLM_API_KEY` is empty. Same
  contract — `complete` / `complete_json`. Lower-fidelity output, fine
  for dev.
- **Prompt caching**: brand voice block + lens definitions + recent
  annotation corrections sit in the cached portion of the system prompt.
  Per-item content is the dynamic part. This pays off in the annotation
  pass where we make hundreds of calls with the same system context.
- **Concurrency**: `asyncio.Semaphore(8)` on the LLM client. Honors
  Anthropic rate limits at the default org tier.

Provider classes go in `llm/claude.py` and `llm/openai_provider.py`.
The factory in `llm/provider.py` already has the switch case stubbed.

---

## 5. API shape

The endpoints DESIGN.md already lists, with lens added where it matters:

```
GET  /api/feed?date=2026-05-25&lens=founder     # one lens; omit param → all
GET  /api/feed/:brief_id                         # one brief incl. claims
POST /api/feed/refresh                           # re-run pipeline now
POST /api/feed/:brief_id/generate                # explainer/discussion on demand
                                                 # body: {mode: "explainer_basics"}
POST /api/feed/:brief_id/read                    # mark read + time spent

GET  /api/raw?date=...&lens=...&source=...&topic=...
POST /api/feedback/item                          # like / dislike / save / mute
POST /api/feedback/annotation
POST /api/prompt                                 # "more CUDA this week"

GET  /api/lenses                                 # list + active state
POST /api/lenses                                 # create a new one
PUT  /api/lenses/:id                             # edit thesis / topics
DELETE /api/lenses/:id                           # archive (keeps history)

GET  /api/profile
PUT  /api/profile
GET  /api/profile/onboarding-needed
GET  /api/profile/knowledge?lens=...
GET  /api/profile/preferences?lens=...
```

`GET /api/feed` returns a shape the existing frontend already consumes —
`{briefs: [{id, lens, title, lead, why, source_count, read_min, sources,
claims}]}`. The fixtures in `frontend/src/app/_brief/data.ts` get replaced
by a server fetch.

---

## 6. Voice enforcement

Every LLM prompt that produces user-visible text gets the same system
fragment, cached:

```
Write in Prism's voice: editorial, precise, slightly dry, never breathless.
Direct address — "you", never "we" or "users". Verbs do the work: reads,
extracts, verifies, tunes, mutes. No hype adjectives — revolutionary,
game-changing, seamless, AI-powered, intelligent. Sentence case. Em-dashes
to set off clauses. No emoji, no unicode pictograms.

Vocabulary: lens, brief, signal, noise, source, claim, thesis.
Never: channel, feed, digest, newsletter, summary, hits, citation, link,
interests.

Length: lead ≤ 280 chars, why_it_matters ≤ 320 chars, each claim ≤ 200 chars.
```

The merger also gets a few-shot block of canonical brand copy lifted from
the design-system README, cached. This is the single highest-leverage
prompt in the system.

---

## 7. Use cases

### UC-1 — Morning brief generation (06:00, daily)

Scheduler kicks the pipeline. Discovery has been running every 2h since
the prior morning, so `items` has the last 24h of raw signal. Annotator
walks new items × active lenses, scoring each. Clusterer groups by
`topic_tag` and merges near-duplicates. Merger produces lens-conditioned
briefs with extracted claims, each claim citing the exact item it came
from. Ranker picks the top six across lenses. Frontend at 06:01 fetches
`/api/feed?date=today` and renders.

### UC-2 — Reader expands a brief

User taps the brief title. Frontend already has the claims — no extra
fetch. Each claim shows its primary source as a citation chip. Tapping
the chip opens the original item in a new tab (URL stored on `items`).
The "+ N more" link below the title opens the full source list panel.

### UC-3 — Reader corrects an annotation

In the raw-data browser, a user disagrees with how a paper was scored —
relevance 0.2 for Engineer, but it's actually 0.8. They post that
correction. It lands in `feedback_annotations`. Next time annotation runs
for that lens, the last 30 corrections get included in the cached system
prompt: "User previously corrected: item about flash-attention scored
0.2, user says 0.8 — calibrate accordingly." Crude, but it's the cheapest
way to teach the model without fine-tuning.

### UC-4 — Free-text prompt: "more CUDA this week"

User types it. Parser extracts intent (boost) + topic (cuda). Stored as a
`user_prompts` row with effect
`{"action": "boost", "topic_tag": "cuda", "lens_id": "engineer", "ttl": "7d"}`.
Ranker applies the boost as an additive term in the final rank for the
TTL window. Effect is logged so the user can see what was done.

### UC-5 — Auto-mute kicks in

A user dislikes three items from `substack.com/some-vc-newsletter`
within seven days. A background task notices the streak and writes a
`muted_sources` row scoped to the relevant lens. Future items from that
domain skip clustering for that lens (still visible in raw data). The
endnote on the brief reads "3 sources auto-muted this week" — that
number is `SELECT COUNT(*) FROM muted_sources WHERE muted_at > now() - 7d
AND reason = 'auto'`.

### UC-6 — Adding a fourth lens

User goes to profile, taps "Add lens", picks Operator. Onboarding asks
for a thesis ("2-3 sentences about what you're trying to figure out
under this hat"), working topics, learning topics. Saved as a new
`lenses` row. The next discovery run is unchanged; the next annotation
run also scores items against the new lens. The frontend lens switcher
picks up the new lens via `GET /api/lenses` and renders it with its
accent color.

---

## 8. Features by phase

**v0 — the slice that replaces the fixtures and proves the pipeline.**
- Lens CRUD + onboarding
- arXiv + HN + Reddit sources (real, running)
- Claude provider (Sonnet for annotation, Opus for merge)
- Annotation per (item, lens) with rationale
- Clustering by topic_tag
- Merge + claim extraction per (lens, cluster)
- Ranking + top-K selection
- Feed + raw-data endpoints backing the frontend
- Scheduler running every 2h discovery, daily 6 AM pipeline

**v1 — feedback closes the loop, on-demand modes light up.**
- Feedback endpoints actually update preferences
- Annotation correction included in next annotation run
- Free-text prompts (boost/suppress)
- Auto-mute heuristic
- Explainer (basics, delta) and Discussion on-demand modes
- Reading-history-driven proficiency model

**v2 — depth.**
- The remaining seven sources from DESIGN.md
- Cross-lens synthesis: when a cluster scores high for ≥ 2 lenses, a
  small "Also relevant to your Engineer lens →" affordance on the
  founder brief
- Topic graph + quiz revision
- PDF / markdown export of a day's briefs

---

## 9. Open questions — need your call before I build

1. **Lens reconciliation.** Confirmed: single human user, multiple
   lenses, per-lens annotation + ranking + merge? Or do you want
   something simpler — one annotation per item, lens is just a filter on
   already-scored items? My read: per-lens annotation is the right
   architecture given the brand promise; the cost is roughly Nx more LLM
   calls in the annotation step, but Sonnet is cheap and prompt caching
   takes most of it back.

2. **Daily brief cap.** DESIGN.md says 5 per day. Frontend currently
   shows ~5 across lenses. Cap at 5 per lens or 5 total? My pick: 5-7
   total, allocated across active lenses by recent engagement, no minimum
   per lens (a quiet lens gets 0 briefs on a quiet day rather than
   padded ones).

3. **Claim extraction model.** Opus 4.7 for merge + claim extraction is
   the right quality (this is where the citations have to be precise and
   the voice has to land). It's also the most expensive step. OK to
   default to Opus, or hold to Sonnet and revisit?

4. **Time-of-day refresh.** Brand copy shows "REFRESHED 12:00", "18:00".
   Three reads of this: (a) cosmetic only — the paper changes color, the
   timestamp is the original 06:00; (b) midday re-rank — same briefs,
   maybe reordered by what the user hasn't read yet; (c) midday
   regenerate — fresh discovery + fresh briefs at noon and again at
   18:00. (a) is free, (b) is cheap, (c) is what the copy implies. My
   pick: (b) by default, (c) opt-in.

5. **Auto-mute heuristic.** I proposed three dislikes in seven days from
   the same source. Acceptable, or do you want stricter (five) / looser
   (two)? Auto-mute is scoped per-lens by default — global mute is
   user-only.

6. **Reddit auth.** PRAW needs a Reddit app's client_id + secret +
   user_agent. Will you create one, or do you want me to fall back to
   their public JSON endpoints (lower quality, rate-limited but
   keyless)?

7. **Frontend cutover.** v0 ends with `data.ts` deleted and the brief
   list fetched from `/api/feed`. Confirm you want that as part of v0,
   not deferred. (I'd recommend yes — otherwise the pipeline is
   un-demoable.)

8. **Multi-tenant later?** DESIGN.md is single-user. The schema works
   for that today. If multi-tenant lives in the future, the cheap
   forward-compatibility move is a nullable `owner_id` on the top-level
   tables now. Worth doing or premature?

9. **What's the Claude API key budget?** Annotation per lens is the cost
   driver. Rough math at default tier: 100 items/day × 3 lenses × Sonnet
   ≈ small. Merge: 15 clusters × Opus ≈ noticeable. Tell me a monthly
   ceiling and I'll wire the LLM client to track spend and circuit-break
   at the limit.

Answer any subset of these and I'll start building. The order I'd
recommend: 1, 9, 6 are blockers; 3, 4, 5 can be flipped later without
rework; 2, 7, 8 are policy and don't change the architecture.
