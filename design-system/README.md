# Prism — Design System

> Intelligence, refracted for who you are.

Prism is a personal intelligence platform that filters the world through the multiple identities you hold — founder, engineer, researcher, operator — and gives you a daily brief tuned to each. **Same world. Sharper view.**

This design system is the source of truth for everything Prism looks like and sounds like. It is built to scale across surfaces (web app, marketing site, decks, exports) while protecting the core editorial-meets-technical character that makes Prism feel different from generic AI newsletter products.

---

## Sources & references

This system was built from:

- **Brand brief** — strategic positioning provided by founder (multi-lens intelligence; identity-conditioned; synthesis not summary; trust through primary sources).
- **Codebase** — `daily_news_feed/` (Next.js 16 + Tailwind v4 frontend; FastAPI backend). The codebase is currently early-scaffolding fidelity, so the visual system here goes well beyond what is implemented in code today. It is the *target* state.
- **Design document** — `daily_news_feed/DESIGN.md` (architecture, data model, four presentation modes).
- **Adjacent code** — `personal_code/` repos (Stax, Paperlike, tenant-shard-db) consulted for engineering voice and product taste but not used as visual reference.

> ⚠️ The codebase ships with default Geist + generic Tailwind classes. No prior brand-specific design tokens existed. Everything in this system was authored fresh against the brand brief.

---

## Index

| File / folder | What's in it |
|---|---|
| `README.md` | This file. Start here. |
| `SKILL.md` | Agent-Skills front-matter so this folder works inside Claude Code. |
| `colors_and_type.css` | All CSS variables: color, type, spacing, radius, shadow, motion. Plus `.p-*` semantic type classes. |
| `assets/` | `prism-mark.svg`, `prism-mark-mono.svg`, `prism-wordmark.svg`, `spectrum-bar.svg`, and `lens-glyphs/` (one outline glyph per lens). |
| `preview/` | Small HTML cards that document each token — these appear in the Design System tab. 25 cards across Type, Colors, Spacing, Components, Brand. |
| `ui_kits/web_app/` | Interactive recreation of the Prism web app: brief, brief detail, raw discovery, onboarding, profile. Open `index.html`. |
| `ui_kits/marketing/` | One-page marketing site: hero with refraction diagram, problem grid, three pillars, worked example, CTA. Open `index.html`. |
| `screenshots/` | Reference captures from build-time. Safe to ignore. |

> No slide template was provided, so `slides/` was not created. Add later if needed.

---

## Open decisions

A few things flagged during the build that still need a call:

- **Base page tone.** Currently shipping as **Sand** (`#FAF7F2`). User flagged this as common — alternatives explored in `preview/color-base.html` include **Linen, Butter, Blush, Sage, Sky, Terracotta**. Switching is a single-token swap in `colors_and_type.css` (the `--prism-paper` and `--prism-card-edge` family); the spectrum lens colors hold up against all six.
- **Primary tagline.** Three are live in `preview/type-display.html`: *"Intelligence, refracted for who you are."* (primary), *"One world, every lens you need."* (alt), *"Same world. Sharper view."* (utility). Marketing site currently uses the primary in hero, the utility in CTA. Confirm or pick one.

---

## The big idea (visual)

White light enters a prism and refracts into a spectrum. That single image carries the entire product story: **one input (the world) → one tool (Prism) → many tuned outputs (your lenses)**. Everywhere this system can lean on that metaphor — without becoming literal — it does:

- A thin **spectrum bar** appears on lens-tagged surfaces (top of a brief, leading edge of a card).
- Lens-tagged content gets a **single-color accent** (founder = amber, engineer = cyan, etc.) — never a multi-color gradient on a single card.
- The **mark** is a refraction glyph, not a literal triangle.

---

## Content fundamentals

Prism's voice is **editorial, precise, slightly dry, never breathless.** Imagine The Economist's restraint married to Stratechery's directness, written for someone who already knows the basics and resents having their time wasted.

### Tone rules

- **You, not we, not "users."** "Tell Prism the hats you wear." Never "users will be able to…"
- **Direct address, declarative.** "Headlines become decisions." Not "headlines can be turned into decisions."
- **Verbs do the work.** *Reads, extracts, verifies, tunes, mutes.* Avoid "leverages," "empowers," "unlocks," "supercharges."
- **No hype adjectives.** Banned: revolutionary, game-changing, AI-powered, intelligent (as a stand-alone adjective), seamless.
- **Numbers are evidence, not slop.** Quote sources, signal-rates, hours-saved only when they are real and falsifiable. No invented "10x" claims.
- **Confidence without bravado.** "Other tools shrink articles. Prism extracts claims." Stating differences flatly is more credible than calling yourself great.

### Casing & punctuation

- **Sentence case** for headings, buttons, nav, eyebrows. "Daily brief" not "Daily Brief."
- **Em dashes** (—) over commas to set off clauses. Editorial habit.
- **Oxford comma** on.
- Section labels in **uppercase tracked** — only as the rare eyebrow ("BRIEF · TODAY · FOUNDER LENS"). Don't sprinkle.
- Lens names are proper nouns in product UI: *Founder, Engineer, Researcher.* Lowercase in body prose: *"your founder lens."*

### Vocabulary — what Prism calls things

| Use | Don't use |
|---|---|
| Lens (the identity-tuned view) | Channel, feed, profile |
| Brief (the daily output) | Digest, newsletter, summary, briefing |
| Signal (relevant content) | Hits, results, recommendations |
| Noise (auto-muted) | Junk, spam, low-quality |
| Source (primary reference) | Citation, link |
| Claim (extracted statement) | Fact, point, takeaway |
| Thesis (what you're trying to figure out) | Interests, topics, preferences |
| Read, extract, verify, tune, mute | Track, analyze, deliver |

### Copy examples (do this)

> **Founder lens · today**
> Anthropic raised $13B at $183B post. Three signals matter for B2B-fintech-in-India: enterprise revenue mix shifted toward $1M+ contracts, India go-to-market explicitly mentioned in the deck, and the round closed in nine days. *Why this is in your brief →*

> **Three muted this week**
> Substack post-of-the-week threads, Product Hunt launch lists, generic VC year-in-review tweets. Tap to un-mute.

> **Onboarding step 2 of 3**
> Write 2–3 sentences about what you're trying to figure out under this hat. The more specific, the sharper the lens.

### Copy examples (avoid)

> ❌ "Stay ahead with AI-powered insights tailored just for you!"
> ❌ "Discover the latest trends in your industry, fast."
> ❌ "Our intelligent algorithm learns your preferences over time."
> ❌ Emojis in body copy. The product itself does not use emoji.

### Emoji policy

**No emoji in product UI or brand copy.** Iconography handles all the work emoji would do. The one exception: thumbs-up/down feedback buttons can render as small SVG icons styled to match, never as native emoji. This is non-negotiable for the "serious tool for serious work" positioning.

---

## Visual foundations

> Prism's aesthetic is **editorial × technical**. Borrow the typographic rigor of a print magazine. Borrow the data density of a Bloomberg terminal. Throw out the consumer-app conventions in between.

### Palette

Two layers:

1. **Base palette** — warm paper + deep ink. Never pure white (`#FFFFFF`) as page background; never pure black. This warmth is what makes Prism feel hand-set rather than auto-generated.
2. **The Spectrum** — five lens colors, tuned in OKLCH for equal perceptual chroma. Each lens owns *one* hue. They are accents only — they tag content, they never become the page.

### The paper refracts through the day

Prism's base palette is not one tone — it's **five tones that cycle through the day**, applied to `<body>` as a single class. Same lens colors, same ink hierarchy, only the surface shifts.

| Time | Class | Paper | Personality |
|---|---|---|---|
| 05–11h | `.time-morning`   | **Butter**     `#FAF4DE` | warm yellow, golden hour |
| 11–14h | `.time-midday`    | **Sky**        `#ECF0F4` | cool pale blue, clear |
| 14–18h | `.time-afternoon` | **Sage**       `#F0F2E8` | muted green, considered |
| 18–22h | `.time-evening`   | **Terracotta** `#F5EBE2` | warm earthy, settling |
| 22–05h | `.time-night`     | **Linen**      `#F1E8DC` | deep cream, late reading |

All five are light themes — Prism stays a reading product, never goes dark. Every component reads its colors from CSS vars, so the shift cascades everywhere without re-rendering. See `colors_and_type.css` for the per-theme overrides; the web app applies the class in a `useEffect` on mount.

### Lens spectrum

| Lens | Hue family | Token |
|---|---|---|
| Founder | Amber | `--lens-founder` |
| Engineer | Cyan | `--lens-engineer` |
| Researcher | Violet | `--lens-researcher` |
| Operator | Verdant | `--lens-operator` |
| Investor / Scout | Rose | `--lens-investor` |

### Typography

Three families. Each does one job.

- **Newsreader** (serif, optical sizing) — display, h1/h2, lead-ins, italic pull-quotes. Editorial gravitas.
- **Geist** (grotesk) — body, UI, labels, buttons. Neutral and modern.
- **JetBrains Mono** — timestamps, source IDs, scores, anything that should read as "data, not prose."

**The serif italic** is Prism's signature move. Lead paragraphs are italic serif (`p-lead`), pull-quotes are italic serif (`p-quote`), the wordmark uses an italic Newsreader cut. Used sparingly, this is what reads as *intelligence* rather than *web app*.

Headings up to h2 are **Newsreader regular** (not bold). The editorial look depends on serif at regular weight over a light counter. Resist defaulting to bold weights.

### Spacing & rhythm

4px base scale. Editorial layouts breathe — at large sizes use `--s-10` (64px) and up between sections. Density is encouraged *inside* a card; whitespace between cards.

### Backgrounds & surfaces

- **Page**: `--prism-paper` (warm off-white). Never gradients on the page background.
- **Cards**: `--prism-card` (pure white) on paper. The white card on warm paper *is* the depth — no shadow needed.
- **Recessed regions** (e.g. raw-data tables, code blocks): `--prism-paper-2`.
- **Night surfaces** (used for the prism-mark hero strip on marketing, for "now reading" focus mode in app): `--prism-night` with `--prism-night-fg` text. Don't dark-mode the whole app — use night surfaces as deliberate punctuation.

### Imagery

- **Documentary, not illustrated.** Black-and-white or low-saturation photography preferred. People at desks, papers, conference halls, server rooms — the texture of knowledge work.
- **Grain over gloss.** A subtle film grain or duotone is consistent with the editorial brand. No glossy 3D renders, no gradient mesh hero images.
- **The mark itself** (triangular refraction) is the strongest visual asset. Lean on it before reaching for photography.

### Borders, hairlines & dividers

- Hairlines (`--prism-hairline`) do most of the work. Cards bordered, sections separated by 1px rules.
- **No box-shadow on cards** in the default state. Shadows only on **floating** layers — popovers, modals, dropdowns.
- Inputs use **inset 1px** borders, no shadow. Focus state thickens to 2px in `--prism-ink`.

### Shadows & elevation

| Token | Use |
|---|---|
| `--sh-flat` | Hairline only — default for cards, inputs, list items. |
| `--sh-1` | Subtle lift — only used on hover for interactive cards. |
| `--sh-2` | Floating element — dropdowns, tooltips. |
| `--sh-pop` | Modals, dialogs, command palette. |
| `--sh-focus` | Focus ring — 3px halo in 12% ink. |

### Radii

Restrained. **`--r-md` (6px)** is the default for cards, buttons, inputs. **`--r-pill` (999px)** is reserved for chips and lens tags only. Never round a hero card more than 14px — softness undercuts the editorial register.

### Hover & press states

- **Hover** on interactive surfaces: background shifts to `--prism-paper-2` (or +1 step of the same tone). Borders may darken from `--prism-hairline` to `--prism-ink-4`. **Never** brighten an accent color on hover — accents stay constant.
- **Press**: no shrink/scale transforms. A subtle `filter: brightness(0.97)` or background-shift one step deeper. Editorial = solid, not springy.
- **Focus** (keyboard): 3px outer halo `--sh-focus` plus a 2px ink border on inputs. Never remove focus styles.

### Motion

Calm and considered. **No bounces, no springs, no parallax.** Tokens:

- `--dur-fast` (140ms) — hover/focus state transitions.
- `--dur-base` (220ms) — appears/disappears, sheets sliding in.
- `--dur-slow` (420ms) — orchestrated reveals (e.g. the brief opening sequence).
- All easing: `--ease-snap` or `--ease-out`. Snap into final positions; never overshoot.

The one signature motion: **the refraction reveal** — on first load of a brief, a thin white "beam" sweeps across the spectrum bar from left to right (420ms, ease-out), then the lens colors fade in behind it. Used once per session, not on every card.

### Transparency & blur

Used sparingly. The top app bar uses `backdrop-filter: blur(12px)` over a 70% paper tint when content scrolls under it. Modal scrims are flat `rgba(20,19,15,0.45)` — no blur. No frosted glass cards.

### Layout rules

- **Reading width** is 64ch (`--w-reading`). Long-form briefs never go wider.
- **Feed cards** cap at 640px width.
- **App shell** is 1280px max; full-bleed only for documentary photography or the marketing hero.
- Top bar height is fixed at **56px**; side rail at **240px** when expanded, **64px** collapsed.
- Grids: 12-column on marketing, 8-column on app. 24px gutters.

### Lens tagging — the one rule

When content is tagged with a lens, the lens color appears in **exactly one** of these positions, never more than one per card:

- A 3px vertical bar at the leading edge of the card, OR
- A small dot + label in the eyebrow, OR
- A subtle 1px border in the lens color (replacing the hairline).

Stacking accents (e.g. amber bar + amber background + amber text) is the AI-slop pattern this system explicitly rejects.

---

## Iconography

Prism uses **Lucide** (via CDN) as its icon system. Reasoning: Lucide's stroke style (1.5–2px, rounded line joins, geometric) matches the editorial-technical pairing — it reads as careful drafting rather than glyph-y or cute. The 24×24 viewbox at 16–20px display size is the default.

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<i data-lucide="lens"></i>
```

> ⚠️ **Substitution flag.** No icons were defined in the upstream codebase. Lucide is a defensible default for a product of this character. Swap to a paid family (e.g. Phosphor Duotone, Streamline) if the brand ever moves more luxe.

### Icon usage rules

- Display at **16px** (inline with body), **20px** (inline with h3/h4), **24px** (standalone, in toolbars).
- Stroke color: `currentColor` always — icons inherit text color, never hard-code.
- **No filled icons** in the main UI. Outline only. Filled variants reserved for the "selected" state of a toggle.
- Custom icons (e.g. the lens glyph, the prism mark) live in `assets/` as SVG; everything else is Lucide.

### What's in `assets/`

- `prism-mark.svg` — the refraction triangle (favicon, app icon, marketing mark).
- `prism-wordmark.svg` — italic Newsreader "Prism" with mark on left.
- `prism-mark-mono.svg` — single-color version for dark surfaces.
- `lens-glyphs/*.svg` — five custom glyphs for the five lenses.
- `spectrum-bar.svg` — the canonical spectrum gradient strip used on briefs.

### Emoji & unicode

**No emoji.** No unicode symbols masquerading as icons (no ▸, ★, ●). Use Lucide. The only allowed "glyph" outside Lucide is the em-dash and en-dash, used in copy.

---

## SKILL.md

This folder is structured to work as a downloadable [Claude Code Agent Skill](https://docs.anthropic.com/en/docs/build-with-claude/skills). See `SKILL.md` for the front-matter.
