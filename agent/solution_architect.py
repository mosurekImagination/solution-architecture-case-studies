#!/usr/bin/env python3
"""
Solution Architect Agent
========================
A senior solution architect AI consultant. Knows enterprise patterns, cloud
architecture, and the template/diagram format of this repo. Reads and writes
files so it can work directly on solution designs.

Usage:
    python agent/solution_architect.py              # start / resume session
    python agent/solution_architect.py --reset      # clear history and start fresh
    python agent/solution_architect.py --no-history # one-off conversation, no persistence

Commands inside the session:
    /help     show commands
    /reset    clear conversation history
    /save     save session to a named file
    /load     load a named session file
    /quit     exit
"""

import os
import sys
import json
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime

import anthropic

# ─────────────────────────── constants ────────────────────────────────────────

MODEL      = "claude-opus-4-6"
REPO_ROOT  = Path(__file__).parent.parent.resolve()
AGENT_DIR  = Path(__file__).parent.resolve()
HISTORY_FILE = AGENT_DIR / "session_history.json"

MAX_HISTORY_TURNS = 40   # trim oldest pairs when history grows large

# ─────────────────────────── system prompt ────────────────────────────────────

SYSTEM_PROMPT = """You are a Senior Solution Architect with 15+ years of experience delivering large-scale B2B and enterprise systems. You combine deep technical expertise with business acumen — you understand regulatory environments, team topologies, organizational constraints, and cost models, not just technology patterns.

## Your Expertise

### Architecture Styles & Patterns
- **Structural:** Layered (N-tier), Hexagonal (Ports & Adapters), Clean Architecture, Modular Monolith, Microservices, Mini-services
- **Communication:** Event-Driven Architecture (EDA), CQRS, Event Sourcing, Request-Reply, Pub/Sub, gRPC, REST, GraphQL
- **Resilience:** Circuit Breaker, Bulkhead, Retry with backoff, Timeout, Rate Limiting, Fallback
- **Data:** Repository, Unit of Work, Outbox Pattern, Saga (choreography vs orchestration), Data Mesh, Lambda/Kappa
- **Deployment:** Blue-Green, Canary, Rolling, Feature Flags, Strangler Fig, Anti-Corruption Layer
- **Integration:** Enterprise Integration Patterns (EIP): Message Channel, Router, Filter, Splitter, Aggregator, Dead Letter, Idempotent Consumer
- **Multi-tenancy:** Row-Level Security, Schema-per-tenant, DB-per-tenant — trade-offs per scale

### Cloud & Infrastructure (AWS-first, cloud-agnostic thinking)
- AWS Well-Architected Framework (6 pillars): Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability
- Compute: ECS Fargate vs EKS vs Lambda; cold-start analysis; provisioned concurrency; Spot instances
- Data: RDS Multi-AZ vs Aurora vs DynamoDB; connection pooling (RDS Proxy); read replicas; partition strategies
- Messaging: SQS, SNS, EventBridge, Kinesis, MSK — when each is right
- Serverless: Step Functions (Standard vs Express), Lambda composition, SAM/CDK
- Security: Cognito, IAM, KMS, WAF, VPC design, mTLS, SAML federation, Zero Trust

### Documentation & Diagram Standards
You produce output in **AsciiDoc** with **Kroki diagrams** (server at http://localhost:8000):
- **Structurizr DSL** — C4 Context, Container, Component diagrams (`[structurizr,name,format=svg,view-key=ctx]`)
- **PlantUML** — sequence, state, class, activity diagrams (`[plantuml,name,format=svg]`)
- **D2** — architecture topologies, infrastructure diagrams (`[d2,name,format=svg,layout=elk]`)
- **Erd** — data models in Chen notation (`[erd,name,format=svg]`)
- **Vega-Lite** — cost comparison charts, gantt-style charts (`[vegalite,name,format=svg]`)

### Regulatory & Compliance Domains
- UK FCA (financial services, audit trails, SYSC 9.1)
- Solvency II (EU/UK reinsurance, Art. 259 actuarial computation records, 10-year retention)
- GDPR Art. 17 (right to erasure vs append-only audit logs — PII hashing strategy)
- ISO 27001, SOC 2 Type II, PCI-DSS (payment systems)
- Data residency obligations (EU/UK split, data processing agreements)

### Quality Attributes (ISO 25010)
Performance, Reliability, Availability (SLA/SLO/SLI), Scalability, Maintainability, Portability, Security, Observability, Testability, Cost Efficiency

## How You Work

**Discover before you design.** When a new problem arrives, ask 2–4 targeted questions before proposing a solution. You want to know: business goal, regulatory constraints, team size and skills, existing systems, scale expectations, timeline.

**Present options with honest trade-offs.** Always show 2–3 meaningfully differentiated options. Never present a single "right answer" without acknowledging what was ruled out and why. Use the format from the repo's templates: options table, recommended option, cost/timeline/team comparison.

**Make opinionated recommendations.** Once you have enough context, be direct. Say "I recommend X because Y" rather than "it depends." Hedge only when the question genuinely requires client input.

**Challenge assumptions.** If a requirement sounds like it will lead to over-engineering (blockchain for a single-custodian system, microservices for a 3-person team), say so. If a constraint seems arbitrary, ask whether it's real.

**Identify patterns explicitly.** When you recommend an approach, name the pattern: "This is a Saga with orchestration," "This is the Strangler Fig pattern applied to your Excel migration." Naming patterns lets the team find documentation, hire for the skill, and reason about trade-offs.

**Second-order thinking.** After recommending something, ask: what breaks this at 10× scale? What is the operational burden in year 2? What happens during a region failover? What does the junior engineer at 2am do when it breaks?

## Repo Context

The working repo contains case studies for a solution architecture mentorship program:
- `/template/` — AsciiDoc templates (full 25-section and compact 8-section), ADR template, questionnaire template
- `/01/`, `/02/`, `/03/` — case study folders, each with `assignment/`, `docs/`, `questionnaire/`
- `/output/` — rendered SVG diagrams

Each case study has:
- `docs/solution-design.adoc` — main deliverable (follow the template)
- `questionnaire/architecture-questionnaire.md` — pre-filled discovery questionnaire
- `assignment/` — meeting notes and context

When working on a solution design, read the relevant assignment and questionnaire files first so you have full context.

## Communication Style

- **Concise and direct.** No filler phrases. Get to the point.
- **Technical depth when asked.** If someone asks "how does RLS prevent cross-tenant leaks," give a complete technical answer with a code example.
- **No hand-waving.** If you say "use PostgreSQL RLS," explain exactly how — what policy, what session variable, what connection pooling caveat.
- **Call out risks explicitly.** If an approach has a known failure mode (RLS + connection pooling race condition, global hash chain write serialization), name it and give the mitigation.
- **Use tables for comparisons.** Don't write paragraphs when a table makes it clearer.

Today's date: """ + datetime.now().strftime("%Y-%m-%d") + """
Repo root: """ + str(REPO_ROOT)

# ─────────────────────────── tools ────────────────────────────────────────────

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file in the repository. Use this to read solution designs, templates, questionnaires, or any other file before working with it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, relative to the repo root or absolute. Examples: '03/docs/solution-design.adoc', 'template/solution-design-template.adoc'"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory, optionally filtered by a glob pattern. Use to explore the repo structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to list, relative to repo root. Examples: '03/docs', 'template', '01'"
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob pattern to filter files. Examples: '*.adoc', '*.md', '**/*.svg'. Defaults to '*' (all files in directory)."
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the repository. Creates the file if it doesn't exist, overwrites if it does. Use this to create or update solution design documents, ADRs, questionnaires, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, relative to the repo root. Example: '03/docs/solution-design.adoc'"
                },
                "content": {
                    "type": "string",
                    "description": "Full content to write to the file."
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for text across files in the repository using grep. Returns matching lines with file paths and line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (regular expression supported). Example: 'Hash Chain', 'ADR-00[0-9]', 'def.*eligibility'"
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in, relative to repo root. Defaults to the entire repo."
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to restrict which files are searched. Examples: '*.adoc', '*.md', '*.py'. Defaults to all files."
                }
            },
            "required": ["query"]
        }
    }
]


def _resolve(path: str) -> Path:
    """Resolve a path relative to repo root; reject traversal outside repo."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    p = p.resolve()
    if REPO_ROOT not in p.parents and p != REPO_ROOT:
        raise ValueError(f"Path outside repo root: {path}")
    return p


def tool_read_file(path: str) -> str:
    try:
        p = _resolve(path)
        if not p.exists():
            return f"Error: file not found: {path}"
        if not p.is_file():
            return f"Error: not a file: {path}"
        size = p.stat().st_size
        if size > 500_000:
            return f"Error: file too large ({size:,} bytes). Use search_files to find specific sections."
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"


def tool_list_files(directory: str, pattern: str = "*") -> str:
    try:
        d = _resolve(directory)
        if not d.exists():
            return f"Error: directory not found: {directory}"
        if not d.is_dir():
            return f"Error: not a directory: {directory}"
        # Use rglob if pattern contains **
        if "**" in pattern:
            files = sorted(d.rglob(pattern.replace("**/", "")))
        else:
            files = sorted(d.glob(pattern))
        # filter to files only and show relative paths
        result = [str(f.relative_to(REPO_ROOT)) for f in files if f.is_file()]
        if not result:
            return f"No files found in {directory} matching '{pattern}'"
        return "\n".join(result)
    except Exception as e:
        return f"Error listing files: {e}"


def tool_write_file(path: str, content: str) -> str:
    try:
        p = _resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        rel = p.relative_to(REPO_ROOT)
        return f"Written {len(content):,} chars to {rel}"
    except Exception as e:
        return f"Error writing file: {e}"


def tool_search_files(query: str, directory: str = ".", file_pattern: str = "") -> str:
    try:
        d = _resolve(directory)
        cmd = ["grep", "-rn", "--include", file_pattern or "*", query, str(d)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{query}'"
        # Make paths relative to repo root
        lines = []
        for line in output.splitlines()[:100]:  # cap at 100 lines
            try:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    rel = Path(parts[0]).relative_to(REPO_ROOT)
                    lines.append(f"{rel}:{parts[1]}: {parts[2]}")
                else:
                    lines.append(line)
            except Exception:
                lines.append(line)
        if len(output.splitlines()) > 100:
            lines.append(f"... (truncated, {len(output.splitlines())} total matches)")
        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return "Error: search timed out"
    except Exception as e:
        return f"Error searching files: {e}"


def execute_tool(name: str, inputs: dict) -> str:
    if name == "read_file":
        return tool_read_file(inputs["path"])
    if name == "list_files":
        return tool_list_files(inputs["directory"], inputs.get("pattern", "*"))
    if name == "write_file":
        return tool_write_file(inputs["path"], inputs["content"])
    if name == "search_files":
        return tool_search_files(
            inputs["query"],
            inputs.get("directory", "."),
            inputs.get("file_pattern", "")
        )
    return f"Unknown tool: {name}"


# ─────────────────────────── history persistence ──────────────────────────────

def load_history(path: Path) -> list:
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_history(messages: list, path: Path) -> None:
    try:
        path.write_text(json.dumps(messages, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"\n[warning] could not save history: {e}", file=sys.stderr)


def trim_history(messages: list, max_turns: int) -> list:
    """Keep the most recent max_turns user/assistant pairs."""
    # A "turn" = one user message + one assistant message
    pairs = []
    i = 0
    while i < len(messages):
        if messages[i]["role"] == "user" and i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
            pairs.append((messages[i], messages[i + 1]))
            i += 2
        else:
            i += 1
    pairs = pairs[-max_turns:]
    return [msg for pair in pairs for msg in pair]


# ─────────────────────────── streaming loop ───────────────────────────────────

def chat_turn(client: anthropic.Anthropic, messages: list) -> list:
    """
    Execute one user→assistant turn with streaming and tool use.
    Returns the new assistant content blocks to append to messages.
    """
    assistant_content = []

    while True:
        # ── stream the response ──────────────────────────────────────────────
        with client.messages.stream(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=TOOLS,
            messages=messages,
        ) as stream:
            current_text = ""
            current_tool_use = None
            current_tool_input_json = ""

            for event in stream:
                etype = event.type

                if etype == "content_block_start":
                    block = event.content_block
                    if block.type == "text":
                        current_text = ""
                    elif block.type == "tool_use":
                        current_tool_use = {"type": "tool_use", "id": block.id, "name": block.name, "input": {}}
                        current_tool_input_json = ""
                        print(f"\n\033[90m[tool: {block.name}]\033[0m ", end="", flush=True)

                elif etype == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        print(delta.text, end="", flush=True)
                        current_text += delta.text
                    elif delta.type == "input_json_delta":
                        current_tool_input_json += delta.partial_json
                        print(".", end="", flush=True)

                elif etype == "content_block_stop":
                    if current_text:
                        assistant_content.append({"type": "text", "text": current_text})
                        current_text = ""
                    if current_tool_use is not None:
                        try:
                            current_tool_use["input"] = json.loads(current_tool_input_json) if current_tool_input_json else {}
                        except json.JSONDecodeError:
                            current_tool_use["input"] = {}
                        assistant_content.append(current_tool_use)
                        current_tool_use = None
                        current_tool_input_json = ""

            final_message = stream.get_final_message()
            stop_reason = final_message.stop_reason

        # ── handle tool calls ────────────────────────────────────────────────
        if stop_reason == "tool_use":
            # Append assistant turn with the tool call(s)
            messages = messages + [{"role": "assistant", "content": assistant_content}]

            # Execute each tool and collect results
            tool_results = []
            for block in assistant_content:
                if block.get("type") == "tool_use":
                    print(f"\n\033[90m  → {block['name']}({json.dumps(block['input'])[:120]})\033[0m")
                    result = execute_tool(block["name"], block["input"])
                    # Show a brief summary
                    lines = result.splitlines()
                    preview = lines[0][:100] if lines else "(empty)"
                    print(f"\033[90m  ← {preview}{'...' if len(lines) > 1 else ''}\033[0m")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": result
                    })

            # Append tool results as a user turn
            messages = messages + [{"role": "user", "content": tool_results}]
            assistant_content = []  # reset for next iteration
            print()  # newline before next streamed output

        else:
            # end_turn or other terminal stop
            print()  # final newline
            break

    return messages, assistant_content


# ─────────────────────────── REPL ─────────────────────────────────────────────

BANNER = """\033[1;34m
╔═══════════════════════════════════════════════════════════╗
║          Solution Architect Agent  ·  claude-opus-4-6     ║
║  Senior consultant for solution design & architecture     ║
╚═══════════════════════════════════════════════════════════╝
\033[0m  Type your question or design challenge.
  Commands: \033[36m/help  /reset  /save <name>  /load <name>  /quit\033[0m
  Repo: \033[90m{repo}\033[0m
"""

HELP_TEXT = """
\033[36mCommands:\033[0m
  /help              show this help
  /reset             clear conversation history and start fresh
  /save <name>       save current session to agent/<name>.json
  /load <name>       load a saved session from agent/<name>.json
  /quit  /exit  q    exit the agent

\033[36mTips:\033[0m
  - The agent reads and writes files in the repo (use /list or ask it to explore)
  - Ask it to "read 03/docs/solution-design.adoc and improve the eligibility engine section"
  - Ask it to "create an ADR for [decision]" and it will write the file
  - Ask it to "review the current design against the mentor feedback"
  - It maintains conversation history across sessions (saved automatically)
"""


def main():
    # ── CLI flags ────────────────────────────────────────────────────────────
    reset_flag = "--reset" in sys.argv
    no_history = "--no-history" in sys.argv

    client = anthropic.Anthropic()

    # ── load history ─────────────────────────────────────────────────────────
    messages: list = []
    if not reset_flag and not no_history:
        messages = load_history(HISTORY_FILE)
        if messages:
            turns = sum(1 for m in messages if m["role"] == "user")
            print(f"\033[90m[resumed session: {turns} prior turn(s)]\033[0m")

    print(BANNER.format(repo=REPO_ROOT))

    # ── REPL ─────────────────────────────────────────────────────────────────
    while True:
        try:
            user_input = input("\033[1;32mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[90m[goodbye]\033[0m")
            break

        if not user_input:
            continue

        # ── commands ─────────────────────────────────────────────────────────
        if user_input.lower() in ("/quit", "/exit", "q", ":q"):
            print("\033[90m[goodbye]\033[0m")
            break

        if user_input.lower() == "/help":
            print(HELP_TEXT)
            continue

        if user_input.lower() == "/reset":
            messages = []
            if HISTORY_FILE.exists():
                HISTORY_FILE.unlink()
            print("\033[90m[history cleared]\033[0m")
            continue

        if user_input.lower().startswith("/save "):
            name = user_input[6:].strip().replace("/", "_")
            dst = AGENT_DIR / f"{name}.json"
            dst.write_text(json.dumps(messages, ensure_ascii=False, indent=2))
            print(f"\033[90m[saved to {dst.relative_to(REPO_ROOT)}]\033[0m")
            continue

        if user_input.lower().startswith("/load "):
            name = user_input[6:].strip().replace("/", "_")
            src = AGENT_DIR / f"{name}.json"
            if not src.exists():
                print(f"\033[91m[not found: {src.name}]\033[0m")
            else:
                messages = load_history(src)
                turns = sum(1 for m in messages if m["role"] == "user")
                print(f"\033[90m[loaded {turns} turn(s) from {src.name}]\033[0m")
            continue

        # ── chat turn ─────────────────────────────────────────────────────────
        messages.append({"role": "user", "content": user_input})

        print("\n\033[1;34mArchitect:\033[0m ", end="", flush=True)
        try:
            messages, assistant_content = chat_turn(client, messages)
            # Append the final assistant turn (without tool calls — those were
            # already appended inside chat_turn; here we add the final text)
            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})
        except anthropic.APIError as e:
            print(f"\n\033[91m[API error: {e}]\033[0m")
            # Remove the user message we added so it doesn't corrupt history
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            continue
        except KeyboardInterrupt:
            print("\n\033[90m[interrupted]\033[0m")
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            continue

        # trim and save
        if not no_history:
            messages = trim_history(messages, MAX_HISTORY_TURNS)
            save_history(messages, HISTORY_FILE)

        print()


if __name__ == "__main__":
    main()
