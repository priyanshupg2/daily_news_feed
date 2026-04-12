# Daily News Feed Agent — Design Document

## Context

In fast-moving fields (AI, ML, inference engineering), the cognitive overhead of finding, filtering, understanding, and retaining relevant information is the real problem — not lack of information. This agent solves that by discovering, merging, ranking, and presenting knowledge tailored to the user’s goals.

**GitHub repo**: priyanshupg2/daily_news_feed

---

## Requirements (Finalized)

### R1: Discovery Engine (Data Lake)
The discovery layer runs **independently** from intelligence. Its job is to exhaustively fetch and store ALL data from all sources every day. This is a data lake — we never lose raw data.

**Storage model**: `date → source → documents`

**Fetching strategy**: Progressive fetching throughout the day to avoid throttling. Not a single burst.

**10 sources** (3 in MVP, rest in v2):

| Source | Signal Type | API | Phase |
|--------|-----------|-----|-------|
| arXiv cs.LG / cs.CL / cs.AI | Latest papers | Free REST | **MVP** |
| HN Algolia | Community-vetted tech news | Free, no key | **MVP** |
| Reddit r/MachineLearning, r/LocalLLaMA | Community discussion | PRAW | **MVP** |
| Twitter/X | Researcher posts, announcements | API | v2 |
| GitHub trending | Repos, tools for inference eng | Scrape/API | v2 |
| Conference proceedings (NeurIPS, ICML, ACL) | High-signal seasonal papers | Scrape | v2 |
| Curated blogs (Lilian Weng, Jay Alammar, Chip Huyen) | Deep technical writing | RSS | v2 |
| Semantic Scholar | Influential papers, citations | Free REST | v2 |
| Google News RSS | Company/product news | Free RSS | v2 |
| NewsData.io | Broader tech news | Free tier | v2 |

### R2: Topic Merging (Critical Differentiator)
Multiple articles/tweets about the same topic (e.g., 100 tweets about “Open Claw”) get merged into **1 consolidated topic-card** with:
- Synthesized summary from all sources
- “Why it matters” tied to user’s goals
- Links to best 3-5 original sources
- Source count (e.g., “12 sources merged”)

### R3: User Profile & Knowledge Tracking
- **Onboarding**: Ask user 3 learning goals (with examples) + working topics + topics to learn
- **Knowledge profile builds passively from reading**: As user reads content, we track what they consumed and build their knowledge profile from that. “User has read 5 articles on Flash Attention → proficiency: intermediate”
- **Interest model builds from feedback** (likes/dislikes/text)
- **Free-text feedback field** always available
- Profile editable anytime

### R4: Two-Layer Intelligence Pipeline

**This is NOT one step. It’s two distinct layers:**

#### Layer 1: Annotation (runs on ALL raw items)
Every raw item gets annotated with:
- `relevance_score` — how relevant to user’s goals
- `quality_score` — citations, upvotes, source authority
- `novelty_score` — is this genuinely new vs. rehash
- `importance_score` — should user see this even if not “interesting”
- `topic_tag` — what topic cluster this belongs to

**User can see all raw annotated data** and provide feedback on the annotations themselves (“this was marked low relevance but it’s actually very relevant to me”). This feedback improves future annotations.

#### Layer 2: Ranking + Merging (produces the feed)
Takes annotated items and:
1. Groups by `topic_tag` into clusters
2. Merges each cluster into 1 consolidated card
3. Reranks clusters by combined score
4. Selects top 5 cards

### R5: Presentation — 4 Modes + Generation Timing

#### When does content generation happen?
- **Feed cards** (summary + “why it matters”): Generated in Layer 2 when merging clusters. Stored in DB.
- **Explainer content**: Generated **on-demand** when user clicks into a card OR switches to explainer mode. NOT pre-generated (too expensive for all 5 cards × all modes).
- **Discussion/debate**: Also on-demand when user selects this mode.

#### The 4 modes:
Agent **auto-selects** default mode. User can **switch** per card.

1. **News (bullet points)** — Default for most items. Title + 1-line + “why it matters”. Quick scan.
2. **Explainer (from basics)** — For new/unfamiliar topics. Builds from ground up. Generated on-demand.
3. **Explainer (delta only)** — For known topics. Only what’s new on top of user’s knowledge profile. Generated on-demand.
4. **Discussion/Debate** — For controversial/multi-sided topics. Pros/cons. Generated on-demand.

### R6: Daily Volume
- **Max 5 high-density topic-cards** per day in the main feed
- Each card backed by multiple merged sources
- All raw annotated data browsable separately

### R7: Feedback System — Data Model

#### What gets stored:

```
feedback_on_items:
  feed_item_id → {action, comment, timestamp}
  actions: like, dislike, more_like_this, less_like_this, too_basic, too_advanced, save

feedback_on_annotations:
  item_id → {field, user_score, comment, timestamp}
  e.g., "item_123, relevance, 0.9, 'this is very relevant to my CUDA work'"

user_prompts:
  prompt_text → {timestamp, processed}
  e.g., "more about CUDA kernels this week"

reading_history:
  feed_item_id → {read_at, time_spent_seconds, expanded_to_mode}
  Used to build knowledge profile passively
```

#### How preferences update:

1. **Explicit feedback** (like/dislike) → directly adjusts topic interest weights
2. **Annotation feedback** → retrains annotation model (LLM prompt includes past corrections)
3. **Reading behavior** → builds knowledge profile (topics read = topics known)
4. **Prompts** → temporarily boost/suppress topics in next run
5. **Preference model** = `{topic → {interest_weight, proficiency_level, last_feedback}}` stored in `user_preferences` table, updated after each interaction

### R8: Knowledge Management (v2)
- Notes auto-generated from daily feed, stored as markdown, editable by user
- Revision: topic-based quiz tied to recently discussed topics
- Topic graph linking related concepts

### R9: LLM Layer
- Abstracted behind `LLMProvider` interface — model-agnostic
- Start with open-source (Ollama with Llama/Mistral locally)
- Swap to Claude/GPT/any model via config

---

## High-Level Design (HLD)

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       NEXT.JS FRONTEND                        │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Feed    │ │ Raw Data  │ │ Onboard  │ │ Profile +     │  │
│  │  (5 cards)│ │ Browser   │ │  Flow    │ │ Preferences   │  │
│  └──────────┘ └───────────┘ └──────────┘ └───────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST API
┌──────────────────────┴───────────────────────────────────────┐
│                   PYTHON BACKEND (FastAPI)                     │
│                                                               │
│  ┌── DISCOVERY (independent, runs throughout day) ──────────┐│
│  │  arXiv │ HN │ Reddit │ [v2: +7 sources]                 ││
│  │  → Progressive fetch → Store ALL in items table          ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│  ┌── LAYER 1: ANNOTATION (runs on all raw items) ──────────┐│
│  │  For each item: score relevance, quality, novelty,       ││
│  │  importance, assign topic_tag                             ││
│  │  → Store annotations in item_annotations table           ││
│  │  → User can browse + give feedback on annotations        ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│  ┌── LAYER 2: RANKING + MERGING (produces daily feed) ─────┐│
│  │  1. Group by topic_tag → clusters                        ││
│  │  2. Merge cluster → 1 card (summary + why_it_matters)    ││
│  │  3. Rerank by combined score                              ││
│  │  4. Select top 5 → feed_items table                      ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│  ┌── ON-DEMAND GENERATION ──────────────────────────────────┐│
│  │  User clicks "Explainer" → generate explainer content    ││
│  │  User clicks "Discussion" → generate debate content      ││
│  │  Cached after first generation                            ││
│  └──────────────────────────────────────────────────────────┘│
│                                                               │
│  ┌── LLM PROVIDER ─────┐  ┌── SCHEDULER ────────────────┐│
│  │  Ollama (default)    │  │  Discovery: progressive/daily  ││
│  │  Claude (swap)       │  │  Annotation: after discovery   ││
│  │  OpenAI (swap)       │  │  Ranking: daily 6 AM           ││
│  └──────────────────────┘  │  On-demand: user trigger       ││
│                             └────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │    SQLite DB    │
              │   (single file) │
              └─────────────────┘
```

### Data Flow — Timing

```
THROUGHOUT THE DAY:
  Discovery fetches progressively → items table grows
  (Avoids throttling, keeps data fresh)

DAILY 6 AM (or on-demand):
  Layer 1: Annotate all new items since last run
    → item_annotations table
  Layer 2: Cluster → Merge → Rank → Top 5
    → topic_clusters + feed_items tables

USER OPENS APP:
  Sees 5 topic-cards (news mode by default)
  Can browse raw annotated data separately
  Clicks "Explainer" on a card → on-demand LLM generation → cached
  Gives feedback → updates preferences + annotation corrections
  Reading tracked → builds knowledge profile
```

---

## Low-Level Design (LLD)

### Database Schema (SQLite)

```sql
-- ═══════════════════════════════════════
-- DATA LAKE: Raw items from all sources
-- ═══════════════════════════════════════
CREATE TABLE items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,              -- 'arxiv', 'hn', 'reddit'
    source_id TEXT,                    -- original ID from source
    title TEXT NOT NULL,
    url TEXT,
    content TEXT,                      -- abstract, body, etc.
    authors TEXT,                      -- JSON array
    published_at DATETIME,
    fetch_date DATE NOT NULL,          -- partition key: which day we fetched this
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                     -- JSON: citations, score, subreddit, etc.
    UNIQUE(source, source_id)
);
CREATE INDEX idx_items_fetch_date ON items(fetch_date);
CREATE INDEX idx_items_source ON items(source, fetch_date);

-- ═══════════════════════════════════════
-- LAYER 1: Annotations on raw items
-- ═══════════════════════════════════════
CREATE TABLE item_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id),
    relevance_score REAL,              -- 0.0 to 1.0
    quality_score REAL,
    novelty_score REAL,
    importance_score REAL,
    topic_tag TEXT,                     -- e.g., "flash_attention", "open_claw"
    annotated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,                     -- which model produced this
    UNIQUE(item_id)
);
CREATE INDEX idx_annotations_topic ON item_annotations(topic_tag);

-- ═══════════════════════════════════════
-- LAYER 2: Topic clusters + Feed cards
-- ═══════════════════════════════════════
CREATE TABLE topic_clusters (
    id TEXT PRIMARY KEY,
    topic_label TEXT NOT NULL,          -- "Flash Attention 3 Released"
    topic_tag TEXT NOT NULL,            -- normalized tag
    item_ids TEXT NOT NULL,             -- JSON array of item IDs
    source_count INTEGER,
    feed_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feed_items (
    id TEXT PRIMARY KEY,
    cluster_id TEXT REFERENCES topic_clusters(id),
    final_rank REAL,
    presentation_mode TEXT NOT NULL DEFAULT 'news',
    summary TEXT NOT NULL,
    why_it_matters TEXT,
    source_links TEXT,                  -- JSON: [{url, title, source}]
    feed_date DATE NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    time_spent_seconds INTEGER,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_feed_date ON feed_items(feed_date);

-- On-demand generated content (explainer, discussion)
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT REFERENCES feed_items(id),
    mode TEXT NOT NULL,                 -- 'explainer_basics', 'explainer_delta', 'discussion'
    content TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_model TEXT,
    UNIQUE(feed_item_id, mode)
);

-- ═══════════════════════════════════════
-- USER: Profile + Preferences + Knowledge
-- ═══════════════════════════════════════
CREATE TABLE user_profile (
    id TEXT PRIMARY KEY DEFAULT 'default',
    goals TEXT NOT NULL,                -- JSON: ["be a great SWE", "research scientist in LLMs", ...]
    working_topics TEXT,                -- JSON: ["model inference", "CUDA kernels"]
    learning_topics TEXT,               -- JSON: ["RLHF", "diffusion models"]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Per-topic preference weights (evolves from feedback)
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag TEXT NOT NULL UNIQUE,
    interest_weight REAL DEFAULT 0.5,   -- 0.0 (suppress) to 1.0 (boost)
    proficiency_level TEXT DEFAULT 'beginner', -- beginner, intermediate, advanced, expert
    articles_read INTEGER DEFAULT 0,
    last_feedback_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge profile (built passively from reading)
CREATE TABLE knowledge_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag TEXT NOT NULL,
    feed_item_id TEXT REFERENCES feed_items(id),
    action TEXT NOT NULL,               -- 'read', 'expanded_explainer', 'expanded_discussion'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Proficiency auto-calculated: count of reads per topic → beginner(<3), intermediate(3-10), advanced(10+)

-- ═══════════════════════════════════════
-- FEEDBACK
-- ═══════════════════════════════════════

-- Feedback on feed cards
CREATE TABLE feedback_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id TEXT NOT NULL REFERENCES feed_items(id),
    action TEXT NOT NULL,               -- 'like', 'dislike', 'more_like_this', 'less_like_this', 'too_basic', 'too_advanced', 'save'
    comment TEXT,                       -- free-text
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feedback on annotations (user corrects the AI's scoring)
CREATE TABLE feedback_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES items(id),
    field TEXT NOT NULL,                -- 'relevance', 'quality', 'novelty', 'importance', 'topic_tag'
    original_value TEXT,                -- what the AI scored
    user_value TEXT,                    -- what the user thinks it should be
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User free-text prompts ("more CUDA this week")
CREATE TABLE user_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    effect TEXT,                        -- JSON: what the system did with this prompt
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Preference Update Logic

```
On LIKE/DISLIKE feed item:
  1. Get topic_tag from the card's cluster
  2. Update user_preferences.interest_weight for that topic
     - like → weight += 0.1 (cap at 1.0)
     - dislike → weight -= 0.1 (floor at 0.0)
  3. Log to knowledge_log

On "too basic" / "too advanced":
  1. Adjust user_preferences.proficiency_level for that topic
     - too_basic → promote proficiency (beginner → intermediate)
     - too_advanced → demote proficiency

On ANNOTATION FEEDBACK:
  1. Store correction in feedback_annotations
  2. Next annotation run includes past corrections in LLM prompt:
     "User previously corrected: item about X was scored 0.2 relevance but user says 0.9"
  3. LLM learns from corrections

On READING:
  1. Mark feed_item.is_read, record time_spent
  2. Log to knowledge_log
  3. Recalculate proficiency: count reads per topic
     <3 reads → beginner, 3-10 → intermediate, 10+ → advanced

On USER PROMPT:
  1. Parse intent (e.g., "more CUDA" → boost topic weight temporarily)
  2. Store effect in user_prompts.effect
  3. Next ranking run applies boost
```

### LLM Abstraction

```python
class LLMProvider(Protocol):
    async def complete(self, prompt: str, system: str = "") -> str: ...
    async def complete_json(self, prompt: str, system: str = "", schema: dict = None) -> dict: ...

class OllamaProvider(LLMProvider): ...    # Default — free, local
class ClaudeProvider(LLMProvider): ...    # Swap via config
class OpenAIProvider(LLMProvider): ...    # Or this
```

### Project Structure

```
daily_news_feed/
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Settings (env vars, LLM config)
│   │   ├── db/
│   │   │   ├── database.py         # SQLite connection + init
│   │   │   └── models.py           # Pydantic models
│   │   ├── llm/
│   │   │   ├── provider.py         # LLMProvider protocol
│   │   │   ├── ollama.py
│   │   │   ├── claude.py
│   │   │   └── openai_provider.py
│   │   ├── discovery/
│   │   │   ├── engine.py           # Orchestrator (progressive fetch)
│   │   │   └── sources/
│   │   │       ├── base.py         # Source protocol
│   │   │       ├── arxiv.py
│   │   │       ├── hackernews.py
│   │   │       └── reddit.py
│   │   ├── intelligence/
│   │   │   ├── annotator.py        # Layer 1: score + tag all items
│   │   │   ├── clusterer.py        # Layer 2: group by topic
│   │   │   ├── merger.py           # Layer 2: cluster → 1 card
│   │   │   ├── ranker.py           # Layer 2: rerank + select top 5
│   │   │   └── content_gen.py      # On-demand: explainer, discussion
│   │   ├── profile/
│   │   │   ├── preferences.py      # Preference update logic
│   │   │   ├── knowledge.py        # Knowledge profile from reading
│   │   │   └── onboarding.py       # First-run flow
│   │   ├── api/
│   │   │   ├── feed.py             # Feed endpoints
│   │   │   ├── raw_data.py         # Browse raw annotated data
│   │   │   ├── profile.py          # Profile + onboarding
│   │   │   └── feedback.py         # All feedback endpoints
│   │   └── scheduler/
│   │       └── jobs.py             # Cron: discovery, annotation, ranking
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Feed view (5 cards)
│   │   │   ├── raw/
│   │   │   │   └── page.tsx        # Browse all annotated raw data
│   │   │   ├── onboarding/
│   │   │   │   └── page.tsx
│   │   │   └── profile/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── TopicCard.tsx
│   │   │   ├── FeedbackBar.tsx
│   │   │   ├── ModeToggle.tsx
│   │   │   ├── AnnotationViewer.tsx  # View/correct annotations
│   │   │   └── PromptInput.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   └── public/
├── .env.example
└── README.md
```

### API Endpoints

```
# Feed (5 daily cards)
GET  /api/feed?date=2026-04-12        # Today's 5 topic-cards
GET  /api/feed/:id                     # Single card detail
POST /api/feed/refresh                 # Trigger full pipeline on-demand
POST /api/feed/:id/generate            # Generate explainer/discussion on-demand
                                       # body: {mode: "explainer_basics"}

# Raw Data (browse all annotated items)
GET  /api/raw?date=2026-04-12          # All items for a date with annotations
GET  /api/raw?date=...&source=arxiv    # Filter by source
GET  /api/raw?date=...&topic=flash_attn # Filter by topic

# Feedback
POST /api/feedback/item                # Feedback on feed card
POST /api/feedback/annotation          # Correct an annotation
POST /api/prompt                       # Free-text prompt

# Profile
GET  /api/profile
PUT  /api/profile
GET  /api/profile/onboarding-needed
GET  /api/profile/knowledge            # View knowledge profile (auto-built)
GET  /api/profile/preferences          # View topic preference weights
```

---

## MVP Implementation Phases

### Phase 1: Scaffolding
- Python backend (FastAPI + uv)
- Next.js frontend (App Router + Tailwind)
- SQLite DB init with full schema
- LLM provider abstraction (Ollama default)
- Push to GitHub via MCP

### Phase 2: Discovery Engine
- arXiv, HN, Reddit fetchers with progressive scheduling
- Store ALL items in `items` table (date partitioned)
- Dedup by source + source_id

### Phase 3: Intelligence — Layer 1 (Annotation)
- Annotate all raw items: relevance, quality, novelty, importance, topic_tag
- Store in `item_annotations`
- Include user's past annotation corrections in LLM prompt

### Phase 4: Intelligence — Layer 2 (Ranking + Merging)
- Cluster by topic_tag
- Merge each cluster → 1 card with summary + why_it_matters
- Rank clusters, select top 5
- Store in `topic_clusters` + `feed_items`

### Phase 5: Profile + Feedback
- Onboarding flow (3 goals + topics)
- Preference update logic (likes → weight changes, reads → knowledge)
- Annotation feedback (user corrects scores)
- Free-text prompts

### Phase 6: API + Frontend
- All endpoints listed above
- Feed page (5 cards), raw data browser, profile page
- On-demand content generation (explainer/discussion)
- Feedback UI on every card + annotation correction UI

### Phase 7: Scheduler
- Discovery: progressive throughout day
- Annotation: after discovery batch completes
- Ranking: daily 6 AM
- On-demand: user trigger

### Verification
- Discovery: all 3 sources store items correctly, dedup works
- Annotation: every item gets scored, topic tagged
- Raw browser: can see all annotated items, filter by source/topic/date
- Clustering: related items grouped correctly
- Merging: coherent consolidated cards
- Feed: 5 cards render, mode toggle works
- On-demand generation: explainer generates and caches
- Feedback: item feedback updates preferences, annotation feedback stored
- Knowledge: reading history builds proficiency automatically
- Cron: end-to-end pipeline runs daily
