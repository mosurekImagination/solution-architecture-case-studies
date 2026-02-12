"""
Tourist Mobile Application - Option 1: MVP Timeline
Timeline: 4 months (Mar–Jun 2026)
Team: 4 developers (2 streams)
Budget: $240k CAPEX (incl. 25% risk buffer)
"""

from shared.gantt import create_gantt_chart

# === COST ESTIMATION RATIONALE ===
# Rate: $600/day (mid-level avg) × 20 working days/month = $12,000/dev/month
# Team: 4 devs (2 per stream) — avoids bus factor, allows code review
# Non-coding overhead: ~25% (reviews, testing, docs, standups)
# Risk: 25% — well-known stack (AWS, PostgreSQL, Swift/Kotlin), clear scope

tasks = [
    # --- POC Phase (Month 1-2): Validate core AI recognition flow ---
    # Stream 1: Backend (2 devs)
    {"name": "DB Schema + PostGIS Setup",        "stream": "Backend",   "start": "2026-03-01", "end": "2026-03-15", "phase": "POC",  "team": "1 dev"},
    {"name": "Core API (Auth, Users)",           "stream": "Backend",   "start": "2026-03-01", "end": "2026-03-25", "phase": "POC",  "team": "1 dev"},
    {"name": "Photo Upload + S3 Integration",    "stream": "Backend",   "start": "2026-03-15", "end": "2026-04-01", "phase": "POC",  "team": "1 dev"},
    {"name": "AI Recognition Lambda (GPT-4V)",   "stream": "Backend",   "start": "2026-03-20", "end": "2026-04-15", "phase": "POC",  "team": "2 devs"},

    # Stream 2: Mobile (2 devs)
    {"name": "Native iOS/Android Shell + Nav",   "stream": "Mobile",    "start": "2026-03-01", "end": "2026-03-20", "phase": "POC",  "team": "2 devs"},
    {"name": "Camera + Photo Upload UI",         "stream": "Mobile",    "start": "2026-03-15", "end": "2026-04-05", "phase": "POC",  "team": "1 dev"},
    {"name": "Attraction Description Screen",    "stream": "Mobile",    "start": "2026-03-25", "end": "2026-04-15", "phase": "POC",  "team": "1 dev"},

    # Integration
    {"name": "POC Integration + Testing",        "stream": "Integration", "start": "2026-04-10", "end": "2026-04-25", "phase": "POC", "team": "4 devs"},

    # --- MVP Phase (Month 3-4): Partner ecosystem + polish ---
    # Stream 1: Backend
    {"name": "Partner API (CRUD, Geo queries)",   "stream": "Backend",  "start": "2026-04-25", "end": "2026-05-20", "phase": "MVP",  "team": "1 dev"},
    {"name": "Recommendation Engine (PostGIS)",   "stream": "Backend",  "start": "2026-05-01", "end": "2026-05-25", "phase": "MVP",  "team": "1 dev"},
    {"name": "Redis Cache Layer",                 "stream": "Backend",  "start": "2026-05-20", "end": "2026-06-05", "phase": "MVP",  "team": "1 dev"},

    # Stream 2: Mobile
    {"name": "Partner Venues List + Details",     "stream": "Mobile",   "start": "2026-04-25", "end": "2026-05-20", "phase": "MVP",  "team": "1 dev"},
    {"name": "QR Code Discount Generation",       "stream": "Mobile",   "start": "2026-05-10", "end": "2026-05-30", "phase": "MVP",  "team": "1 dev"},
    {"name": "Audio Playback + TTS",              "stream": "Mobile",   "start": "2026-05-15", "end": "2026-06-01", "phase": "MVP",  "team": "1 dev"},

    # Infrastructure
    {"name": "CI/CD + Monitoring Setup",          "stream": "DevOps",   "start": "2026-03-01", "end": "2026-03-25", "phase": "POC",  "team": "1 dev"},
    {"name": "CloudWatch Alerts + Dashboards",    "stream": "DevOps",   "start": "2026-05-15", "end": "2026-06-05", "phase": "MVP",  "team": "1 dev"},

    # Final
    {"name": "MVP Integration + QA + App Store",  "stream": "Integration", "start": "2026-06-01", "end": "2026-06-25", "phase": "MVP", "team": "4 devs"},
]

milestones = [
    {"name": "POC Demo",     "date": "2026-04-25"},
    {"name": "MVP Launch",   "date": "2026-06-25"},
]

create_gantt_chart(
    tasks, milestones,
    title="Option 1: MVP Timeline — 4 months, 4 devs, US only",
    filename="01/diagrams/timeline-option-1-mvp",
)
