# GitHub Copilot Instructions

This repository contains solution architecture case studies used for professional development and mentorship exercises. Documents are written in AsciiDoc and rendered to HTML via Kroki (PlantUML, D2, Structurizr). Each case study contains a proposal, a full solution design, a decision brief, and supporting diagrams.

---

## Client-Facing Language

Client-facing documents include: solution designs (`.adoc`), proposals, and decision briefs located in `<exercise>/docs/`.

Never include internal or work-in-progress language in client-facing documents. This includes:
- "this figure has not been confirmed by the client"
- "must be replaced before use"
- "TODO: replace with actual value"
- "unconfirmed assumption"
- `:status: Draft`

When a value is illustrative or assumed, frame it professionally:
- ✅ "using an illustrative average basket of $15; projections scale proportionally to your actual average order value"
- ✅ "based on an estimated X — to be calibrated during the Investigation Period"
- ✅ "to be validated with the compliance team during the Phase 1 compliance workshop"

If an assumption is a blocker, raise it in a discovery questionnaire or Next Steps table — not as a NOTE in the document body.

### Discovery Questionnaires

Questionnaires in `<exercise>/questionnaire/` may use `❓` markers and `TBD` to flag items requiring client input. This is intentional — questionnaires are meant to surface open questions.

### AI-Generated Documents

AI-assisted reviews and self-assessments live in `<exercise>/ai-documents/`. They are **not** client-facing deliverables.

- Label with `**Type:** AI-assisted ...` in the document header.
- Use `**Author:** <name>` — not a fictional reviewer role.
- Never place AI-generated reviews in `docs/` alongside client-facing documents.
- Naming convention: `architecture-review.md`, `architecture-challenge.md`, `self-assessment.md`.

---

## Table Formatting

All important information belongs inside the table. Do not place explanatory paragraphs, caveats, or summaries below the closing `|===`.

- ✅ Add a spanning notes row as the last row inside the table: `4+|_note text_`
- ❌ Italic or bold paragraph after `|===`
- If a note must stand alone, place it **above** the table, never below.

---

## Document Structure — Proposal vs. Solution Design

| Content | Document |
|---|---|
| Business goals, growth levers, revenue projections | Proposal |
| Architecture decisions, functional requirements, risk register, cost breakdown | Solution design |

Do not duplicate strategic content between documents. The proposal sells; the solution design delivers.

All solution designs follow the standard section order: Glossary → Executive Summary → Problem Statement → Solution Options → Cost Breakdown → Risks & Assumptions → Architecture Decisions (ADRs) → Deployment → Post-Launch Plan → Next Steps.

ADR format: Context → Decision → Rationale (options considered with explicit rejection reasons).

---

## Proposal Conventions

- Do not ask the client for any actions or data before the engagement agreement is signed.
- All pre-work (data samples, vendor access, workflow audit) belongs in the post-signing **Investigation Period**.
- Always include an Investigation Period as the first post-signing phase (2–4 weeks): current workflow documentation, data quality baseline, risk identification, improvement opportunities. Concludes with a written report and validated Phase 1 plan.
- When a client states a revenue or growth target, decompose it into multiple levers with estimated contributions per lever — not a single mechanism.

---

## Diagram Readability (PDF-safe)

Diagrams must be legible at standard A4/Letter width in PDF export.

**PlantUML:**
- `skinparam defaultFontSize 14` minimum; 16 for executive/proposal diagrams
- `skinparam sequenceArrowFontSize 13`
- Gantt: `zoom 3` minimum; task FontSize 13+; separator FontSize 14+

**D2:**
- `style.font-size: 14` on container groups, `13` on leaf nodes
- Labels must not exceed ~25 characters; use `\n` for line breaks
- Add `vars: { d2-config: { layout-engine: elk } }` for better spacing

**Structurizr (C4):**
- Do not add `configuration { styles { ... } }` — the Kroki renderer returns 400 for it

---

## AsciiDoc Conventions

- Table column count in `[cols="..."]` must match the number of cells in the header row.
- Use `options="header"` on all tables.
- Spanning cells: `N+|content` spans N columns.
- Diagrams are defined inline as fenced blocks: `[plantuml,name,format=svg]`, `[d2,name,format=svg,layout=elk]`, `[structurizr,name,format=svg,view-key=key]`.

---

## Repository Layout

```
<exercise-number>/
  assignment/         Internal notes and meeting summaries
  docs/               Client-facing deliverables (solution-design.adoc, domain-primer.adoc, etc.)
  ai-documents/       AI-assisted reviews and challenge documents (NOT client-facing)
  questionnaire/      Discovery questionnaires with pre-filled assumptions
template/             Reusable AsciiDoc and Markdown templates
```
