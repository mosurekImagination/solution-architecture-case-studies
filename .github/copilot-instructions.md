# Copilot Instructions — Solution Architecture Mentoring Program

## About This Repository

This is a **Software Solution Architecture Mentoring Program** workspace. Each numbered directory (`01/`, `02/`, ...) contains a case study assignment where the student receives a client brief, analyzes it, asks clarifying questions, and produces a full solution architecture.

## Program Workflow

Each assignment typically follows this process:

1. **Receive client brief** — informal, often incomplete description of what the client wants
2. **Formulate questions** — identify gaps, but frame them as assumptions to verify/deny (never throw raw questions at the client)
3. **Design the solution** — assumptions, component design, cost breakdown, milestones, diagrams
4. **Meet with mentor** — present work, receive feedback captured in `notes` file
5. **Iterate** — improve based on mentor feedback

## Directory Structure per Case Study

```
XX/
├── assignment/          # Client brief, meeting notes, mentor feedback
│   ├── meeting-N.adoc   # Meeting notes in AsciiDoc
│   ├── key-informations.md
│   └── notes            # Raw mentor feedback (plain text, no extension)
├── diagrams/            # Python scripts using `diagrams` library + generated PNGs
│   ├── option-N-description.py   # Architecture diagrams (diagrams library)
│   ├── timeline-N-description.py # Gantt charts (matplotlib via shared/gantt.py)
│   └── cost-N-description.py     # Cost tables (matplotlib via shared/cost_table.py)
├── docs/                # Deliverables — user stories, design docs
│   └── user-stories.adoc
└── questionnaire/       # Filled architecture questionnaire
    ├── architecture-questionnaire.md       # Full internal version
    └── architecture-questionnaire-short.md # Short client-facing version
```

### Shared Module (`shared/`)
```
shared/
├── __init__.py
├── gantt.py             # Reusable Gantt chart generator (matplotlib)
└── cost_table.py        # CAPEX/OPEX table + cost comparison renderer (matplotlib)
```

## Document Format Conventions

- **AsciiDoc (`.adoc`)** — structured documents: meeting notes, user stories
- **Markdown (`.md`)** — questionnaires, key information, learnings
- **Plain text (no extension)** — raw mentor feedback (`notes` files)
- **Python (`.py`)** — architecture diagrams using `diagrams` library, timeline/cost charts using `matplotlib`

## Diagram Conventions

- Diagrams use the [diagrams](https://diagrams.mingrammer.com/) Python library (v0.23.4) with Graphviz
- Run via Docker: `./generate-diagrams.sh [XX]` (or `all`)
- Scripts go in `XX/diagrams/`, output PNGs land in the same folder
- Naming: `option-N-description.py` (e.g., `option-1-mvp.py`, `option-2-progressive.py`)
- Each diagram file starts with a docstring: timeline, budget (CAPEX + OPEX), region, feature summary
- Use `graph_attr`, `node_attr`, `edge_attr` for consistent styling
- Use `Cluster()` for logical grouping, `Edge(label=...)` for protocol/purpose annotations
- Include cost annotations where relevant

## Timeline & Cost Visualization

- Gantt charts and cost tables use `matplotlib` via shared helpers in `shared/` module
- `shared/gantt.py` — `create_gantt_chart()` for project timelines with parallel streams and milestones
- `shared/cost_table.py` — `create_capex_table()`, `create_opex_table()`, `create_cost_summary()` for cost breakdowns
- Timeline scripts named `timeline-{option}.py`, cost scripts named `cost-{option}.py`
- Same Docker workflow as architecture diagrams: `./generate-diagrams.sh [XX]`

## Key Mentoring Principles (from learnings.md)

1. **Never throw raw questions at the client** — provide an assumption and ask to verify or deny it. Example: "I assume your application will be popular → we need to prepare for scaling. Is that correct?"
2. **Balance the number of questions** — too many open questions will overwhelm the client
3. **Provide proof/eligibility for choices** — when presenting options, justify why you recommend one
4. **Cost estimation** — use developer-price × time (not by module), show timeline with parallelizable work (Gantt chart), account for risk (20-50% buffer), limit 3-4 devs per stream
5. **Push system boundaries** — edge cases reveal gaps and generate questions naturally
6. **Milestone structure** — POC → MVP → Full Release → Future, with clear feature mapping to each phase

## Architecture Questionnaire

The blank template is at `architecture-questionnaire-template.md` (root). Each case study fills it in under `XX/questionnaire/`. The template covers 10 sections: Business Context, Functional Requirements, NFRs, Technical Requirements, Architecture Patterns, Infrastructure & Deployment, Observability, DR/BC, Constraints & Assumptions, Future Considerations.

## User Story Format

User stories follow AsciiDoc format with:
- Epic grouping (`== Epic N: Name`)
- Story ID pattern: `US-{epic}.{sequence}.{global_id}`
- "As a / I want to / So that" structure
- Acceptance criteria as bullet lists
- Priority classification: `MUST HAVE (POC)`, `MUST HAVE (MVP)`, `SHOULD HAVE (MVP)`, `COULD HAVE (Full)`, `WON'T HAVE (Future)`

## When Helping with This Repository

- Follow all conventions above for file naming, formats, and directory structure
- Reference the questionnaire template sections as a thinking framework when designing solutions
- Always consider NFRs: performance, scalability, availability, security, data
- Propose multiple architecture options when appropriate (different scale/cost tiers)
- Frame questions as assumptions to verify, not open-ended questions
- Include cost considerations in architecture decisions
