---
name: prism-design
description: Use this skill to generate well-branded interfaces and assets for Prism — the personal intelligence platform that refracts the world through the multiple identities its user holds (founder, engineer, researcher, operator, investor). Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping and production work.
user-invocable: true
---

# Prism design skill

Read `README.md` in this folder first. It is the source of truth for brand voice (the **CONTENT FUNDAMENTALS** section), visual foundations (the **VISUAL FOUNDATIONS** section), and how the system fits together.

Then open the other files as needed:

- `colors_and_type.css` — all tokens. Import this everywhere you build with Prism.
- `assets/` — logos, lens glyphs, spectrum bar, prism mark.
- `preview/` — reference cards documenting every token.
- `ui_kits/web_app/` — interactive recreation of the Prism web app. Reuse components or copy patterns.
- `ui_kits/marketing/` — public-facing layout patterns.

## How to use this skill

**If creating visual artifacts** (slides, mocks, throwaway prototypes, briefs to show stakeholders): copy assets out of `assets/` into your output folder, import `colors_and_type.css`, and use the `.p-*` semantic type classes plus the lens tokens (`--lens-founder`, etc.). Look at the `preview/` cards for canonical usage of every token. Lean on the UI kits for ready-made component patterns.

**If working on production code** (the actual Prism web app codebase at `daily_news_feed/frontend/`): read this folder to become an expert on the brand, then translate the tokens into your project's chosen system (Tailwind theme, CSS vars, Linaria, etc.). Components in `ui_kits/` are intentionally simple visual recreations — they are reference, not production code.

## If invoked without further guidance

Ask the user what they want to build or design. A few good probing questions:

- What surface? (App screen, marketing page, brief PDF export, social card, slide deck, internal doc?)
- Which lens(es) are in scope? (Founder / Engineer / Researcher / Operator / Investor)
- Is this for a real product moment, a pitch, or a one-off prototype?
- Do they want to stay strictly inside the foundations, or push the brand into new territory? (If the latter — propose, don't assume.)

Then act as an expert Prism designer. Output HTML artifacts for one-off / visual work, or production-ready code if integrating with the codebase. Always cite which tokens you used so the user can verify.

## The one rule you must never break

**No emoji in product UI.** No `:rocket:`, no `🎯`, no unicode pictograms. Lucide outline icons or custom SVG only. This is non-negotiable for Prism's "serious tool for serious work" positioning. See ICONOGRAPHY in the README for the full icon policy.
