"use client";

import { useState } from "react";
import type { Brief, Lens } from "./data";
import { BookmarkIcon, ThumbsDownIcon, ThumbsUpIcon } from "./icons";

type Props = {
  brief: Brief;
  lens: Lens;
  isOpen: boolean;
  onToggle: (id: string) => void;
};

export function BriefCard({ brief, lens, isOpen, onToggle }: Props) {
  const [marks, setMarks] = useState<{ up?: boolean; down?: boolean; save?: boolean }>({});

  const flip = (k: "up" | "down" | "save") => (e: React.MouseEvent) => {
    e.stopPropagation();
    setMarks((s) => ({ ...s, [k]: !s[k] }));
  };

  return (
    <article className={`brief ${isOpen ? "is-open" : ""}`}>
      <div className="brief-accent" style={{ background: lens.color }} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div className="brief-eyebrow" style={{ color: lens.ink }}>
          <span className="brief-eyebrow-dot" style={{ background: lens.color }} />
          {lens.name} lens
        </div>
        <div className="brief-meta">
          {brief.source_count} sources · {brief.read_min} min
        </div>
      </div>

      <h2 className="brief-title" onClick={() => onToggle(brief.id)}>
        {brief.title}
      </h2>
      <p className="brief-lead">{brief.lead}</p>
      <p className="brief-why">
        <span className="brief-why-label">Why this is in your brief</span>
        {brief.why}
      </p>

      <div className="brief-footer">
        <div className="brief-sources">
          {brief.sources.slice(0, 3).map((s) => (
            <a key={s}>{s}</a>
          ))}
          {brief.sources.length > 3 && <span>+ {brief.sources.length - 3} more</span>}
        </div>
        <div className="fbrow">
          <button className={`fb-btn ${marks.up ? "is-on" : ""}`} onClick={flip("up")} title="Sharp signal" aria-label="Sharp signal">
            <ThumbsUpIcon size={14} />
          </button>
          <button className={`fb-btn ${marks.down ? "is-on" : ""}`} onClick={flip("down")} title="Noise" aria-label="Noise">
            <ThumbsDownIcon size={14} />
          </button>
          <button className={`fb-btn ${marks.save ? "is-on" : ""}`} onClick={flip("save")} title="Save" aria-label="Save">
            <BookmarkIcon size={14} />
          </button>
        </div>
      </div>

      {isOpen && brief.claims.length > 0 && (
        <div className="brief-expand">
          <div className="claims-label">Claims · verified across {brief.source_count} sources</div>
          {brief.claims.map((c) => (
            <div className="claim" key={c.n}>
              <div className="claim-n">{String(c.n).padStart(2, "0")}</div>
              <div>
                <div className="claim-text" dangerouslySetInnerHTML={{ __html: c.text }} />
                <div className="cite">
                  <a>{c.src}</a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
