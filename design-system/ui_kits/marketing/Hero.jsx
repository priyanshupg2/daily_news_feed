/* global React */
// Inline icons — same vocabulary as the web app kit.
function MarketingIcon({ name, size = 16 }) {
  const props = {
    width: size, height: size, viewBox: '0 0 24 24',
    fill: 'none', stroke: 'currentColor',
    strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round',
  };
  switch (name) {
    case 'arrow':    return <svg {...props}><path d="M5 12h14M13 5l7 7-7 7"/></svg>;
    case 'check':    return <svg {...props}><path d="M5 12l5 5L20 7"/></svg>;
    case 'plus':     return <svg {...props}><path d="M12 5v14M5 12h14"/></svg>;
    default: return null;
  }
}

function MarketingNav() {
  return (
    <nav className="nav">
      <a href="#" className="nav-brand">
        <img src="../../assets/prism-mark.svg" alt=""/>
        <span className="nav-brand-text">Prism</span>
      </a>
      <div className="nav-links">
        <a href="#how">How it works</a>
        <a href="#lenses">Lenses</a>
        <a href="#trust">Sources</a>
        <a href="#pricing">Pricing</a>
      </div>
      <div className="nav-actions">
        <a href="#" className="btn btn-secondary btn-sm">Sign in</a>
        <a href="#" className="btn btn-primary btn-sm">Get early access <MarketingIcon name="arrow" size={13}/></a>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="hero">
      <div className="container">
        <div className="hero-grid">
          <div>
            <div className="hero-eyebrow">
              <span className="hero-eyebrow-dot"/>
              Five lenses, one tool
            </div>
            <h1 className="hero-title">Intelligence, <em>refracted</em> for who you are.</h1>
            <p className="hero-sub">You're a founder, an engineer, a researcher — all before lunch. Prism reads the world and gives you a daily brief tuned to each version of you.</p>
            <div className="hero-cta-row">
              <a href="#" className="btn btn-primary">Get early access <MarketingIcon name="arrow"/></a>
              <a href="#" className="btn btn-secondary">See a real brief</a>
            </div>
            <div className="hero-meta">Joining 1,400 founders, operators &amp; researchers on the list</div>
          </div>
          <RefractionVisual/>
        </div>
      </div>
    </section>
  );
}

// The hero-side refraction visual: white beam → prism → labeled briefs in a clean stack.
function RefractionVisual() {
  const lenses = [
    { color: 'var(--lens-founder)',    name: 'Founder',    text: 'Anthropic raised $13B — three signals for B2B fintech' },
    { color: 'var(--lens-investor)',   name: 'Investor',   text: 'Two India fintechs at the same Series B mark' },
    { color: 'var(--lens-researcher)', name: 'Researcher', text: 'CHI papers converge on interaction-first a11y' },
    { color: 'var(--lens-engineer)',   name: 'Engineer',   text: 'Speculative decoding, in 200 lines' },
    { color: 'var(--lens-operator)',   name: 'Operator',   text: 'Runway extended — three orgs cut burn this week' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 12, alignItems: 'center' }}>
      {/* Left: the prism diagram */}
      <svg viewBox="0 0 160 320" style={{ width: '100%', height: 'auto', display: 'block' }}>
        <defs>
          <linearGradient id="white-beam-h" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="rgba(20,19,15,0.0)"/>
            <stop offset="100%" stopColor="rgba(20,19,15,0.55)"/>
          </linearGradient>
        </defs>
        <line x1="0" y1="160" x2="60" y2="160" stroke="url(#white-beam-h)" strokeWidth="2.5" strokeLinecap="round"/>
        <path d="M90 70 L150 240 L30 240 Z" stroke="#14130F" strokeWidth="2.4" fill="none" strokeLinejoin="round"/>
        <circle cx="90" cy="160" r="3" fill="#14130F"/>
        <line x1="90" y1="160" x2="160" y2="40"  stroke="var(--lens-founder)"    strokeWidth="2.5" strokeLinecap="round"/>
        <line x1="90" y1="160" x2="160" y2="100" stroke="var(--lens-investor)"   strokeWidth="2.5" strokeLinecap="round"/>
        <line x1="90" y1="160" x2="160" y2="160" stroke="var(--lens-researcher)" strokeWidth="2.5" strokeLinecap="round"/>
        <line x1="90" y1="160" x2="160" y2="220" stroke="var(--lens-engineer)"   strokeWidth="2.5" strokeLinecap="round"/>
        <line x1="90" y1="160" x2="160" y2="280" stroke="var(--lens-operator)"   strokeWidth="2.5" strokeLinecap="round"/>
      </svg>

      {/* Right: vertical stack of labels */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {lenses.map(l => (
          <div key={l.name} style={{
            display: 'flex', alignItems: 'baseline', gap: 10,
            paddingLeft: 14,
            borderLeft: `2px solid ${l.color}`,
          }}>
            <span style={{
              fontFamily: 'var(--font-sans)', fontSize: 10, fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.12em',
              color: 'var(--prism-ink-3)', whiteSpace: 'nowrap', minWidth: 76,
            }}>{l.name}</span>
            <span style={{
              fontFamily: 'var(--font-display)', fontStyle: 'italic',
              fontSize: 14, color: 'var(--prism-ink)', lineHeight: 1.3,
            }}>{l.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { MarketingNav, Hero, MarketingIcon });
