/* global React, BriefCard, LensSwitcher, ModeToggle, BRIEFS, LENSES, Icon, ThumbsIcon, RAW_ITEMS */

function DailyBriefScreen({ onOpenBrief }) {
  const [lens, setLens] = React.useState('all');
  const visible = lens === 'all' ? BRIEFS : BRIEFS.filter(b => b.lens === lens);

  return (
    <>
      <div className="brief-header">
        <div className="brief-header-bar"/>
        <div className="brief-header-inner">
          <div className="brief-header-left">
            <div className="ey">BRIEF · TUESDAY · 06:00</div>
            <div className="ti">Today's signal — across {LENSES.length} lenses</div>
          </div>
          <div className="brief-header-right">
            <div className="brief-header-stat">
              <div className="brief-header-stat-n">{BRIEFS.length}</div>
              <div className="brief-header-stat-l">briefs</div>
            </div>
            <div className="brief-header-stat">
              <div className="brief-header-stat-n">{BRIEFS.reduce((s,b) => s + b.source_count, 0)}</div>
              <div className="brief-header-stat-l">sources merged</div>
            </div>
            <div className="brief-header-stat">
              <div className="brief-header-stat-n">{BRIEFS.reduce((s,b) => s + b.read_min, 0)}</div>
              <div className="brief-header-stat-l">min total</div>
            </div>
          </div>
        </div>
      </div>

      <LensSwitcher active={lens} onChange={setLens}/>

      {visible.map(b => <BriefCard key={b.id} brief={b} onOpen={onOpenBrief}/>)}

      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 14, color: 'var(--prism-ink-3)' }}>
        That's all five. Three sources were auto-muted this week — <a href="#" style={{ color: 'inherit' }}>review</a>.
      </div>
    </>
  );
}

function BriefDetailScreen({ brief, onBack }) {
  const lens = LENSES.find(l => l.id === brief.lens);
  const [mode, setMode] = React.useState('news');
  return (
    <>
      <button className="btn btn-ghost" style={{ marginBottom: 20, padding: '6px 10px 6px 6px' }} onClick={onBack}>
        <Icon name="arrow" size={14} style={{ transform: 'scaleX(-1)' }}/> Back to today
      </button>

      <div className="detail-spectrum" style={{ background: lens.color }}/>

      <div className="detail-eyebrow">
        <span className="brief-eyebrow" style={{ color: lens.ink, margin: 0 }}>
          <span className="brief-eyebrow-dot" style={{ background: lens.color }}/>
          {lens.name} lens
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--prism-ink-3)' }}>· {brief.source_count} sources merged · {brief.read_min} min read</span>
      </div>

      <h1 className="detail-title">{brief.title}</h1>
      <p className="detail-lead">{brief.lead}</p>

      <div style={{ marginBottom: 28 }}><ModeToggle value={mode} onChange={setMode}/></div>

      {mode === 'news' && brief.claims?.length > 0 && (
        <section className="detail-section">
          <div className="detail-section-label">Claims · {brief.claims.length} extracted, verified across {brief.source_count} sources</div>
          {brief.claims.map(c => (
            <div className="detail-claim" key={c.n}>
              <div className="detail-claim-n">{String(c.n).padStart(2,'0')}</div>
              <div className="detail-claim-text" dangerouslySetInnerHTML={{ __html: c.text }}/>
              <div className="detail-claim-src">{c.src}</div>
            </div>
          ))}
        </section>
      )}

      {mode === 'basics' && (
        <section className="detail-section">
          <div className="detail-section-label">Explainer · from basics</div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 15, lineHeight: 1.65, color: 'var(--prism-ink)', maxWidth: '64ch' }}>
            Speculative decoding accelerates LLM inference by running a small "draft" model to propose
            multiple tokens, then verifying them in parallel with the larger target model. Tokens the
            target accepts are kept; mismatches force a fallback to one normal decode step. The net win
            depends on draft acceptance rate.
          </p>
        </section>
      )}

      {mode === 'delta' && (
        <section className="detail-section">
          <div className="detail-section-label">Explainer · delta from what you know</div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 15, lineHeight: 1.65, color: 'var(--prism-ink)', maxWidth: '64ch' }}>
            You already understand the rejection-sampling proof. What's new this week: the structured-output
            case is unsolved — Karpathy's 200-line implementation gives the cleanest read on why, and the
            arxiv paper isolates the failure mode to constrained-decoding masks invalidating the draft
            distribution.
          </p>
        </section>
      )}

      {mode === 'discussion' && (
        <section className="detail-section">
          <div className="detail-section-label">Two sides</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{ padding: 18, background: 'var(--prism-paper-2)', borderRadius: 'var(--r-md)' }}>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--prism-ink-3)', marginBottom: 8 }}>Ship it</div>
              <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 13.5, lineHeight: 1.5 }}>2.4× throughput is real and the implementation fits on a screen. Latency is the UX.</p>
            </div>
            <div style={{ padding: 18, background: 'var(--prism-paper-2)', borderRadius: 'var(--r-md)' }}>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--prism-ink-3)', marginBottom: 8 }}>Hold off</div>
              <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 13.5, lineHeight: 1.5 }}>The structured-output failure mode kills you on JSON tool-calls — which is most of your traffic.</p>
            </div>
          </div>
        </section>
      )}

      <section className="detail-section">
        <div className="detail-section-label">Primary sources</div>
        {brief.sources.map((s, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: i ? '1px solid var(--prism-hairline)' : 'none', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            <span style={{ color: 'var(--prism-ink)' }}>{s}</span>
            <span style={{ color: 'var(--prism-ink-3)' }}>verified · {(0.95 - i * 0.04).toFixed(2)}</span>
          </div>
        ))}
      </section>

      <section className="detail-section">
        <div className="detail-section-label">Tune this brief</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}><ThumbsIcon direction="up"/> Sharp signal</button>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}><ThumbsIcon direction="down"/> Noise</button>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}>More like this</button>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}>Too basic</button>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}>Too advanced</button>
          <button className="fb-btn" style={{ padding: '7px 12px', border: '1px solid var(--prism-hairline)' }}><Icon name="mute" size={14}/> Mute this source</button>
        </div>
      </section>
    </>
  );
}

function RawDiscoveryScreen() {
  const [source, setSource] = React.useState('all');
  const sources = ['all', 'arxiv', 'hn', 'reddit', 'podcast', 'github'];
  const visible = source === 'all' ? RAW_ITEMS : RAW_ITEMS.filter(r => r.source === source);

  return (
    <>
      <div style={{ marginBottom: 8 }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 28, margin: '0 0 6px', letterSpacing: '-0.012em' }}>Raw discovery</h2>
        <p style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 15, color: 'var(--prism-ink-2)', margin: 0 }}>
          Every annotated item from the lake. Tap a score to disagree.
        </p>
      </div>

      <div className="lens-switcher" style={{ marginTop: 18 }}>
        {sources.map(s => (
          <button
            key={s}
            className={`lens-pill ${source === s ? 'is-active' : ''}`}
            onClick={() => setSource(s)}
          >{s === 'all' ? `All sources · ${RAW_ITEMS.length}` : s}</button>
        ))}
      </div>

      <div style={{ background: 'var(--prism-card)', border: '1px solid var(--prism-hairline)', borderRadius: 'var(--r-md)', overflow: 'hidden' }}>
        <div className="raw-row head">
          <span>SOURCE</span><span>TITLE</span><span>TOPIC</span><span>LENS</span><span style={{ textAlign: 'right' }}>SCORE</span>
        </div>
        {visible.map(r => {
          const lens = LENSES.find(l => l.id === r.lens);
          return (
            <div className="raw-row" key={r.id} style={r.muted ? { opacity: 0.45 } : {}}>
              <span className="src">{r.source}</span>
              <span className="ti">{r.title}{r.muted && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, marginLeft: 6, color: 'var(--prism-critical)' }}>· muted</span>}</span>
              <span className="topic">{r.topic}</span>
              <span><span className="brief-eyebrow-dot" style={{ background: lens?.color, display: 'inline-block', marginRight: 4 }}></span><span style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--prism-ink-2)' }}>{lens?.name}</span></span>
              <span className="score">{r.relevance.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    </>
  );
}

function OnboardingScreen({ onDone }) {
  return (
    <div className="onb">
      <div className="onb-step">STEP 2 OF 3 · LENSES</div>
      <h1 className="onb-title">What hats do you wear?</h1>
      <p className="onb-lead">Declare the identities you hold. Each becomes a lens — a tuned view of the world for that specific version of you. Two or three is the sweet spot.</p>

      {LENSES.map(l => (
        <div className="onb-field" key={l.id}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span className="brief-eyebrow-dot" style={{ background: l.color }}/>
            <span className="onb-field-name">{l.name}</span>
          </div>
          <div className="onb-field-thesis">{l.thesis}</div>
        </div>
      ))}

      <button className="onb-add">
        <span style={{ width: 14, height: 14, display: 'inline-flex' }}><Icon name="plus" size={14}/></span>
        Add another hat
      </button>

      <div className="onb-actions">
        <button className="btn btn-primary" onClick={onDone}>
          Read today's first brief
          <Icon name="arrow" size={14}/>
        </button>
        <button className="btn btn-ghost">Save and continue later</button>
      </div>
    </div>
  );
}

function ProfileScreen() {
  return (
    <div style={{ maxWidth: 560 }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 28, margin: '0 0 6px', letterSpacing: '-0.012em' }}>Settings</h2>
      <p style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 15, color: 'var(--prism-ink-2)', margin: '0 0 28px' }}>Tune your lenses. Mute what isn't working.</p>

      <div className="detail-section-label">Your lenses</div>
      {LENSES.map(l => (
        <div key={l.id} style={{ display: 'grid', gridTemplateColumns: '24px 1fr auto', alignItems: 'center', gap: 14, padding: '14px 0', borderTop: '1px solid var(--prism-hairline)' }}>
          <span className="brief-eyebrow-dot" style={{ background: l.color, width: 8, height: 8 }}/>
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 500, marginBottom: 2 }}>{l.name}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 13.5, color: 'var(--prism-ink-2)' }}>{l.thesis}</div>
          </div>
          <button className="btn btn-ghost" style={{ padding: '6px 10px' }}>Edit</button>
        </div>
      ))}

      <div className="detail-section-label" style={{ marginTop: 32 }}>Auto-muted this week</div>
      <div style={{ background: 'var(--prism-paper-2)', borderRadius: 'var(--r-md)', padding: '14px 16px' }}>
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: 13, lineHeight: 1.55, color: 'var(--prism-ink-2)' }}>
          Substack post-of-the-week threads, Product Hunt launch lists, generic VC year-in-review tweets.
          <a href="#" style={{ marginLeft: 6, color: 'var(--prism-ink)', borderBottom: '1px dotted' }}>Un-mute</a>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DailyBriefScreen, BriefDetailScreen, RawDiscoveryScreen, OnboardingScreen, ProfileScreen });
