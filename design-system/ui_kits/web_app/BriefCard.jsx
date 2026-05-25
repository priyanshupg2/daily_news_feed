/* global React, Icon, ThumbsIcon, LENSES */

function LensBadge({ lens, size = 'sm' }) {
  return (
    <span className="brief-eyebrow" style={{ color: lens.ink, margin: 0 }}>
      <span className="brief-eyebrow-dot" style={{ background: lens.color }}/>
      {lens.name} lens
    </span>
  );
}

function BriefCard({ brief, onOpen }) {
  const lens = LENSES.find(l => l.id === brief.lens) || LENSES[0];
  return (
    <article className="brief" onClick={() => onOpen?.(brief)}>
      <div className="brief-accent" style={{ background: lens.color }}/>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, gap: 12 }}>
        <LensBadge lens={lens}/>
        <span className="brief-meta">{brief.source_count} sources · {brief.read_min} min</span>
      </div>
      <h3 className="brief-title">{brief.title}</h3>
      <p className="brief-lead">{brief.lead}</p>
      <p className="brief-why">
        <span className="brief-why-label">Why this is in your brief</span>
        {brief.why}
      </p>
      <div className="brief-footer">
        <div className="brief-sources">
          {brief.sources.slice(0, 3).map((s, i) => <a key={i}>{s}</a>)}
          {brief.sources.length > 3 && <span>+ {brief.sources.length - 3} more</span>}
        </div>
        <FeedbackRow briefId={brief.id}/>
      </div>
    </article>
  );
}

function FeedbackRow({ briefId }) {
  const [state, setState] = React.useState({});
  const set = k => () => setState(s => ({ ...s, [k]: !s[k] }));
  return (
    <div className="fbrow" onClick={e => e.stopPropagation()}>
      <button className={`fb-btn ${state.up ? 'is-on' : ''}`} onClick={set('up')}>
        <ThumbsIcon direction="up"/>
      </button>
      <button className={`fb-btn ${state.down ? 'is-on' : ''}`} onClick={set('down')}>
        <ThumbsIcon direction="down"/>
      </button>
      <button className={`fb-btn ${state.save ? 'is-on' : ''}`} onClick={set('save')}>
        <Icon name="bookmark" size={14}/>
      </button>
    </div>
  );
}

function ModeToggle({ value, onChange }) {
  const modes = [
    { id: 'news', label: 'News' },
    { id: 'basics', label: 'Explainer · basics' },
    { id: 'delta', label: 'Explainer · delta' },
    { id: 'discussion', label: 'Discussion' },
  ];
  return (
    <div className="modes">
      {modes.map(m => (
        <button
          key={m.id}
          className={`mode-btn ${value === m.id ? 'is-active' : ''}`}
          onClick={() => onChange?.(m.id)}
        >{m.label}</button>
      ))}
    </div>
  );
}

function LensSwitcher({ active, onChange }) {
  return (
    <div className="lens-switcher">
      <button
        className={`lens-pill ${active === 'all' ? 'is-active' : ''}`}
        onClick={() => onChange('all')}
      >All briefs · 5</button>
      {LENSES.map(l => (
        <button
          key={l.id}
          className={`lens-pill ${active === l.id ? 'is-active' : ''}`}
          onClick={() => onChange(l.id)}
        >
          <span className="lens-pill-dot" style={{ background: l.color }}/>
          {l.name}
        </button>
      ))}
    </div>
  );
}

Object.assign(window, { BriefCard, FeedbackRow, ModeToggle, LensSwitcher, LensBadge });
