"""
Tourist Mobile Application - Cost Breakdown for All 4 Options
Generates: CAPEX tables, OPEX tables, and cost comparison chart

Cost Methodology (per mentor feedback):
- Developer-price × time (not by module)
- Rate: $600/day mid-level, $700-800/day senior, blended per option
- Risk buffer: 20-50% with justification
- Non-coding overhead: 25-30% baked into timeline
- Bus factor: minimum 2 devs per stream
"""

from shared.cost_table import create_capex_table, create_opex_table, create_cost_summary


# ============================================================================
# OPTION 1: MVP — 4 months, 4 devs, US only
# ============================================================================
# Rate: $600/day × 20 days = $12,000/dev/month
# POC: 4 devs × 2 months = $96,000
# MVP: 4 devs × 2 months = $96,000
# Risk: 25% — well-known stack (AWS ECS, PostgreSQL, Swift/Kotlin, established AI APIs)
#   - AWS managed services reduce operational risk
#   - Single region (US) — no multi-region complexity
#   - Team of 4 is manageable communication-wise

capex_option_1 = [
    {"phase": "POC",  "duration": "2 months", "team": "4 devs", "rate": "$600/day",
     "base_cost": "$96,000",  "risk": "25%", "total": "$120,000"},
    {"phase": "MVP",  "duration": "2 months", "team": "4 devs", "rate": "$600/day",
     "base_cost": "$96,000",  "risk": "25%", "total": "$120,000"},
]

create_capex_table(capex_option_1,
    title="Option 1: MVP — CAPEX Breakdown ($240k total)",
    filename="01/diagrams/capex-option-1-mvp")

opex_option_1 = [
    {"service": "AWS ECS (Fargate)",   "monthly_cost": "$180",  "notes": "2 tasks, 0.5 vCPU / 1GB each"},
    {"service": "RDS PostgreSQL",      "monthly_cost": "$200",  "notes": "db.t4g.large, 100GB, single-AZ"},
    {"service": "ElastiCache Redis",   "monthly_cost": "$75",   "notes": "cache.t3.micro, 5GB"},
    {"service": "S3 Storage",          "monthly_cost": "$25",   "notes": "Photos + static assets, ~50GB"},
    {"service": "CloudFront CDN",      "monthly_cost": "$50",   "notes": "US distribution, ~100GB/mo"},
    {"service": "Route 53",            "monthly_cost": "$5",    "notes": "DNS, health checks"},
    {"service": "Lambda (AI)",         "monthly_cost": "$30",   "notes": "Photo recognition, ~5k invocations/mo"},
    {"service": "SQS",                 "monthly_cost": "$5",    "notes": "Recognition queue"},
    {"service": "CloudWatch",          "monthly_cost": "$30",   "notes": "Logs, metrics, alarms"},
    {"service": "Cognito",             "monthly_cost": "$25",   "notes": "~1,000 MAU (Year 1)"},
    {"service": "OpenAI API",          "monthly_cost": "$150",  "notes": "GPT-4V, ~3k requests/mo"},
    {"service": "Google Vision API",   "monthly_cost": "$30",   "notes": "Landmark detection, ~3k/mo"},
    {"service": "SendGrid",            "monthly_cost": "$15",   "notes": "Transactional emails, free tier"},
    {"service": "Google Maps API",     "monthly_cost": "$15",   "notes": "Geocoding + Places, ~2k requests/mo"},
]

create_opex_table(opex_option_1,
    title="Option 1: MVP — Monthly OPEX (Year 1, ~1k users)",
    filename="01/diagrams/opex-option-1-mvp")


# ============================================================================
# OPTION 2: Progressive Build — 7 months, 4→6 devs, US+China (RECOMMENDED)
# ============================================================================
# POC: 4 devs × 2 months × $600/day = $96,000
# MVP: 4 devs × 2 months × $600/day = $96,000
# Full: 6 devs × 3 months × $600/day = $216,000
# Risk: 30% — multi-region adds complexity (China CDN, data residency laws),
#   Stripe payment integration has PCI compliance requirements,
#   cross-region replication needs careful testing
#   But: progressive approach de-risks by validating POC first

capex_option_2 = [
    {"phase": "POC",  "duration": "2 months", "team": "4 devs", "rate": "$600/day",
     "base_cost": "$96,000",  "risk": "25%", "total": "$120,000"},
    {"phase": "MVP",  "duration": "2 months", "team": "4 devs", "rate": "$600/day",
     "base_cost": "$96,000",  "risk": "25%", "total": "$120,000"},
    {"phase": "Full", "duration": "3 months", "team": "6 devs", "rate": "$600/day",
     "base_cost": "$216,000", "risk": "35%", "total": "$291,600"},
]

create_capex_table(capex_option_2,
    title="Option 2: Progressive Build — CAPEX Breakdown ($532k total)",
    filename="01/diagrams/capex-option-2-progressive")

opex_option_2 = [
    {"service": "AWS ECS (Fargate) US",   "monthly_cost": "$250",  "notes": "3 tasks, 1 vCPU / 2GB"},
    {"service": "AWS ECS (Fargate) CN",   "monthly_cost": "$250",  "notes": "3 tasks, China region"},
    {"service": "RDS PostgreSQL US",      "monthly_cost": "$350",  "notes": "db.t4g.xlarge, 500GB, Multi-AZ"},
    {"service": "RDS PostgreSQL CN",      "monthly_cost": "$350",  "notes": "db.t4g.xlarge, 500GB, China"},
    {"service": "RDS Read Replica US",    "monthly_cost": "$200",  "notes": "Read replica, same tier"},
    {"service": "ElastiCache Redis",      "monthly_cost": "$150",  "notes": "cache.t3.medium, 10GB, US+CN"},
    {"service": "S3 Storage (US+CN)",     "monthly_cost": "$50",   "notes": "~200GB total both regions"},
    {"service": "CloudFront CDN",         "monthly_cost": "$80",   "notes": "US/Global distribution"},
    {"service": "Alibaba CDN (China)",    "monthly_cost": "$100",  "notes": "China content delivery"},
    {"service": "Lambda (AI) US+CN",      "monthly_cost": "$60",   "notes": "~10k invocations/mo combined"},
    {"service": "EventBridge + SQS",      "monthly_cost": "$20",   "notes": "Event-driven flows"},
    {"service": "CloudWatch (US+CN)",     "monthly_cost": "$60",   "notes": "Both regions monitoring"},
    {"service": "Cognito",               "monthly_cost": "$50",   "notes": "~5,000 MAU"},
    {"service": "OpenAI API",            "monthly_cost": "$300",  "notes": "GPT-4V, ~8k requests/mo"},
    {"service": "Google Vision API",     "monthly_cost": "$60",   "notes": "~8k requests/mo"},
    {"service": "Stripe Processing",     "monthly_cost": "$200",  "notes": "2.9% + $0.30 per transaction"},
    {"service": "SendGrid",             "monthly_cost": "$20",   "notes": "Transactional + marketing"},
    {"service": "Google Maps API",       "monthly_cost": "$30",   "notes": "~5k requests/mo"},
]

create_opex_table(opex_option_2,
    title="Option 2: Progressive — Monthly OPEX (Year 2, ~10k users)",
    filename="01/diagrams/opex-option-2-progressive")


# ============================================================================
# OPTION 3: All Features Day 1 — 10 months, 8→10 devs, US+China+EU
# ============================================================================
# Foundation: 8 devs × 3 months × $650/day = $312,000
# Full Features: 10 devs × 4 months × $650/day = $520,000
# Hardening: 10 devs × 3 months × $650/day = $390,000
# Risk: 35% — full microservices from day 1, 3 regions simultaneously,
#   payment + loyalty + analytics all in parallel, multiple external vendor integrations
#   AWS managed services offset some risk, but team coordination overhead is significant

capex_option_3 = [
    {"phase": "POC",  "duration": "3 months", "team": "8 devs",  "rate": "$650/day",
     "base_cost": "$312,000",  "risk": "30%", "total": "$405,600"},
    {"phase": "MVP",  "duration": "4 months", "team": "10 devs", "rate": "$650/day",
     "base_cost": "$520,000",  "risk": "35%", "total": "$702,000"},
    {"phase": "Full", "duration": "3 months", "team": "10 devs", "rate": "$650/day",
     "base_cost": "$390,000",  "risk": "40%", "total": "$546,000"},
]

create_capex_table(capex_option_3,
    title="Option 3: All Features Day 1 — CAPEX Breakdown ($1.65M total)",
    filename="01/diagrams/capex-option-3-all-features")

opex_option_3 = [
    {"service": "ECS/Fargate (5 services × 3 regions)", "monthly_cost": "$1,200", "notes": "Microservices across US, CN, EU"},
    {"service": "RDS Aurora (3 regions)",                "monthly_cost": "$1,500", "notes": "db.r6g.2xlarge, 1TB+, Multi-AZ each"},
    {"service": "ElastiCache Redis Cluster",             "monthly_cost": "$400",   "notes": "20GB+, HA mode, 3 regions"},
    {"service": "DynamoDB (AR logs)",                    "monthly_cost": "$100",   "notes": "Time-series, on-demand capacity"},
    {"service": "OpenSearch Cluster",                    "monthly_cost": "$350",   "notes": "3-node cluster, geo search"},
    {"service": "S3 Storage (Global)",                   "monthly_cost": "$100",   "notes": "~500GB across regions"},
    {"service": "CloudFront + Alibaba CDN",              "monthly_cost": "$250",   "notes": "Global + China CDN"},
    {"service": "Lambda (AI Workers)",                   "monthly_cost": "$120",   "notes": "~25k invocations/mo"},
    {"service": "Kinesis + Redshift",                    "monthly_cost": "$500",   "notes": "Analytics pipeline + data warehouse"},
    {"service": "EventBridge + SQS + SNS",               "monthly_cost": "$50",    "notes": "Event mesh + messaging"},
    {"service": "CloudWatch + X-Ray",                    "monthly_cost": "$150",   "notes": "Full observability, 3 regions"},
    {"service": "WAF + Shield",                          "monthly_cost": "$100",   "notes": "DDoS protection, bot mitigation"},
    {"service": "Cognito + KMS",                         "monthly_cost": "$80",    "notes": "MFA, encryption, ~50k MAU"},
    {"service": "OpenAI API",                            "monthly_cost": "$800",   "notes": "GPT-4V, ~25k requests/mo"},
    {"service": "Google Vision + Gemini",                "monthly_cost": "$200",   "notes": "Multi-model fallback"},
    {"service": "Stripe Processing",                     "monthly_cost": "$500",   "notes": "Higher volume transactions"},
    {"service": "Google Maps + Translate",               "monthly_cost": "$100",   "notes": "POI + translation, ~20k/mo"},
    {"service": "SendGrid + SNS Push",                   "monthly_cost": "$50",    "notes": "Email + push notifications"},
]

create_opex_table(opex_option_3,
    title="Option 3: All Features — Monthly OPEX (Year 2, ~50k users)",
    filename="01/diagrams/opex-option-3-all-features")


# ============================================================================
# OPTION 4: Klook/Viator Scale — 12 months migration, 15 devs, Global
# ============================================================================
# Architecture Migration: 15 devs × 4 months × $700/day = $840,000
# Global Expansion: 15 devs × 4 months × $700/day = $840,000
# Hardening: 15 devs × 4 months × $700/day = $840,000
# Risk: 40% — migrating a live system, Kubernetes complexity, global multi-region,
#   database sharding migration, service mesh learning curve, unknown load patterns at 50M+
# Higher blended rate: more senior engineers needed for distributed systems expertise

capex_option_4 = [
    {"phase": "POC",  "duration": "4 months", "team": "15 devs", "rate": "$700/day",
     "base_cost": "$840,000",  "risk": "35%", "total": "$1,134,000"},
    {"phase": "MVP",  "duration": "4 months", "team": "15 devs", "rate": "$700/day",
     "base_cost": "$840,000",  "risk": "40%", "total": "$1,176,000"},
    {"phase": "Full", "duration": "4 months", "team": "15 devs", "rate": "$700/day",
     "base_cost": "$840,000",  "risk": "45%", "total": "$1,218,000"},
]

create_capex_table(capex_option_4,
    title="Option 4: Klook Scale — CAPEX Breakdown ($3.53M total)",
    filename="01/diagrams/capex-option-4-scale")

opex_option_4 = [
    {"service": "EKS Clusters (5 regions)",             "monthly_cost": "$8,000",  "notes": "30+ microservices, auto-scaling pods"},
    {"service": "Aurora Global DB (Sharded)",            "monthly_cost": "$12,000", "notes": "10+ shards, 50+ read replicas, 5 regions"},
    {"service": "Redis Cluster (Sharded)",               "monthly_cost": "$3,000",  "notes": "100GB+, sharded across regions"},
    {"service": "DynamoDB Global Tables",                "monthly_cost": "$2,000",  "notes": "AR logs, high-throughput, global"},
    {"service": "OpenSearch (Sharded Cluster)",          "monthly_cost": "$2,500",  "notes": "Multi-node, geo search, full-text"},
    {"service": "S3 Multi-tier Storage",                 "monthly_cost": "$800",    "notes": "5TB+, Standard→IA→Glacier lifecycle"},
    {"service": "CloudFront + Regional CDNs",            "monthly_cost": "$2,000",  "notes": "500+ edge locations, global"},
    {"service": "ALB/NLB (5 regions)",                   "monthly_cost": "$1,500",  "notes": "Ultra-high throughput, 10k+ QPS"},
    {"service": "Kinesis + Kafka",                       "monthly_cost": "$3,000",  "notes": "Real-time streams, partitioned"},
    {"service": "Redshift",                              "monthly_cost": "$2,000",  "notes": "Peta-scale analytics warehouse"},
    {"service": "SageMaker ML Endpoints",                "monthly_cost": "$4,000",  "notes": "GPU workers, model serving"},
    {"service": "DataDog APM + Monitoring",              "monthly_cost": "$5,000",  "notes": "Distributed tracing, 50+ hosts"},
    {"service": "AWS Shield Advanced + WAF",             "monthly_cost": "$3,500",  "notes": "DDoS protection, $3k/mo base"},
    {"service": "Cognito + Secrets Manager",             "monthly_cost": "$500",    "notes": "MFA, rotation, 5M+ MAU"},
    {"service": "OpenAI API (Token Pooling)",            "monthly_cost": "$5,000",  "notes": "Bulk pricing, ~500k requests/mo"},
    {"service": "Google Vision + Gemini",                "monthly_cost": "$2,000",  "notes": "Multi-model, high volume"},
    {"service": "Stripe + PayPal",                       "monthly_cost": "$15,000", "notes": "High-volume global payments"},
    {"service": "Twilio + SendGrid",                     "monthly_cost": "$2,000",  "notes": "Global SMS + email marketing"},
    {"service": "Google Maps Advanced",                  "monthly_cost": "$1,500",  "notes": "POI, routing, ~200k/mo"},
    {"service": "Neural Translation API",                "monthly_cost": "$500",    "notes": "Real-time translation, 20+ languages"},
]

create_opex_table(opex_option_4,
    title="Option 4: Klook Scale — Monthly OPEX (Year 3+, 5M+ users)",
    filename="01/diagrams/opex-option-4-scale")


# ============================================================================
# COST COMPARISON — All 4 Options Side by Side
# ============================================================================

options_comparison = [
    {
        "name": "Option 1\nMVP",
        "capex": 240000,
        "opex_monthly": 835,
        "timeline": "4 months",
        "features": "Basic AI recognition,\npartners, US only",
    },
    {
        "name": "Option 2\nProgressive\n(RECOMMENDED)",
        "capex": 531600,
        "opex_monthly": 2630,
        "timeline": "7 months",
        "features": "Payments, loyalty,\nUS+China",
    },
    {
        "name": "Option 3\nAll Features",
        "capex": 1653600,
        "opex_monthly": 6550,
        "timeline": "10 months",
        "features": "Complete platform,\nUS+China+EU",
    },
    {
        "name": "Option 4\nKlook Scale",
        "capex": 3528000,
        "opex_monthly": 74800,
        "timeline": "12 months",
        "features": "50M+ users,\nglobal, full K8s",
    },
]

create_cost_summary(
    options_comparison,
    title="Tourist App — Architecture Options Cost Comparison",
    filename="01/diagrams/cost-comparison",
    figsize=(14, 6),
)

print("\n" + "="*60)
print("COST ESTIMATION SUMMARY")
print("="*60)
print(f"""
Option 1 (MVP):
  CAPEX: $240,000 | OPEX: $835/mo | Timeline: 4 months
  Team: 4 devs | Region: US only | Risk: 25%
  Why 25%: Well-known AWS stack, single region, clear scope

Option 2 (Progressive — RECOMMENDED):
  CAPEX: $531,600 | OPEX: $2,630/mo | Timeline: 7 months
  Team: 4→6 devs | Region: US+China | Risk: 25-35%
  Why recommended: De-risks with progressive delivery,
  validates POC before committing to multi-region

Option 3 (All Features Day 1):
  CAPEX: $1,653,600 | OPEX: $6,550/mo | Timeline: 10 months
  Team: 8→10 devs | Region: US+China+EU | Risk: 30-40%
  Why 35% avg: Microservices + 3 regions + payments all at once,
  but AWS managed services offset some risk

Option 4 (Klook/Viator Scale):
  CAPEX: $3,528,000 | OPEX: $74,800/mo | Timeline: 12 months
  Team: 15 devs | Region: Global (5 regions) | Risk: 35-45%
  Why 40% avg: Live migration, K8s complexity, DB sharding,
  unknown load patterns at 50M+ users. Requires senior talent.
""")
