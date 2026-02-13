# Solution Architecture Case Studies

A repository of solution architecture case studies and a professional **template suite** for creating solution design documents. Templates blend best practices from **arc42**, **C4 Model**, **TOGAF**, and **AWS Well-Architected Framework**. All diagrams are code — rendered inline via [Kroki](https://kroki.io/).

## Project Structure

```
.
├── template/                              # Reusable template suite
│   ├── solution-design-template.adoc      # Full design — 25 sections, 16 diagrams
│   ├── solution-design-compact-template.adoc  # Compact — 8 sections, ~15 min meeting
│   ├── architecture-questionnaire-template.md # Requirements intake questionnaire
│   ├── adr-template.adoc                  # Architecture Decision Record template
│   ├── life-lessons.md                    # Consulting wisdom & non-obvious lessons
│   └── README.md                          # Template usage guide
├── 01/                                    # Case Study 01
│   ├── assignment/                        # Assignment brief and notes
│   ├── docs/                              # Solution design & user stories
│   └── questionnaire/                     # Filled questionnaire
├── docker-compose.yml                     # Kroki server (PlantUML + Mermaid)
├── render.sh                              # Render all .adoc → HTML
├── learnings.md                           # Raw project learnings
└── README.md
```

## Quick Start

### 1. Start Kroki diagram server

```bash
docker-compose up -d
```

Kroki will be available at `http://localhost:8000`. Health check: `curl http://localhost:8000/health`

### 2. Render documents to HTML

```bash
# Render all .adoc files (output goes to output/ directory)
./render.sh

# Render only templates
./render.sh template

# Render a specific case study
./render.sh 01

# Check prerequisites without rendering
./render.sh --check
```

HTML output mirrors the source structure inside `output/`:
```
output/
  template/
    solution-design-template.html
    solution-design-compact-template.html
    adr-template.html
  01/docs/
    solution-design.html
    user-stories.html
```

### 3. Prerequisites

- **Docker & Docker Compose** — for Kroki diagram server
- **Node.js + npm** — for `npx asciidoctor` rendering
- **npm packages** — `npm install asciidoctor asciidoctor-kroki` (or let `npx` handle it)

## Template Suite

| File | Purpose | Audience |
|------|---------|----------|
| [`solution-design-template.adoc`](template/solution-design-template.adoc) | Full solution design — 25 sections, 16 diagrams | Architects, developers |
| [`solution-design-compact-template.adoc`](template/solution-design-compact-template.adoc) | Compact — 8 sections, 4 diagrams (~15 min meeting) | Executives, stakeholders |
| [`architecture-questionnaire-template.md`](template/architecture-questionnaire-template.md) | Requirements intake questionnaire with pre-fill guidance | Solution architects |
| [`adr-template.adoc`](template/adr-template.adoc) | Architecture Decision Record (one per decision) | Architects, tech leads |
| [`life-lessons.md`](template/life-lessons.md) | Non-obvious consulting wisdom — estimation, risk, stakeholders | Everyone |

**Workflow:** Questionnaire → Solution Design (full or compact) → ADRs for key decisions.

See [`template/README.md`](template/README.md) for detailed usage, section guide, and complexity matrix.

## Diagram Engines

All diagrams render via **Kroki** — 5 engines, all built into the `yuzutech/kroki` container:

| Engine | Use Case | AsciiDoc Syntax |
|--------|----------|-----------------|
| **Structurizr** | C4 Context, Container, Deployment (shared model) | `[structurizr,format=svg,view-key=X]` |
| **D2** | Component architecture, infrastructure, observability | `[d2,format=svg,layout=elk]` |
| **PlantUML** | Sequence, activity, state, Gantt, mind map, WBS | `[plantuml,format=svg]` |
| **Erd** | ER data model (Chen notation) | `[erd,format=svg]` |
| **Vega-Lite** | Cost comparison charts | `[vegalite,format=svg]` |

## Infrastructure (docker-compose)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| kroki | `yuzutech/kroki` | 8000 | Main gateway — routes to all engines |
| plantuml | `plantuml/plantuml-server:jetty` | 8080 | PlantUML + Structurizr rendering |
| mermaid | `yuzutech/kroki-mermaid` | 8002 | Mermaid rendering |

All services have `restart: unless-stopped` and Kroki includes a healthcheck.

D2, Erd, Vega-Lite, and GraphViz are built into the main `kroki` container.

## Stop Kroki

```bash
docker-compose down
```