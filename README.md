# Solution Architecture Case Studies

This repository contains solution architecture case studies with diagrams rendered using [Kroki](https://kroki.io/) — a unified API for diagram-as-code tools. Architecture diagrams are written in **PlantUML**, timelines in **Mermaid**, and cost tables as native **AsciiDoc tables** — all inline in the `.adoc` documents.

## Project Structure

Each case study is organized in its own numbered directory:

```
.
├── 01/              # Case Study 01
│   ├── assignment/  # Assignment brief and notes
│   ├── docs/        # Solution design (AsciiDoc with inline diagrams)
│   └── questionnaire/
├── docker-compose.yml   # Kroki server (PlantUML + Mermaid)
└── README.md
```

## Quick Start

**Prerequisites:** Docker and Docker Compose installed
- [Install Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)

**Start Kroki server:**
```bash
docker-compose up -d
```

Kroki will be available at `http://localhost:8000`.

**Render the AsciiDoc document:**

Install Asciidoctor with the Kroki extension:
```bash
gem install asciidoctor-kroki
```

Generate HTML:
```bash
asciidoctor -r asciidoctor-kroki 01/docs/solution-design.adoc
```

Or use the VS Code [AsciiDoc extension](https://marketplace.visualstudio.com/items?itemName=asciidoctor.asciidoctor-vscode) with Kroki support for live preview.

## Diagram Tools

| Diagram Type | Tool | Format |
|---|---|---|
| Architecture diagrams | PlantUML (via Kroki) | Inline in `.adoc` |
| Timeline / Gantt charts | Mermaid (via Kroki) | Inline in `.adoc` |
| Cost tables (CAPEX/OPEX) | Native AsciiDoc tables | Inline in `.adoc` |

All diagrams are defined as code directly in the AsciiDoc source files — no separate diagram files or generation scripts needed.

## Stop Kroki

```bash
docker-compose down
```