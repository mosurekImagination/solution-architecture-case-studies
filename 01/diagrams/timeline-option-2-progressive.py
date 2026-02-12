"""
Tourist Mobile Application - Option 2: Progressive Build Timeline (RECOMMENDED)
Timeline: 7 months (Mar–Sep 2026) — MVP in 4 months, full features by month 7
Team: 4 devs (POC/MVP) → 6 devs (Full), 3 streams
Budget: $532k CAPEX (incl. 25-35% risk buffer)
"""

from shared.gantt import create_gantt_chart

# === COST ESTIMATION RATIONALE ===
# Rate: $600/day (mid-level avg) × 20 working days/month = $12,000/dev/month
# Team: 4 devs months 1-4, scale to 6 devs months 5-7
# Phase 1 (POC+MVP): 4 devs × 4 months = $192k base
# Phase 2 (Full): 6 devs × 3 months = $216k base
# Non-coding overhead: ~25%
# Risk: 30% — multi-region adds complexity (China CDN, data residency), payment integration
# 2 mid-levels per stream for bus factor mitigation

tasks = [
    # === PHASE 1: POC (Month 1-2) — Validate core AI + multi-region feasibility ===
    # Stream 1: Backend (2 devs)
    {"name": "DB Schema + PostGIS + Migrations",  "stream": "Backend",   "start": "2026-03-01", "end": "2026-03-15", "phase": "POC",  "team": "1 dev"},
    {"name": "Core API (Auth, Users, Profiles)",   "stream": "Backend",   "start": "2026-03-01", "end": "2026-03-28", "phase": "POC",  "team": "1 dev"},
    {"name": "Photo Upload + SQS + S3 Pipeline",   "stream": "Backend",   "start": "2026-03-15", "end": "2026-04-05", "phase": "POC",  "team": "1 dev"},
    {"name": "AI Recognition Lambda (Multi-LLM)",   "stream": "Backend",   "start": "2026-03-20", "end": "2026-04-20", "phase": "POC",  "team": "2 devs"},

    # Stream 2: Mobile (2 devs)
    {"name": "Native iOS/Android Shell + Nav",     "stream": "Mobile",    "start": "2026-03-01", "end": "2026-03-20", "phase": "POC",  "team": "2 devs"},
    {"name": "Camera + Photo Upload Flow",         "stream": "Mobile",    "start": "2026-03-15", "end": "2026-04-05", "phase": "POC",  "team": "1 dev"},
    {"name": "Attraction Description + Audio",     "stream": "Mobile",    "start": "2026-03-25", "end": "2026-04-20", "phase": "POC",  "team": "1 dev"},

    # Integration
    {"name": "POC Integration Sprint",             "stream": "Integration", "start": "2026-04-15", "end": "2026-04-30", "phase": "POC", "team": "4 devs"},

    # === PHASE 2: MVP (Month 3-4) — Partner ecosystem + US launch ===
    # Stream 1: Backend
    {"name": "Partner CRUD + Geo Queries API",     "stream": "Backend",   "start": "2026-05-01", "end": "2026-05-25", "phase": "MVP",  "team": "1 dev"},
    {"name": "Recommendation Engine + Cache",       "stream": "Backend",   "start": "2026-05-10", "end": "2026-06-05", "phase": "MVP",  "team": "1 dev"},
    {"name": "QR Code Discount System (Backend)",   "stream": "Backend",   "start": "2026-05-25", "end": "2026-06-15", "phase": "MVP",  "team": "1 dev"},

    # Stream 2: Mobile
    {"name": "Partner Venues UI + Map View",        "stream": "Mobile",   "start": "2026-05-01", "end": "2026-05-25", "phase": "MVP",  "team": "1 dev"},
    {"name": "QR Code + Discount Screens",          "stream": "Mobile",   "start": "2026-05-20", "end": "2026-06-10", "phase": "MVP",  "team": "1 dev"},
    {"name": "Offline Cache Mode (Phase 1)",        "stream": "Mobile",   "start": "2026-06-01", "end": "2026-06-20", "phase": "MVP",  "team": "1 dev"},

    # Infrastructure
    {"name": "CI/CD + IaC (Terraform)",             "stream": "DevOps",   "start": "2026-03-01", "end": "2026-03-28", "phase": "POC",  "team": "1 dev"},
    {"name": "US Region Prod Setup",                "stream": "DevOps",   "start": "2026-05-15", "end": "2026-06-10", "phase": "MVP",  "team": "1 dev"},

    # MVP Integration + App Store submission
    {"name": "MVP Integration + QA + Submit",       "stream": "Integration", "start": "2026-06-15", "end": "2026-06-30", "phase": "MVP", "team": "4 devs"},

    # === PHASE 3: Full Features (Month 5-7) — Payments, Loyalty, China ===
    # Stream 1: Backend (2 devs)
    {"name": "Stripe Payment Integration",          "stream": "Backend",  "start": "2026-07-01", "end": "2026-07-30", "phase": "Full", "team": "2 devs"},
    {"name": "Loyalty Points Engine",               "stream": "Backend",  "start": "2026-07-15", "end": "2026-08-15", "phase": "Full", "team": "1 dev"},
    {"name": "Partner Portal API",                  "stream": "Backend",  "start": "2026-08-01", "end": "2026-08-25", "phase": "Full", "team": "1 dev"},

    # Stream 2: Mobile (2 devs)
    {"name": "Payment + Checkout Flow",             "stream": "Mobile",   "start": "2026-07-01", "end": "2026-07-28", "phase": "Full", "team": "1 dev"},
    {"name": "Loyalty Dashboard UI",                "stream": "Mobile",   "start": "2026-07-20", "end": "2026-08-15", "phase": "Full", "team": "1 dev"},
    {"name": "Multi-language Support",              "stream": "Mobile",   "start": "2026-08-10", "end": "2026-09-01", "phase": "Full", "team": "1 dev"},

    # Stream 3: China Region (2 devs — new hires)
    {"name": "China Region Infra (CN-North-1)",     "stream": "China Infra", "start": "2026-07-01", "end": "2026-07-25", "phase": "Full", "team": "1 dev"},
    {"name": "Alibaba CDN + Data Residency",        "stream": "China Infra", "start": "2026-07-20", "end": "2026-08-15", "phase": "Full", "team": "1 dev"},
    {"name": "Cross-Region Replication",            "stream": "China Infra", "start": "2026-08-10", "end": "2026-09-05", "phase": "Full", "team": "2 devs"},

    # Final integration
    {"name": "Full Release QA + Regression",        "stream": "Integration", "start": "2026-09-01", "end": "2026-09-20", "phase": "Full", "team": "6 devs"},
]

milestones = [
    {"name": "POC Demo",          "date": "2026-04-30"},
    {"name": "MVP Launch (US)",   "date": "2026-06-30"},
    {"name": "Full Release",      "date": "2026-09-20"},
]

create_gantt_chart(
    tasks, milestones,
    title="Option 2: Progressive Build — 7 months, 4→6 devs, US+China (RECOMMENDED)",
    filename="01/diagrams/timeline-option-2-progressive",
    figsize=(16, 12),
)
