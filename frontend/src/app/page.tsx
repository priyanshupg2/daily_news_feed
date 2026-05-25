"use client";

import { useEffect, useState } from "react";
import { BriefView } from "./_brief/BriefView";
import type { Brief, LensId } from "./_brief/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type APIClaim = {
  n: number;
  text: string;
  citation_text: string | null;
  source_url: string | null;
  source_title: string | null;
};

type APIBrief = {
  id: string;
  title: string | null;
  lead: string | null;
  why_it_matters: string | null;
  summary: string;
  framing: string | null;
  source_links: { url: string; title: string; source: string }[];
  source_count: number;
  primary_lens: LensId | null;
  lenses: { lens_id: LensId; relevance_score: number; name: string }[];
  claims: APIClaim[];
};

function adapt(api: APIBrief): Brief {
  const primary = api.primary_lens ?? api.lenses[0]?.lens_id ?? "engineer";
  const lensIds = api.lenses.map((l) => l.lens_id);
  return {
    id: api.id,
    lens: primary,
    lenses: lensIds,
    title: api.title ?? api.summary.slice(0, 80),
    lead: api.lead ?? api.summary,
    why: api.why_it_matters ?? "",
    source_count: api.source_count,
    read_min: Math.max(2, Math.min(10, Math.ceil(api.source_count / 2))),
    sources: api.source_links.map((s) =>
      (() => {
        try { return new URL(s.url).hostname.replace(/^www\./, ""); }
        catch { return s.source; }
      })()
    ),
    claims: api.claims.map((c) => ({
      n: c.n,
      text: c.text,
      src: c.citation_text ?? c.source_title ?? "source",
    })),
  };
}

export default function DailyBriefPage() {
  const [briefs, setBriefs] = useState<Brief[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/feed/`)
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`);
        return r.json();
      })
      .then((data: { briefs: APIBrief[] }) => {
        setBriefs(data.briefs.map(adapt));
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16 text-fg">
        <h1 className="text-2xl">Backend unreachable</h1>
        <p className="mt-2 text-sm text-muted">
          {error}. Start the API with{" "}
          <code className="font-mono">uvicorn src.main:app</code> from{" "}
          <code className="font-mono">backend/</code>.
        </p>
      </main>
    );
  }
  if (briefs === null) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16 text-fg">
        <p className="text-sm text-muted">Loading…</p>
      </main>
    );
  }
  if (briefs.length === 0) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-16 text-fg">
        <h1 className="text-2xl">No briefs yet today.</h1>
        <p className="mt-2 text-sm text-muted">
          The pipeline runs at 06:00. Trigger one manually with{" "}
          <code className="font-mono">POST /api/feed/refresh?full=true</code>{" "}
          once <code className="font-mono">ANTHROPIC_API_KEY</code> is set.
        </p>
      </main>
    );
  }
  return <BriefView briefs={briefs} />;
}
