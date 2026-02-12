"""
Tourist Mobile Application - Option 3: All Features Day 1 Timeline
Timeline: 10 months (Mar–Dec 2026)
Team: 8-10 developers (4 streams)
Budget: $1.65M CAPEX (incl. 30-40% risk buffer)
"""

from shared.gantt import create_gantt_chart

# === COST ESTIMATION RATIONALE ===
# Rate: $600/day (mid-level avg), $800/day (senior) blended ~$650/day
# Team: 8 devs months 1-4, 10 devs months 5-10
# Blended rate: ~$13,000/dev/month
# Non-coding overhead: ~30% (larger team = more coordination)
# Risk: 35% — multiple unknowns: 3 regions simultaneously, full microservices from day 1,
#   payment + loyalty + analytics all in parallel, external vendor risks (Stripe, multiple AI APIs)
# Why 35% not higher: Using AWS managed services reduces operational risk

tasks = [
    # === PHASE 1: Foundation (Month 1-3) — Core platform + all services skeleton ===
    # Stream 1: Core Backend (3 devs)
    {"name": "Microservices Scaffold + API GW",    "stream": "Backend Core",  "start": "2026-03-01", "end": "2026-03-25", "phase": "POC", "team": "2 devs"},
    {"name": "User Service + Auth (Cognito MFA)",  "stream": "Backend Core",  "start": "2026-03-01", "end": "2026-04-01", "phase": "POC", "team": "1 dev"},
    {"name": "Partner Service + Admin API",        "stream": "Backend Core",  "start": "2026-03-20", "end": "2026-04-20", "phase": "POC", "team": "1 dev"},
    {"name": "Photo Recognition (Multi-LLM)",      "stream": "Backend Core",  "start": "2026-03-15", "end": "2026-04-25", "phase": "POC", "team": "2 devs"},
    {"name": "Recommendation + OpenSearch",         "stream": "Backend Core",  "start": "2026-04-15", "end": "2026-05-20", "phase": "POC", "team": "2 devs"},

    # Stream 2: Mobile (3 devs)
    {"name": "Native iOS/Android + Design System",  "stream": "Mobile",       "start": "2026-03-01", "end": "2026-03-28", "phase": "POC", "team": "2 devs"},
    {"name": "Camera + Upload + Description",       "stream": "Mobile",       "start": "2026-03-20", "end": "2026-04-20", "phase": "POC", "team": "2 devs"},
    {"name": "Partner Venues + Map Integration",    "stream": "Mobile",       "start": "2026-04-10", "end": "2026-05-10", "phase": "POC", "team": "2 devs"},
    {"name": "QR Code + Discount Flows",            "stream": "Mobile",       "start": "2026-05-01", "end": "2026-05-25", "phase": "MVP", "team": "1 dev"},

    # Stream 3: Infrastructure (2 devs)
    {"name": "IaC (Terraform) + CI/CD Pipelines",   "stream": "DevOps",       "start": "2026-03-01", "end": "2026-04-01", "phase": "POC", "team": "2 devs"},
    {"name": "US Region Full Deploy",               "stream": "DevOps",       "start": "2026-04-01", "end": "2026-04-25", "phase": "POC", "team": "1 dev"},
    {"name": "Observability Stack (CW + X-Ray)",    "stream": "DevOps",       "start": "2026-04-15", "end": "2026-05-15", "phase": "MVP", "team": "1 dev"},

    # POC Integration
    {"name": "POC Integration Sprint",              "stream": "Integration",  "start": "2026-05-10", "end": "2026-05-28", "phase": "POC", "team": "8 devs"},

    # === PHASE 2: Full Features (Month 4-7) ===
    # Stream 1: Backend Feature Completion
    {"name": "Stripe Payment Service (PCI-DSS)",    "stream": "Backend Core", "start": "2026-06-01", "end": "2026-07-10", "phase": "MVP", "team": "2 devs"},
    {"name": "Loyalty Points Engine",               "stream": "Backend Core", "start": "2026-06-15", "end": "2026-07-20", "phase": "MVP", "team": "1 dev"},
    {"name": "Kinesis Analytics Pipeline",          "stream": "Backend Core", "start": "2026-07-01", "end": "2026-08-01", "phase": "Full", "team": "1 dev"},
    {"name": "EventBridge + Notifications",         "stream": "Backend Core", "start": "2026-07-15", "end": "2026-08-10", "phase": "Full", "team": "1 dev"},

    # Stream 2: Mobile Completion
    {"name": "Payment + Checkout Flow",             "stream": "Mobile",       "start": "2026-06-01", "end": "2026-07-01", "phase": "MVP", "team": "2 devs"},
    {"name": "Loyalty Dashboard + History",          "stream": "Mobile",       "start": "2026-06-20", "end": "2026-07-20", "phase": "MVP", "team": "1 dev"},
    {"name": "Offline Mode + Local LLM",            "stream": "Mobile",       "start": "2026-07-01", "end": "2026-08-05", "phase": "Full", "team": "2 devs"},
    {"name": "Multi-language + Translations",       "stream": "Mobile",       "start": "2026-07-20", "end": "2026-08-20", "phase": "Full", "team": "1 dev"},

    # Stream 4: Multi-Region (2 devs — hired month 4)
    {"name": "China Region Infra (CN-North-1)",     "stream": "Multi-Region", "start": "2026-06-01", "end": "2026-07-01", "phase": "Full", "team": "2 devs"},
    {"name": "Alibaba CDN + GFW Compliance",        "stream": "Multi-Region", "start": "2026-06-25", "end": "2026-07-25", "phase": "Full", "team": "1 dev"},
    {"name": "EU Region Prep (GDPR Setup)",         "stream": "Multi-Region", "start": "2026-07-15", "end": "2026-08-15", "phase": "Full", "team": "1 dev"},
    {"name": "Cross-Region Replication + DR",       "stream": "Multi-Region", "start": "2026-08-01", "end": "2026-09-01", "phase": "Full", "team": "2 devs"},

    # === PHASE 3: Hardening + Launch (Month 8-10) ===
    {"name": "Security Audit + Pen Testing",        "stream": "DevOps",       "start": "2026-09-01", "end": "2026-10-01", "phase": "Full", "team": "2 devs"},
    {"name": "Performance Testing (Load/Stress)",   "stream": "DevOps",       "start": "2026-09-15", "end": "2026-10-15", "phase": "Full", "team": "1 dev"},
    {"name": "Partner Portal Web App",              "stream": "Mobile",       "start": "2026-09-01", "end": "2026-10-15", "phase": "Full", "team": "2 devs"},
    {"name": "Full Integration + Regression",       "stream": "Integration",  "start": "2026-10-15", "end": "2026-11-15", "phase": "Full", "team": "10 devs"},
    {"name": "Staged Rollout + Launch",             "stream": "Integration",  "start": "2026-11-15", "end": "2026-12-15", "phase": "Full", "team": "10 devs"},
]

milestones = [
    {"name": "POC Demo",             "date": "2026-05-28"},
    {"name": "MVP (US Launch)",      "date": "2026-08-01"},
    {"name": "Full Release (Global)","date": "2026-12-15"},
]

create_gantt_chart(
    tasks, milestones,
    title="Option 3: All Features Day 1 — 10 months, 8→10 devs, US+China+EU",
    filename="01/diagrams/timeline-option-3-all-features",
    figsize=(18, 14),
)
