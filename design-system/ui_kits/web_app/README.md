# Prism — web app UI kit

This is a click-thru recreation of the Prism web app, built from the brand brief + the early scaffolding in `daily_news_feed/frontend/`. Open `index.html` to interact.

## What's covered

The kit demonstrates the five canonical screens:

- **Daily brief** — the morning view. Spectrum header strip + five lens-tagged brief cards. Filter by lens with the pill switcher.
- **Brief detail** — open any card. Spectrum band, large display title, italic lead, mode toggle (News / Explainer basics / Explainer delta / Discussion), extracted claims with primary-source citations, tune-this-brief feedback row.
- **Raw discovery** — every annotated item from the lake, filterable by source, with mono scores. Tap a row to disagree with the AI's annotation.
- **Onboarding (step 2 of 3)** — declare your hats. Italic-serif thesis previews per lens.
- **Profile / settings** — manage lenses, see what was auto-muted this week.
- **Lens-only views** (Founder / Engineer / Researcher) — same brief cards, filtered to one identity, with the lens's color tinting the header band.

## Files

| File | What it is |
|---|---|
| `index.html` | App shell + click-thru router. Open this. |
| `app.css` | All app styles. Imports `../../colors_and_type.css`. |
| `AppShell.jsx` | Sidebar + top bar with search. |
| `BriefCard.jsx` | The hero card, `LensSwitcher`, `ModeToggle`, `FeedbackRow`. |
| `Screens.jsx` | The five screen components. |
| `Icons.jsx` | Inline outline icons (Lucide-style). |
| `data.jsx` | Sample briefs + raw items written in Prism's voice. |

## Conventions

- All sizing/color/type come from `colors_and_type.css` tokens. No hard-coded hex outside the foundations file.
- Lens metadata lives in one place: `LENSES` array in `AppShell.jsx`. Add a sixth identity by extending that array.
- Each brief is tagged with a single lens; the card surfaces it as a 3px leading accent + a soft eyebrow dot. That's the **one-rule lens tagging** the README enforces — never stack accents.
- Icons are inline SVG, not Lucide CDN, to keep the kit offline-runnable. In production, swap to `lucide-react` or the Lucide UMD; the names match.

## Open questions

- The brief-detail mode toggle currently shows synthetic content for each mode. Real product behaviour is to call the backend on first click and cache the result (see `DESIGN.md` R5). The visual structure is correct; the call wiring is out of scope for the kit.
- Saved / Settings are stub views. Add the saved-briefs list when product needs it.
