/* global React, MarketingIcon */

function Problem() {
  return (
    <section className="section" id="problem">
      <div className="container">
        <div className="section-eyebrow">The problem</div>
        <h2 className="section-title">You don't have one job. Your tools assume you do.</h2>
        <p className="section-lead">
          A technical founder is a CEO, an engineer, and a researcher — at the same time. The 12 newsletters,
          three platforms, and 40 tabs that promise to keep you current were built for one of those people. Pick one.
        </p>
        <div className="problem-grid">
          <div className="problem-card">
            <div className="problem-card-tag">TLDR &middot; Rundown &middot; Superhuman</div>
            <h3 className="problem-card-name">Generic AI summaries</h3>
            <p className="problem-card-fail">Built for "everyone." Tuned for no one.</p>
          </div>
          <div className="problem-card">
            <div className="problem-card-tag">Particle &middot; Artifact</div>
            <h3 className="problem-card-name">Consumer news</h3>
            <p className="problem-card-fail">One feed for all. Artifact shut down for a reason.</p>
          </div>
          <div className="problem-card">
            <div className="problem-card-tag">CB Insights &middot; PitchBook</div>
            <h3 className="problem-card-name">Enterprise intel</h3>
            <p className="problem-card-fail">$30–60K a year. Built for one role.</p>
          </div>
          <div className="problem-card">
            <div className="problem-card-tag">Twitter &middot; RSS</div>
            <h3 className="problem-card-name">The firehose</h3>
            <p className="problem-card-fail">Infinite scroll, no synthesis. You triage it yourself.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Pillars() {
  return (
    <section className="section" id="how">
      <div className="container">
        <div className="section-eyebrow">What's different</div>
        <h2 className="section-title">Three things make Prism different.</h2>

        <div className="pillar-grid" style={{ marginTop: 56 }}>
          <div className="pillar">
            <div className="pillar-n">01<em>·</em></div>
            <h3 className="pillar-h">Multi-lens, not multi-topic.</h3>
            <p className="pillar-p">
              You don't pick topics. You declare identities and the questions you're holding under each.
              Each becomes a lens — a tuned view of the world for that specific version of you.
            </p>
          </div>
          <div className="pillar">
            <div className="pillar-n">02<em>·</em></div>
            <h3 className="pillar-h">Synthesis, not summary.</h3>
            <p className="pillar-p">
              Other tools shrink articles. Prism extracts claims, verifies them across sources, and tells
              you what changed and why it matters — for your specific thesis. Headlines become decisions.
            </p>
          </div>
          <div className="pillar">
            <div className="pillar-n">03<em>·</em></div>
            <h3 className="pillar-h">Sources you can trust.</h3>
            <p className="pillar-p">
              Every claim links to its primary source. Per-lens signal-rate is measured and bad sources
              auto-mute. You stop wasting time on noise you didn't know was noise.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section" id="lenses">
      <div className="container">
        <div className="section-eyebrow">A worked example · the technical founder</div>
        <h2 className="section-title">Three lenses. One person. One brief.</h2>
        <p className="section-lead">
          Tell Prism the hats you wear and what you're trying to figure out under each. Each becomes a lens.
          The same morning produces three different briefs.
        </p>

        <div className="how-grid">
          <div className="how-card">
            <div className="how-card-accent" style={{ background: 'var(--lens-founder)' }}/>
            <div className="how-card-eyebrow" style={{ color: 'var(--lens-founder-ink)' }}>
              <span className="how-card-dot" style={{ background: 'var(--lens-founder)' }}/>
              Founder lens
            </div>
            <p className="how-card-q">"B2B fintech for Indian SMBs — what unit economics actually work, what distribution is still un-saturated."</p>
            <h3 className="how-card-h">Reads like a market memo.</h3>
            <p className="how-card-p">Funding patterns, competitor moves, regulatory shifts, distribution channels.</p>
          </div>
          <div className="how-card">
            <div className="how-card-accent" style={{ background: 'var(--lens-engineer)' }}/>
            <div className="how-card-eyebrow" style={{ color: 'var(--lens-engineer-ink)' }}>
              <span className="how-card-dot" style={{ background: 'var(--lens-engineer)' }}/>
              Engineer lens
            </div>
            <p className="how-card-q">"Going deep on agentic systems — what's actually shipping, what's breaking, what's the new bottleneck."</p>
            <h3 className="how-card-h">Reads like a technical digest.</h3>
            <p className="how-card-p">Repos, releases, benchmark posts, postmortems. The 200-line reference, not the 50-page paper.</p>
          </div>
          <div className="how-card">
            <div className="how-card-accent" style={{ background: 'var(--lens-researcher)' }}/>
            <div className="how-card-eyebrow" style={{ color: 'var(--lens-researcher-ink)' }}>
              <span className="how-card-dot" style={{ background: 'var(--lens-researcher)' }}/>
              Researcher lens
            </div>
            <p className="how-card-q">"HCI for assistive tech — what's moving in the field, where the open questions are converging."</p>
            <h3 className="how-card-h">Reads like a lab notebook.</h3>
            <p className="how-card-p">Papers, citations, who's working on what — and the connections nobody has drawn yet.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTAStrip() {
  return (
    <section className="section" id="pricing" style={{ paddingTop: 40 }}>
      <div className="container">
        <div className="cta">
          <div className="cta-spectrum"/>
          <h2 className="cta-title">Same world. <em>Sharper view.</em></h2>
          <p className="cta-lead">Early access opens in waves. Pricing for individuals; not $30K a year. Tell us the hats you wear and we'll set up your lenses.</p>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              placeholder="you@yourdomain.com"
              style={{
                fontFamily: 'var(--font-sans)', fontSize: 14,
                padding: '12px 14px', minWidth: 260,
                border: '1px solid var(--prism-hairline)',
                borderRadius: 'var(--r-md)',
                background: 'var(--prism-paper)',
                color: 'var(--prism-ink)',
                outline: 'none',
              }}
            />
            <button className="btn btn-primary">Request access <MarketingIcon name="arrow"/></button>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--prism-ink-3)' }}>· no spam, no shouting</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function MarketingFooter() {
  return (
    <footer className="footer">
      <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <img src="../../assets/prism-mark.svg" width="16" height="16" alt=""/>
          <span style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 14 }}>Prism</span>
          <span style={{ marginLeft: 12, color: 'var(--prism-ink-4)' }}>© 2026</span>
        </div>
        <div className="footer-links">
          <a href="#">Manifesto</a>
          <a href="#">Trust &amp; sources</a>
          <a href="#">Changelog</a>
          <a href="#">Privacy</a>
          <a href="#">@prism</a>
        </div>
      </div>
    </footer>
  );
}

Object.assign(window, { Problem, Pillars, HowItWorks, CTAStrip, MarketingFooter });
