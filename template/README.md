# Solution Architecture Template Suite

A professional, modular template suite for creating solution architecture documents. Blends best practices from **arc42**, **C4 Model**, **TOGAF**, and **AWS Well-Architected Framework**.

---

## Template Files

| File | Purpose |
|------|---------|
| [`solution-design-template.adoc`](solution-design-template.adoc) | Main solution design document — the primary deliverable |
| [`architecture-questionnaire-template.md`](architecture-questionnaire-template.md) | Requirements intake questionnaire (fill out first) |
| [`adr-template.adoc`](adr-template.adoc) | Architecture Decision Record template (one per decision) |

## Quick Start

### 1. Gather Requirements

Copy `architecture-questionnaire-template.md` into your project and fill it out with stakeholders. Every questionnaire section cross-references the corresponding design section (→ §N).

### 2. Start the Solution Design

Copy `solution-design-template.adoc` into your project. The template is modular:

- **Core sections (§1–§13):** Always include — minimum viable solution design.
- **Optional sections (§14–§25):** Include based on project complexity. Each marked with `// OPTIONAL`.

### 3. Record Decisions

For each significant design decision, copy `adr-template.adoc` and name it:
```
docs/adr/adr-001-short-title.adoc
```
Link ADRs from the summary table in the solution design (§ Architecture Decision Records).

### 4. Render the Document

```bash
# Start Kroki diagram server (from repository root)
docker-compose up -d

# Render to HTML
npx asciidoctor -r asciidoctor-kroki solution-design.adoc

# Open result
start solution-design.html        # Windows
open solution-design.html          # macOS
xdg-open solution-design.html     # Linux
```

---

## Project Complexity Guide

Which template sections to include:

| Section | Small | Medium | Large |
|---------|:-----:|:------:|:-----:|
| Stakeholders & RACI | ✓ | ✓ | ✓ |
| Executive Summary | ✓ | ✓ | ✓ |
| Architecture Principles | — | ✓ | ✓ |
| Problem Statement | ✓ | ✓ | ✓ |
| C4 Context (Level 1) | ✓ | ✓ | ✓ |
| C4 Container (Level 2) | — | ✓ | ✓ |
| C4 Deployment | — | — | ✓ |
| Component Architecture | ✓ | ✓ | ✓ |
| Data Architecture | — | ✓ | ✓ |
| Key Flows | ✓ | ✓ | ✓ |
| Options Comparison | ✓ | ✓ | ✓ |
| Security Architecture | — | ✓ | ✓ |
| API Design | — | ✓ | ✓ |
| Deployment & Infrastructure | — | — | ✓ |
| Observability | — | — | ✓ |
| Business Process Flows | — | ✓ | ✓ |
| Entity Lifecycle | — | — | ✓ |
| Feature Breakdown | — | ✓ | ✓ |
| Migration & Transition | — | — | ✓ |
| ADRs | — | ✓ | ✓ |

---

## Diagram Engines

All diagrams render via **Kroki** (self-hosted). The five engines used are built into the `yuzutech/kroki` container — no additional setup required beyond `docker-compose up`.

| Engine | Use Case | AsciiDoc Block | Count |
|--------|----------|----------------|:-----:|
| **Structurizr** | C4 Context, Container, Deployment — shared model, multiple views | `[structurizr,format=svg,view-key=X]` | 3 |
| **D2** | Component architecture, infrastructure topology, observability stacks | `[d2,format=svg,layout=elk]` | 3 |
| **PlantUML** | Sequence, activity, state, Gantt, mind map, WBS | `[plantuml,format=svg]` | 8 |
| **Erd** | ER data model (Chen notation) | `[erd,format=svg]` | 1 |
| **Vega-Lite** | Cost comparison charts, capacity planning | `[vegalite,format=svg]` | 1 |

**Total: 16 diagrams** across 5 engines.

### Why Multiple Engines?

Each engine excels at a specific diagram type:
- **Structurizr DSL**: Define a C4 model once, render context/container/deployment views via `view-key`
- **D2**: Modern layout engine (ELK), nested grouping, professional visual style
- **PlantUML**: Industry standard for behavioral diagrams with rich feature set
- **Erd**: Purpose-built for ER diagrams with clean Chen notation
- **Vega-Lite**: Declarative JSON for statistical charts — no drawing, just data

---

## Infrastructure

The `docker-compose.yml` in the repository root provides:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| kroki | `yuzutech/kroki` | 8000 | Main gateway — routes to all engines |
| plantuml | `plantuml/plantuml-server:jetty` | 8080 | PlantUML + Structurizr rendering |
| mermaid | `yuzutech/kroki-mermaid` | 8002 | Mermaid rendering (available if needed) |

D2, Erd, Vega-Lite, and GraphViz are all built into the main `kroki` container.

---

## Audience Layering

The template serves three audience levels:

| Audience | Key Sections |
|----------|-------------|
| **Executive** | Stakeholders, Executive Summary (with Recommendation at a Glance), Options Comparison |
| **Architect** | + C4 Views, Component Architecture, Data Model, Security, Quality Scenarios |
| **Developer** | + Key Flows (sequence), API Design, Entity Lifecycle, ADRs, Technical Deep Dives |

---

## Frameworks Blended

| Framework | Contribution |
|-----------|-------------|
| **arc42** | Quality scenarios, building block view, cross-cutting concepts |
| **C4 Model** | Context → Container → Deployment progressive zoom |
| **TOGAF** | Architecture principles, stakeholder management, transition planning |
| **AWS Well-Architected** | Security, reliability, performance, cost, operational excellence pillars |
