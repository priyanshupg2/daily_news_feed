/* global React, Icon */

// Lens metadata — single source of truth used across screens.
const LENSES = [
  { id: 'founder',    name: 'Founder',    thesis: 'B2B fintech for Indian SMBs',          color: 'var(--lens-founder)',    soft: 'var(--lens-founder-soft)',    ink: 'var(--lens-founder-ink)' },
  { id: 'engineer',   name: 'Engineer',   thesis: 'Agentic systems, inference economics', color: 'var(--lens-engineer)',   soft: 'var(--lens-engineer-soft)',   ink: 'var(--lens-engineer-ink)' },
  { id: 'researcher', name: 'Researcher', thesis: 'HCI for assistive tech',               color: 'var(--lens-researcher)', soft: 'var(--lens-researcher-soft)', ink: 'var(--lens-researcher-ink)' },
];

function AppShell({ active, onNavigate, children }) {
  return (
    <div className="app">
      <Rail active={active} onNavigate={onNavigate}/>
      <div className="canvas">
        <TopBar active={active}/>
        <div className="canvas-inner">{children}</div>
      </div>
    </div>
  );
}

function Rail({ active, onNavigate }) {
  return (
    <nav className="rail">
      <div className="rail-brand">
        <img src="../../assets/prism-mark.svg" alt=""/>
        <span className="rail-brand-text">Prism</span>
      </div>

      <div className="rail-section">Today</div>
      <button className={`rail-item ${active === 'brief' ? 'is-active' : ''}`} onClick={() => onNavigate('brief')}>
        <Icon name="brief"/> Daily brief
      </button>
      <button className={`rail-item ${active === 'raw' ? 'is-active' : ''}`} onClick={() => onNavigate('raw')}>
        <Icon name="raw"/> Raw discovery
      </button>
      <button className="rail-item" onClick={() => onNavigate('brief')}>
        <Icon name="bookmark"/> Saved
      </button>

      <div className="rail-section">Lenses</div>
      {LENSES.map(l => (
        <button
          key={l.id}
          className={`rail-item ${active === 'lens-' + l.id ? 'is-active' : ''}`}
          onClick={() => onNavigate('lens-' + l.id)}
        >
          <span className="rail-item-dot" style={{ background: l.color }}/>
          {l.name}
        </button>
      ))}
      <button className="rail-item" onClick={() => onNavigate('onboarding')}>
        <Icon name="plus"/> Add a lens
      </button>

      <div className="rail-spacer"></div>

      <button className={`rail-item ${active === 'profile' ? 'is-active' : ''}`} onClick={() => onNavigate('profile')}>
        <Icon name="sliders"/> Settings
      </button>
    </nav>
  );
}

function TopBar({ active }) {
  const title =
    active === 'brief' ? 'Tuesday, 25 May 2026' :
    active === 'raw' ? 'Raw discovery' :
    active === 'onboarding' ? 'Add a lens' :
    active === 'profile' ? 'Settings' :
    active && active.startsWith('lens-') ? 'Lens · ' + (LENSES.find(l => l.id === active.slice(5))?.name || '') :
    'Today';
  return (
    <header className="topbar">
      <span className="topbar-title">{title}</span>
      <span className="topbar-meta">·  brief refreshed 06:00</span>
      <div style={{ flex: 1 }}/>
      <div className="topbar-search">
        <Icon name="search" size={14}/>
        <input placeholder="Search briefs, sources, claims…"/>
        <span className="kbd">⌘K</span>
      </div>
      <button className="topbar-action">
        <Icon name="sparkle" size={14}/>
        Refresh
      </button>
    </header>
  );
}

Object.assign(window, { AppShell, LENSES });
