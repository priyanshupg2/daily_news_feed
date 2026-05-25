# Prism — marketing site UI kit

A single-page marketing recreation that demonstrates how Prism's foundations translate to public-facing copy + layout. Open `index.html`.

## Sections (top to bottom)

1. **Nav** — Wordmark + 4 links + Sign in / Get early access.
2. **Hero** — "Intelligence, refracted for who you are." Paired with the **refraction diagram**: a white beam enters a prism and exits as five labeled lens beams, each leading to a real example brief title.
3. **Problem grid** — Four cards naming the competition (Generic AI, Consumer news, Enterprise intel, The firehose) with one-line dismissals.
4. **Three pillars** — Multi-lens / Synthesis / Sources. Big numerals, editorial setting.
5. **Worked example** — Three lens cards (Founder / Engineer / Researcher) showing how the same person gets three different briefs.
6. **CTA strip** — Spectrum-capped panel with an email capture. "Same world. Sharper view."
7. **Footer** — Minimal links.

## Files

| File | What it is |
|---|---|
| `index.html` | The site. Open this. |
| `site.css` | Marketing styles. Imports `../../colors_and_type.css`. |
| `Hero.jsx` | Nav, hero block, refraction diagram. |
| `Sections.jsx` | Problem, pillars, how-it-works, CTA, footer. |

## Notes

- Designed at 1280px width. Padding gracefully collapses below 800px but a real responsive pass is out of scope for the kit.
- All copy reflects Prism's editorial voice — see CONTENT FUNDAMENTALS in the root `README.md`. No "AI-powered," no "leverage," no exclamation marks.
- The refraction diagram is the strongest brand asset here. Reuse it (resized) on About pages, social cards, deck title slides.
