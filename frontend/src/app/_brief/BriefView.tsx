"use client";

import { useEffect, useState } from "react";
import { BriefCard } from "./BriefCard";
import { type Brief, LENSES } from "./types";
import { SlidersIcon, SparkleIcon } from "./icons";

type ThemeId =
  | "auto"
  | "time-sand"
  | "time-morning"
  | "time-midday"
  | "time-afternoon"
  | "time-evening"
  | "time-night";

type LensFilter = "all" | (typeof LENSES)[number]["id"];

const THEMES: { id: ThemeId; name: string; swatch: string }[] = [
  { id: "auto",           name: "Auto · by time", swatch: "#E8DEB6" },
  { id: "time-sand",      name: "Sand",           swatch: "#FAF7F2" },
  { id: "time-morning",   name: "Butter",         swatch: "#FAF4DE" },
  { id: "time-midday",    name: "Sky",            swatch: "#ECF0F4" },
  { id: "time-afternoon", name: "Sage",           swatch: "#F0F2E8" },
  { id: "time-evening",   name: "Terracotta",     swatch: "#F5EBE2" },
  { id: "time-night",     name: "Linen",          swatch: "#F1E8DC" },
];

function timeOfDay() {
  const h = new Date().getHours();
  if (h >= 5  && h < 11) return { period: "morning",   theme: "time-morning"   as const, refresh: "06:00" };
  if (h >= 11 && h < 14) return { period: "midday",    theme: "time-midday"    as const, refresh: "12:00" };
  if (h >= 14 && h < 18) return { period: "afternoon", theme: "time-afternoon" as const, refresh: "12:00" };
  if (h >= 18 && h < 22) return { period: "evening",   theme: "time-evening"   as const, refresh: "18:00" };
  return { period: "night", theme: "time-night" as const, refresh: "still 06:00" };
}

export function BriefView({ briefs }: { briefs: Brief[] }) {
  const [theme, setTheme] = useState<ThemeId>("auto");
  const [lens, setLens] = useState<LensFilter>("all");
  const [openId, setOpenId] = useState<string | null>(null);

  // Time-of-day is client-only so we render header copy after mount to avoid
  // server/client divergence on locale + hour.
  const [tod, setTod] = useState<{ period: string; refresh: string; dateLabel: string } | null>(null);

  useEffect(() => {
    const t = timeOfDay();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTod({
      period: t.period,
      refresh: t.refresh,
      dateLabel: new Date()
        .toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })
        .toUpperCase(),
    });
  }, []);

  useEffect(() => {
    const applied = theme === "auto" ? timeOfDay().theme : theme;
    document.body.className = applied;
  }, [theme]);

  const visible = lens === "all" ? briefs : briefs.filter((b) => b.lens === lens);
  const total = briefs.length;
  const sources = briefs.reduce((s, b) => s + b.source_count, 0);
  const mins = briefs.reduce((s, b) => s + b.read_min, 0);

  const counts: Record<string, number> = { all: briefs.length };
  LENSES.forEach((l) => {
    counts[l.id] = briefs.filter((b) => b.lens === l.id).length;
  });

  return (
    <div className="page">
      {/* Top strip */}
      <div className="topstrip">
        <a href="#" className="topstrip-brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/prism-mark.svg" alt="" />
          <span className="topstrip-brand-text">Prism</span>
        </a>
        <div className="topstrip-actions">
          <span className="kbd-strip">⌘K</span>
          <button className="icon-btn" title="Refresh" aria-label="Refresh">
            <SparkleIcon size={15} />
          </button>
          <button className="icon-btn" title="Settings" aria-label="Settings">
            <SlidersIcon size={15} />
          </button>
        </div>
      </div>

      {/* Paper picker */}
      <div className="palette-picker">
        <span className="palette-picker-label">Paper</span>
        {THEMES.map((t) => (
          <button
            key={t.id}
            className={`palette-chip ${theme === t.id ? "is-active" : ""}`}
            onClick={() => setTheme(t.id)}
          >
            <span className="palette-chip-swatch" style={{ background: t.swatch }} />
            {t.name}
          </button>
        ))}
      </div>

      {/* Brief header */}
      <div className="brief-header">
        <div className="brief-header-bar" />
        <div className="brief-header-inner">
          <div className="brief-header-date">
            <span className="pulse" />
            {tod ? `${tod.dateLabel} · REFRESHED ${tod.refresh}` : "TODAY · REFRESHED —"}
          </div>
          <h1 className="brief-header-h">
            The {tod?.period ?? "day"}, <em>refracted.</em>
          </h1>
          <div className="brief-header-stats-inline">
            <span>
              <b>{total}</b>briefs
            </span>
            <span>
              <b>{sources}</b>sources merged
            </span>
            <span>
              <b>{mins}m</b>to read
            </span>
          </div>
        </div>
      </div>

      {/* Lens switcher */}
      <div className="lens-switcher">
        <button
          className={`lens-pill ${lens === "all" ? "is-active" : ""}`}
          onClick={() => setLens("all")}
        >
          All <span className="lens-pill-count">· {counts.all}</span>
        </button>
        {LENSES.map((l) => (
          <button
            key={l.id}
            className={`lens-pill ${lens === l.id ? "is-active" : ""}`}
            onClick={() => setLens(l.id)}
          >
            <span className="lens-pill-dot" style={{ background: l.color }} />
            {l.name}
            <span className="lens-pill-count">· {counts[l.id] ?? 0}</span>
          </button>
        ))}
      </div>

      {/* Cards */}
      {visible.map((b) => {
        const briefLens = LENSES.find((l) => l.id === b.lens) ?? LENSES[0];
        return (
          <BriefCard
            key={b.id}
            brief={b}
            lens={briefLens}
            isOpen={openId === b.id}
            onToggle={(id) => setOpenId((prev) => (prev === id ? null : id))}
          />
        );
      })}

      <div className="endnote">
        That&apos;s the {tod?.period ?? "day"}. <a>3 sources auto-muted this week</a>.
      </div>
    </div>
  );
}
