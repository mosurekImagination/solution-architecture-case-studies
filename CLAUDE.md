# Project Conventions

## Document Authoring

### Client-Facing Language
Never include internal or work-in-progress language in client-facing documents (proposals, solution designs, decision briefs). This includes phrases like:
- "this figure has not been confirmed by the client"
- "must be replaced before use"
- "TODO: replace with actual value"
- "unconfirmed assumption"

When a value is illustrative or assumed, frame it professionally:
- ✅ "using an illustrative average basket of $15; projections scale proportionally to your actual average order value"
- ✅ "based on an estimated X — to be calibrated in Phase 1"

If an assumption is a blocker, raise it in a discovery questionnaire or Next Steps table — not as a NOTE inside the document body.

### Table Formatting

All important information must be contained within the table. Do not place explanatory paragraphs or caveats below a table — move them inside as a spanning notes row. If a note must stand alone, place it **above** the table, never below.

- ✅ Add a spanning `4+|_note text_` row as the last row inside `|===`
- ❌ Italic or bold paragraph after the closing `|===`

### Document Structure — Proposal vs. Solution Design

Business goals analysis, growth strategy, and translation of client targets (e.g. "20% turnover increase") into growth options and revenue projections belong in the **proposal**. The solution design focuses on technical architecture, requirements, and cost detail.

- Business goals, growth levers, revenue scenarios → **proposal**
- Architecture decisions, functional requirements, risk register, cost breakdown → **solution design**

### Proposal Conventions

- Do not ask the client for any actions before the engagement agreement is signed. All pre-work (data samples, vendor access confirmation, workflow audit) belongs inside the post-signing Investigation Period.
- Always include an **Investigation Period** as the first post-signing phase: 2–4 weeks of structured discovery covering current workflows, data quality baseline, risk identification, and additional improvement opportunities. It concludes with a written report and validated Phase 1 plan.

### Diagram Readability (PDF-safe)

Diagrams must be legible when exported to PDF at standard A4/Letter page width. Apply these defaults:

**PlantUML:**
- `skinparam defaultFontSize 14` minimum (16 for executive/proposal diagrams)
- `skinparam sequenceArrowFontSize 13`
- Gantt: `zoom 3` minimum; task FontSize 13+; separator FontSize 14+

**D2:**
- `style.font-size: 14` on container groups, `13` on leaf nodes
- Labels must not exceed ~25 characters; use `\n` for line breaks
- Add `vars: { d2-config: { layout-engine: elk } }` for better spacing

**Structurizr (C4):**
- The Kroki renderer does not support `configuration { styles { ... } }` — do not add it

## AI-Generated Documents

AI-assisted reviews, challenge documents, and self-assessments are stored in an `ai-documents/` subfolder within each case study (e.g., `03/ai-documents/`). These files are **not** client-facing deliverables.

- Always label them with `**Type:** AI-assisted ...` in the document header.
- Never place AI-generated content in `docs/` alongside client-facing solution designs.
- Naming convention: `architecture-review.md`, `architecture-challenge.md`, `self-assessment.md`.
- The author field should reflect the human author (`**Author:** <name>`), not a fictional reviewer role.
