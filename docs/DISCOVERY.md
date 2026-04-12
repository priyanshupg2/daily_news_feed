# Discovery — Feature Design Document

## Overview

The Discovery component is the foundation layer of the Daily News Feed system. It **fetches**, **stores**, and **serves** raw items from external sources. It operates independently from the intelligence pipeline — its only job is to exhaustively collect and retain all data.

The principle: **never lose raw data**. Every item fetched is stored permanently, partitioned by the date it was fetched. Downstream layers (annotation, ranking, merging) read from the lake but never modify it.

---

## Scope

This document covers:

1. Discovery engine — fetching items from external sources
2. Storage — persisting raw items in SQLite
3. API — serving discovery data to the frontend
4. Frontend — a drill-down crawl inspector
5. Testing — how to verify each layer

Out of scope: annotation, clustering, ranking, feed generation, LLM calls.

---

## Architecture

```
                        ┌─────────────────────────────┐
                        │      External Sources        │
                        │  arXiv  │  HN  │  Reddit     │
                        └────┬────┴───┬──┴─────┬──────┘
                             │        │        │
                      ┌──────┴────────┴────────┴──────┐
                      │       Discovery Engine         │
                      │  - Runs sources sequentially   │
                      │  - Deduplicates by             │
                      │    (source, source_id)          │
                      │  - Inserts into items table    │
                      └──────────────┬─────────────────┘
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │     SQLite — items table      │
                      │  Partitioned by fetch_date    │
                      │  WAL mode, async via aiosqlite│
                      └──────────────┬────────────────┘
                                     │
                      ┌──────────────┴────────────────┐
                      │                                │
               ┌──────┴──────┐                ┌───────┴───────┐
               │  REST API    │                │  CLI Runner    │
               │  FastAPI     │                │  python -m     │
               │  /api/       │                │  src.discovery │
               │  discovery/* │                │  .run          │
               └──────┬──────┘                └───────────────┘
                      │
               ┌──────┴──────┐
               │  Frontend    │
               │  /discovery  │
               └─────────────┘
```

---

## Folder Structure

Existing files marked with `*`. New files to create are unmarked.

```
backend/
├── pyproject.toml                           *
├── src/
│   ├── main.py                              *  FastAPI app (add /api/discovery router)
│   ├── config.py                            *  DATABASE_PATH, CORS_ORIGINS
│   │
│   ├── db/
│   │   ├── database.py                      *  get_db(), init_db(), SCHEMA_SQL
│   │   └── models.py                        *  RawItem pydantic model
│   │
│   ├── discovery/
│   │   ├── engine.py                        *  DiscoveryEngine — orchestrator
│   │   ├── run.py                           *  CLI entry point
│   │   └── sources/
│   │       ├── base.py                      *  Source protocol
│   │       ├── arxiv.py                     *  ArxivSource
│   │       ├── hackernews.py                *  HackerNewsSource
│   │       └── reddit.py                    *  RedditSource
│   │
│   └── api/
│       ├── raw_data.py                      *  (rename to discovery.py)
│       └── discovery.py                        All discovery API endpoints
│
├── tests/
│   ├── conftest.py                             Shared fixtures (test DB, client)
│   ├── fixtures/
│   │   ├── arxiv_response.xml                  Saved arXiv Atom XML
│   │   ├── hn_search_response.json             Saved HN Algolia JSON
│   │   ├── hn_frontpage_response.json          Saved HN front page JSON
│   │   └── reddit_response.json                Saved Reddit JSON
│   ├── test_arxiv_source.py                    Unit: arXiv parsing
│   ├── test_hn_source.py                       Unit: HN parsing
│   ├── test_reddit_source.py                   Unit: Reddit parsing
│   ├── test_discovery_engine.py                Integration: engine + DB
│   └── test_discovery_api.py                   API endpoint tests
│
└── data/
    └── news_feed.db                         *  SQLite database (gitignored)

frontend/
└── src/
    ├── app/
    │   └── discovery/
    │       ├── page.tsx                        Level 1: Dashboard
    │       ├── [source]/
    │       │   └── page.tsx                    Level 2: Source item list
    │       └── item/
    │           └── [id]/
    │               └── page.tsx                Level 3: Item detail
    ├── components/
    │   └── discovery/
    │       ├── SourceCard.tsx                   Source card with count
    │       └── ItemRow.tsx                      Title row in source list
    └── lib/
        ├── api.ts                           *  Add discovery API calls
        └── types.ts                         *  Add DiscoveryStats type
```

---

## Storage

### Table: `items`

Single table for all raw discovered items.

```sql
CREATE TABLE items (
    id           TEXT PRIMARY KEY,          -- sha256("source:source_id")[:16]
    source       TEXT NOT NULL,             -- 'arxiv' | 'hackernews' | 'reddit'
    source_id    TEXT,                      -- original ID from the source
    title        TEXT NOT NULL,
    url          TEXT,
    content      TEXT,                      -- abstract / selftext / story_text
    authors      TEXT,                      -- comma-separated string
    published_at DATETIME,                  -- when the source published it
    fetch_date   DATE NOT NULL,             -- the day WE fetched it (partition key)
    fetched_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata     TEXT,                      -- JSON blob, source-specific
    UNIQUE(source, source_id)
);

CREATE INDEX idx_items_fetch_date ON items(fetch_date);
CREATE INDEX idx_items_source     ON items(source, fetch_date);
```

### ID Generation

Deterministic: `sha256("source:source_id")[:16]`. Re-fetching the same item produces the same ID. The `UNIQUE(source, source_id)` constraint rejects duplicates at the DB level.

### Metadata Per Source

The `metadata` column is a JSON blob. Each source writes different fields:

**arXiv:**
```json
{
  "arxiv_id": "2401.12345v1",
  "categories": ["cs.LG", "cs.CL"],
  "primary_category": "cs.LG",
  "pdf_url": "http://arxiv.org/pdf/2401.12345v1"
}
```

**Hacker News:**
```json
{
  "hn_id": "39012345",
  "points": 342,
  "num_comments": 87,
  "story_url": "https://example.com/article",
  "hn_url": "https://news.ycombinator.com/item?id=39012345",
  "tags": ["story", "front_page"]
}
```

**Reddit:**
```json
{
  "reddit_id": "1abc2de",
  "subreddit": "MachineLearning",
  "score": 1205,
  "upvote_ratio": 0.94,
  "num_comments": 156,
  "permalink": "https://www.reddit.com/r/MachineLearning/comments/...",
  "external_url": "https://arxiv.org/abs/...",
  "is_self": false,
  "link_flair_text": "[R]",
  "domain": "arxiv.org"
}
```

### Storage Characteristics

| Property | Value |
|----------|-------|
| Engine | SQLite, WAL mode |
| Async | aiosqlite |
| Location | `data/news_feed.db` (configurable via `DATABASE_PATH`) |
| Daily volume | ~300-500 items across 3 sources |
| Row size | ~1-3 KB (title + content + metadata) |
| Retention | Permanent, never deleted |
| Partitioning | Logical via `fetch_date` column + index |

---

## Discovery Sources

### Source Protocol

```python
class Source(Protocol):
    source_name: str
    async def fetch(self) -> list[RawItem]: ...
```

### arXiv (`backend/src/discovery/sources/arxiv.py`)

| Property | Value |
|----------|-------|
| API | arXiv Atom/XML (`export.arxiv.org/api/query`) |
| Auth | None |
| Categories | `cs.LG`, `cs.CL`, `cs.AI` |
| Volume | 100 per category, ~300 total |
| Dedup | Strip arXiv version suffix (`2401.12345v2` → `2401.12345`) |
| Content | Paper abstract |

### Hacker News (`backend/src/discovery/sources/hackernews.py`)

| Property | Value |
|----------|-------|
| API | HN Algolia (`hn.algolia.com/api/v1/search`) |
| Auth | None |
| Strategy | 80 AI/ML keywords batched in OR queries + front page filter |
| Lookback | 48 hours |
| Volume | ~200 after dedup |
| Content | `story_text` (Ask HN / Show HN only) |

### Reddit (`backend/src/discovery/sources/reddit.py`)

| Property | Value |
|----------|-------|
| API | Reddit public JSON (`.json` endpoint, no OAuth) |
| Auth | None |
| Subreddits | `MachineLearning`, `LocalLLaMA`, `artificial` |
| Sort | `hot` + `top` (t=day) per sub |
| Volume | ~300 total |
| Content | `selftext` (truncated to 2000 chars) |

---

## Discovery Engine

**File**: `backend/src/discovery/engine.py`

Orchestrates sources sequentially, collects items, bulk-inserts with dedup.

### Entry Points

**CLI:**
```bash
cd backend
uv run python -m src.discovery.run               # all sources
uv run python -m src.discovery.run --source arxiv # single source
```

**API:**
```
POST /api/discovery/run
POST /api/discovery/run?source=arxiv
```

---

## API Endpoints

All endpoints mounted under `/api/discovery`.

### GET /api/discovery/stats

The dashboard endpoint. Returns per-source item counts for a given date.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `date` | `string` (YYYY-MM-DD) | today | Which fetch_date to summarize |

**Response** `200 OK`:
```json
{
  "date": "2026-04-12",
  "total": 312,
  "sources": [
    { "source": "arxiv",      "count": 156 },
    { "source": "hackernews", "count": 98 },
    { "source": "reddit",     "count": 58 }
  ],
  "latest_fetch": "2026-04-12T14:30:22"
}
```

**SQL:**
```sql
SELECT source, COUNT(*) as count
FROM items
WHERE fetch_date = ?
GROUP BY source;

SELECT MAX(fetched_at) as latest_fetch
FROM items
WHERE fetch_date = ?;
```

---

### GET /api/discovery/items

List items for a specific source and date. Used by Level 2 (source drill-down).

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `date` | `string` (YYYY-MM-DD) | no | today | Filter by fetch_date |
| `source` | `string` | **yes** | — | `arxiv`, `hackernews`, or `reddit` |
| `limit` | `int` | no | 50 | Page size (max 200) |
| `offset` | `int` | no | 0 | Pagination offset |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "a1b2c3d4e5f67890",
      "title": "Flash Attention 3: Fast and Exact Attention with IO-Awareness",
      "published_at": "2026-04-12T08:15:00+00:00"
    },
    {
      "id": "b2c3d4e5f6789012",
      "title": "Scaling Laws for Neural Language Model Pretraining",
      "published_at": "2026-04-12T06:42:00+00:00"
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

Note: this returns only `id`, `title`, and `published_at` — just enough to render a clickable list. No content, no metadata. Keeps the response small.

**SQL:**
```sql
SELECT id, title, published_at
FROM items
WHERE fetch_date = ? AND source = ?
ORDER BY published_at DESC
LIMIT ? OFFSET ?;
```

---

### GET /api/discovery/items/{item_id}

Full detail for a single item. Used by Level 3 (item detail view).

**Response** `200 OK`:
```json
{
  "id": "a1b2c3d4e5f67890",
  "source": "arxiv",
  "source_id": "2401.12345",
  "title": "Flash Attention 3: Fast and Exact Attention with IO-Awareness",
  "url": "http://arxiv.org/abs/2401.12345",
  "content": "We propose Flash Attention 3, a new algorithm that computes exact attention...",
  "authors": "Tri Dao, Daniel Y. Fu",
  "published_at": "2026-04-12T08:15:00+00:00",
  "fetch_date": "2026-04-12",
  "metadata": {
    "arxiv_id": "2401.12345v1",
    "categories": ["cs.LG", "cs.CL"],
    "primary_category": "cs.LG",
    "pdf_url": "http://arxiv.org/pdf/2401.12345v1"
  }
}
```

**Response** `404`:
```json
{ "detail": "Item not found" }
```

---

### POST /api/discovery/run

Trigger a discovery run.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | `string` | all | Run only a specific source |

**Response** `200 OK`:
```json
{
  "stored": 47,
  "message": "Discovery complete. 47 new items stored."
}
```

**Response** `409 Conflict` (already running):
```json
{ "detail": "Discovery is already running" }
```

Concurrency guard: module-level `asyncio.Lock`. If held, return 409 immediately.

---

## Frontend

The frontend is a **three-level drill-down crawl inspector**. It answers one question: "what did we fetch, and when?"

### Navigation Flow

```
/discovery                    → Level 1: Dashboard
/discovery/arxiv              → Level 2: arXiv item list
/discovery/arxiv              → Level 2: (same, paginated)
/discovery/item/a1b2c3d4...   → Level 3: Item detail
```

### Level 1: Dashboard (`/discovery`)

Pick a date, see what was fetched on that date. One card per source showing the count.

```
┌──────────────────────────────────────┐
│  Discovery                           │
│                                      │
│  Date: [◀  2026-04-12  ▶]           │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  arXiv                    156  │  │  ← click to drill in
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  Hacker News               98  │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  Reddit                    58  │  │
│  └────────────────────────────────┘  │
│                                      │
│  Total: 312 items                    │
│  Last fetched: 2:30 PM              │
│                                      │
│  [Run Discovery]                     │
└──────────────────────────────────────┘
```

**Data**: `GET /api/discovery/stats?date=2026-04-12`

**Behavior**:
- Date defaults to today
- Arrow buttons step by 1 day
- Changing date re-fetches stats
- Clicking a source card navigates to `/discovery/{source}?date=2026-04-12`
- "Run Discovery" button calls `POST /api/discovery/run`, then re-fetches stats

### Level 2: Source Item List (`/discovery/[source]`)

List of titles fetched from one source on one date. Click a title to see detail.

```
┌──────────────────────────────────────┐
│  ← Discovery / arXiv                 │
│  2026-04-12 · 156 items             │
│                                      │
│  Flash Attention 3: Fast and Exact   │
│  Attention with IO-Awareness         │
│  8:15 AM                             │
│  ─────────────────────────────────── │
│  Scaling Laws for Neural Language    │
│  Model Pretraining                   │
│  6:42 AM                             │
│  ─────────────────────────────────── │
│  RLHF Without Reward Models Using   │
│  Constitutional AI                   │
│  5:30 AM                             │
│  ─────────────────────────────────── │
│  MoE Routing with Expert Choice     │
│  Improves Downstream Performance     │
│  4:12 AM                             │
│  ─────────────────────────────────── │
│  ...                                 │
│                                      │
│  ◀ 1  2  3  4 ▶                     │
└──────────────────────────────────────┘
```

**Data**: `GET /api/discovery/items?source=arxiv&date=2026-04-12&limit=50&offset=0`

**Behavior**:
- Back link returns to dashboard (preserves selected date)
- Each row is just title + published time
- Click a title → navigate to `/discovery/item/{id}`
- Pagination at the bottom

### Level 3: Item Detail (`/discovery/item/[id]`)

All information for one item. Read-only. This is the "crawl receipt."

```
┌──────────────────────────────────────┐
│  ← Back                             │
│                                      │
│  Flash Attention 3: Fast and Exact   │
│  Attention with IO-Awareness         │
│                                      │
│  Source       arXiv                  │
│  Authors      Tri Dao, Daniel Y. Fu  │
│  Published    Apr 12, 2026 8:15 AM   │
│  Fetched      Apr 12, 2026 2:30 PM   │
│  URL          arxiv.org/abs/2401...  │
│                                      │
│  ── Content ──────────────────────── │
│  We propose Flash Attention 3, a     │
│  new algorithm that computes exact   │
│  attention with IO-awareness. Our    │
│  method achieves 2x speedup over...  │
│                                      │
│  ── Metadata ─────────────────────── │
│  arXiv ID       2401.12345v1         │
│  Categories     cs.LG, cs.CL        │
│  Primary        cs.LG               │
│  PDF            [link]               │
└──────────────────────────────────────┘
```

**Data**: `GET /api/discovery/items/{id}`

**Behavior**:
- Back link returns to source list (preserves source + date)
- URL field is a clickable external link (opens in new tab)
- PDF link (arXiv) or HN discussion link opens in new tab
- Metadata section renders all key-value pairs from the JSON blob
- For Reddit: shows subreddit, score, upvote ratio, flair, comment count
- For HN: shows points, comment count, HN discussion link

### Components

| Component | File | Used in |
|-----------|------|---------|
| `SourceCard` | `components/discovery/SourceCard.tsx` | Level 1 — clickable card showing source name + count |
| `ItemRow` | `components/discovery/ItemRow.tsx` | Level 2 — clickable row showing title + time |

### Routes (Next.js App Router)

```
frontend/src/app/discovery/
├── page.tsx                    # Level 1: Dashboard
├── [source]/
│   └── page.tsx                # Level 2: Source item list
└── item/
    └── [id]/
        └── page.tsx            # Level 3: Item detail
```

### Frontend Types (additions to `lib/types.ts`)

```typescript
export interface DiscoveryStats {
  date: string;
  total: number;
  sources: { source: string; count: number }[];
  latest_fetch: string | null;
}

export interface DiscoveryListItem {
  id: string;
  title: string;
  published_at: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
```

### API Client (additions to `lib/api.ts`)

```typescript
// Discovery
getDiscoveryStats: (date?: string) =>
  fetchAPI<DiscoveryStats>(`/api/discovery/stats${date ? `?date=${date}` : ''}`),

getDiscoveryItems: (source: string, params?: { date?: string; limit?: number; offset?: number }) =>
  fetchAPI<PaginatedResponse<DiscoveryListItem>>(
    `/api/discovery/items?source=${source}&${new URLSearchParams(...)}`
  ),

getDiscoveryItem: (id: string) =>
  fetchAPI<RawItem>(`/api/discovery/items/${id}`),

runDiscovery: (source?: string) =>
  fetchAPI<{ stored: number; message: string }>(
    `/api/discovery/run${source ? `?source=${source}` : ''}`,
    { method: 'POST' }
  ),
```

---

## Testing

### Strategy

```
Unit tests (fast, no network, no real DB)
├── test_arxiv_source.py       — parse XML fixtures
├── test_hn_source.py          — parse JSON fixtures
├── test_reddit_source.py      — parse JSON fixtures
│
Integration tests (real DB, mocked HTTP)
├── test_discovery_engine.py   — engine + SQLite
│
API tests (real DB, FastAPI TestClient)
└── test_discovery_api.py      — all 4 endpoints
```

### Fixtures

Real API responses saved as files. Tests never hit the network.

```
tests/fixtures/
├── arxiv_response.xml              5-10 arXiv entries
├── hn_search_response.json         5-10 HN Algolia hits
├── hn_frontpage_response.json      Front page result
└── reddit_response.json            Subreddit .json response
```

### Unit Tests: Source Parsing

Each source has a `_parse_*` method that takes raw API data and returns `RawItem` objects. These are pure functions — easy to test with fixtures.

```python
# test_arxiv_source.py
class TestArxivSource:
    def test_parse_produces_valid_items(self):
        """XML fixture → list of RawItems with correct fields."""

    def test_dedup_across_categories(self):
        """Same paper in cs.LG and cs.CL appears only once."""

    def test_version_stripping(self):
        """2401.12345v2 deduplicates with 2401.12345v1."""

    def test_malformed_entry_skipped(self):
        """Entry missing <id> is silently skipped."""
```

```python
# test_hn_source.py
class TestHackerNewsSource:
    def test_parse_hit_produces_valid_item(self):

    def test_front_page_filters_non_ai_stories(self):

    def test_dedup_between_search_and_frontpage(self):
```

```python
# test_reddit_source.py
class TestRedditSource:
    def test_parse_post_produces_valid_item(self):

    def test_stickied_posts_excluded(self):

    def test_selftext_truncated_at_2000(self):

    def test_self_post_uses_permalink_not_external_url(self):
```

### Integration Tests: Discovery Engine

```python
# test_discovery_engine.py
class TestDiscoveryEngine:
    async def test_stores_items_in_db(self, test_db):

    async def test_dedup_on_rerun(self, test_db):
        """Same items twice → stored only once."""

    async def test_one_source_failure_doesnt_block_others(self, test_db):
```

### API Tests: Endpoints

```python
# test_discovery_api.py
class TestDiscoveryStatsAPI:
    async def test_stats_empty_db(self, client):
        """Returns total=0 and empty sources list."""

    async def test_stats_with_data(self, client, seeded_db):
        """Returns correct per-source counts for the date."""

    async def test_stats_filters_by_date(self, client, seeded_db):
        """Different date returns different counts."""

class TestDiscoveryItemsAPI:
    async def test_requires_source_param(self, client):
        """Returns 422 without source parameter."""

    async def test_returns_titles_only(self, client, seeded_db):
        """Response items have id, title, published_at — no content/metadata."""

    async def test_filters_by_source_and_date(self, client, seeded_db):

    async def test_pagination(self, client, seeded_db):

class TestDiscoveryItemDetailAPI:
    async def test_returns_full_item(self, client, seeded_db):
        """Response includes content, metadata, all fields."""

    async def test_not_found_returns_404(self, client):

class TestDiscoveryRunAPI:
    async def test_triggers_engine(self, client, monkeypatch):
        """Mocked engine returns stored count."""

    async def test_concurrent_run_returns_409(self, client, monkeypatch):
```

### Test Infrastructure

**`tests/conftest.py`:**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.config import settings
from src.db.database import init_db

@pytest.fixture
async def test_db(tmp_path):
    """Temp SQLite DB with schema initialized."""
    settings.DATABASE_PATH = str(tmp_path / "test.db")
    await init_db()
    yield

@pytest.fixture
async def client(test_db):
    """Async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def seeded_db(test_db):
    """DB with 5 arxiv + 5 hn + 5 reddit items pre-inserted."""
    ...
```

### Running Tests

```bash
cd backend
uv run pytest tests/ -v                           # all
uv run pytest tests/test_arxiv_source.py -v       # one source
uv run pytest tests/ -k "api" -v                  # API only
uv run pytest tests/ -k "stats" -v                # just stats endpoint
```

---

## Implementation Order

| Step | What | Validates |
|------|------|-----------|
| 1 | `GET /api/discovery/stats` | Dashboard can show per-source counts |
| 2 | `GET /api/discovery/items` (list with source filter) | Source drill-down shows title list |
| 3 | `GET /api/discovery/items/{id}` | Item detail page works |
| 4 | `POST /api/discovery/run` | Can trigger fetch from UI |
| 5 | Test fixtures in `tests/fixtures/` | Deterministic test data |
| 6 | `tests/conftest.py` | Test harness runs |
| 7 | Unit tests for source parsing | Parsing is correct |
| 8 | Engine integration tests | Store + dedup works |
| 9 | API endpoint tests | All 4 endpoints verified |
| 10 | Frontend Level 1: Dashboard | Date picker + source cards |
| 11 | Frontend Level 2: Source list | Title list with pagination |
| 12 | Frontend Level 3: Item detail | Full item view |
