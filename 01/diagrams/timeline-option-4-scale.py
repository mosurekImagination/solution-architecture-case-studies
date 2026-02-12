"""
Tourist Mobile Application - Option 4: Klook/Viator Scale Timeline
Timeline: Phase 1 migration ~12 months, ongoing scaling Years 2-5
Team: 15-20 developers (5+ streams)
Budget: $3.53M CAPEX (incl. 35-45% risk buffer)
Note: This option assumes Option 2 or 3 is already running in production.
      This is the scale-up migration path, not a fresh build.
"""

from shared.gantt import create_gantt_chart

# === COST ESTIMATION RATIONALE ===
# Rate: $700/day blended (more seniors needed for distributed systems)
# Team: 15 devs avg over 12 months
# Blended rate: ~$14,000/dev/month
# Non-coding overhead: ~30% (large team coordination, architecture decisions)
# Risk: 40% — migration risk (live system), Kubernetes complexity, global multi-region,
#   sharding migration, service mesh learning curve
# Why 40%: Migrating a running system is inherently risky. New tech (EKS, Istio, Aurora Global)
#   requires team ramp-up. 50M+ user target has unknowns in load patterns.

tasks = [
    # === PHASE 1: Architecture Migration (Month 1-4) ===
    # Stream 1: Platform (3 devs)
    {"name": "EKS Cluster Setup + Istio Mesh",     "stream": "Platform",      "start": "2026-03-01", "end": "2026-04-15", "phase": "POC",  "team": "3 devs"},
    {"name": "CI/CD Migration (GitOps/ArgoCD)",     "stream": "Platform",      "start": "2026-03-15", "end": "2026-04-20", "phase": "POC",  "team": "1 dev"},
    {"name": "Observability (DataDog + Prometheus)", "stream": "Platform",      "start": "2026-04-01", "end": "2026-05-01", "phase": "POC",  "team": "2 devs"},
    {"name": "Aurora Global DB Migration",          "stream": "Platform",      "start": "2026-04-15", "end": "2026-06-01", "phase": "MVP",  "team": "2 devs"},

    # Stream 2: Service Decomposition (4 devs)
    {"name": "Monolith → User Service (K8s)",       "stream": "Microservices", "start": "2026-03-01", "end": "2026-04-15", "phase": "POC",  "team": "2 devs"},
    {"name": "Monolith → Partner Service (K8s)",     "stream": "Microservices", "start": "2026-03-20", "end": "2026-04-30", "phase": "POC",  "team": "2 devs"},
    {"name": "Monolith → Payment Service (K8s)",     "stream": "Microservices", "start": "2026-04-01", "end": "2026-05-15", "phase": "MVP",  "team": "2 devs"},
    {"name": "Monolith → Recommendation (K8s)",      "stream": "Microservices", "start": "2026-04-20", "end": "2026-06-01", "phase": "MVP",  "team": "2 devs"},
    {"name": "Event Mesh (Kafka + EventBridge)",     "stream": "Microservices", "start": "2026-05-15", "end": "2026-06-20", "phase": "MVP",  "team": "2 devs"},

    # Stream 3: Data Layer Scaling (3 devs)
    {"name": "PostgreSQL → Aurora Sharding",         "stream": "Data",          "start": "2026-03-15", "end": "2026-05-15", "phase": "POC",  "team": "2 devs"},
    {"name": "Redis → Redis Cluster (100GB+)",       "stream": "Data",          "start": "2026-04-01", "end": "2026-05-01", "phase": "MVP",  "team": "1 dev"},
    {"name": "OpenSearch Cluster (Sharded)",         "stream": "Data",          "start": "2026-04-15", "end": "2026-05-20", "phase": "MVP",  "team": "1 dev"},
    {"name": "Kinesis + Kafka Analytics Pipeline",   "stream": "Data",          "start": "2026-05-15", "end": "2026-06-25", "phase": "Full", "team": "2 devs"},
    {"name": "Redshift Data Warehouse",              "stream": "Data",          "start": "2026-06-01", "end": "2026-07-01", "phase": "Full", "team": "1 dev"},

    # Integration
    {"name": "Migration Validation Sprint",          "stream": "Integration",   "start": "2026-06-15", "end": "2026-07-10", "phase": "MVP",  "team": "15 devs"},

    # === PHASE 2: Global Expansion (Month 5-8) ===
    # Stream 4: Multi-Region (3 devs)
    {"name": "US-West-2 Active-Active Deploy",       "stream": "Global Infra",  "start": "2026-07-01", "end": "2026-08-01", "phase": "Full", "team": "2 devs"},
    {"name": "China Region (AWS CN + Alibaba)",      "stream": "Global Infra",  "start": "2026-07-15", "end": "2026-08-25", "phase": "Full", "team": "2 devs"},
    {"name": "EU Region (GDPR + Data Residency)",    "stream": "Global Infra",  "start": "2026-08-15", "end": "2026-09-25", "phase": "Full", "team": "2 devs"},
    {"name": "APAC Region Deploy",                   "stream": "Global Infra",  "start": "2026-09-15", "end": "2026-10-20", "phase": "Full", "team": "1 dev"},
    {"name": "Global Aurora Replication",            "stream": "Global Infra",  "start": "2026-10-01", "end": "2026-11-01", "phase": "Full", "team": "2 devs"},

    # Stream 5: Scale Features (3 devs)
    {"name": "ML Pipeline (SageMaker + GPU)",        "stream": "ML/AI",         "start": "2026-07-01", "end": "2026-08-20", "phase": "Full", "team": "2 devs"},
    {"name": "Custom Model Training Pipeline",       "stream": "ML/AI",         "start": "2026-08-15", "end": "2026-10-01", "phase": "Full", "team": "2 devs"},
    {"name": "Real-time Recommendation ML",          "stream": "ML/AI",         "start": "2026-09-15", "end": "2026-11-01", "phase": "Full", "team": "1 dev"},

    # === PHASE 3: Hardening (Month 9-12) ===
    {"name": "Load Testing (10k+ QPS)",              "stream": "Platform",      "start": "2026-11-01", "end": "2026-12-01", "phase": "Full", "team": "2 devs"},
    {"name": "DR Automation (RTO 15min)",            "stream": "Platform",      "start": "2026-11-15", "end": "2026-12-15", "phase": "Full", "team": "2 devs"},
    {"name": "Security Hardening + Compliance",      "stream": "Platform",      "start": "2026-12-01", "end": "2027-01-15", "phase": "Full", "team": "2 devs"},
    {"name": "Chaos Engineering + Resilience",       "stream": "Platform",      "start": "2026-12-15", "end": "2027-01-25", "phase": "Full", "team": "1 dev"},
    {"name": "Full Scale Launch Readiness",          "stream": "Integration",   "start": "2027-01-15", "end": "2027-02-15", "phase": "Full", "team": "15 devs"},
]

milestones = [
    {"name": "Migration Complete",   "date": "2026-07-10"},
    {"name": "Multi-Region Live",    "date": "2026-11-01"},
    {"name": "Scale-Ready Launch",   "date": "2027-02-15"},
]

create_gantt_chart(
    tasks, milestones,
    title="Option 4: Klook/Viator Scale — 12 months migration, 15 devs, Global",
    filename="01/diagrams/timeline-option-4-scale",
    figsize=(18, 16),
)
