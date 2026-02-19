# Solution Architecture Questionnaire — Case Study 02

> **Purpose:** Gather requirements and context before creating a solution design.
> Answers feed directly into the [Solution Design Template](solution-design-template.adoc).
>
> **⚠️ Pre-Fill Status:** Pre-filled with assumptions from initial client meeting (VTT transcription).
> Items marked with ❓ require client validation. Items marked with `TBD` need further discovery.
>
> **Priority Tags:**
> - 🔴 **Must have** — blocks architecture decisions
> - 🟡 **Should have** — important but can assume a default
> - 🟢 **Nice to have** — refine later if time permits

---

## 1. Project & Stakeholders

> → Maps to: **§2 Stakeholders**, **§3 Executive Summary**

### 1.1 Project Overview
- **Project Name:** Data-Driven Customer Engagement Platform (working title)
- **Business Domain:** E-commerce / Groceries & Commodity Goods Retail
- **Primary Business Objective:** Increase daily customer turnover by 20% (~1M → ~1.2M customers/day) through personalized product suggestions powered by data analytics and AI
- **Project Sponsor:** ❓ TBD — enterprise leadership (needs identification)
- **Target Start Date:** ❓ TBD — must be scoped to hit April 2027 deadline
- **Target Go-Live Date:** April 2027 (next fiscal year), with proved results before 2028

### 1.2 Stakeholder Register

| Name / Role | Organization | Key Concerns | Communication Needs |
|-------------|-------------|--------------|---------------------|
| Enterprise Leadership / Sponsor | Client (International Webshop) | ROI on 20% turnover increase, budget approval | Executive summaries, cost projections |
| Internal Technical Team | Client | Data pipeline feasibility, integration with WordPress | Technical workshops, architecture reviews |
| Mobile App Vendor | External (outsourced) | Data access requests, API exposure, contract scope | APIs available for BE integration; DB available on request |
| Wholesalers (multiple) | External partners | Data sharing agreements, discount/deal visibility | ❓ TBD — likely formal data exchange agreements |
| ❓ Data Privacy Officer | Client | GDPR compliance, customer data processing across EU | Compliance reviews, DPA documentation |
| ❓ Marketing Team | Client | Campaign management, email content, customer segmentation | Regular syncs on suggestion strategy |

> 💡 **Hidden Stakeholder Check:**
> - ❓ **Legal/Compliance team** — GDPR is critical given 15 years of EU customer data
  - ❓ **DBA/Ops team** — who manages WordPress DB today? 900GB heavily-customized MySQL needs someone to set up read replica
  - ❓ **Mobile app vendor contract owner** — who negotiates API access terms and SLA with the vendor?
> - ❓ **Wholesaler relationship managers** — who can broker data sharing agreements?

### 1.3 Business Drivers
- **What business problem does this solution solve?**
  The enterprise has 15 years of scattered customer data across isolated systems (WordPress webshop, mobile app, wholesaler feeds) but cannot leverage it to personalize customer interactions. Despite having ~1M daily customers, they lack the data infrastructure to understand individual buying patterns and proactively suggest relevant products. This untapped data represents lost revenue.

- **What are the key business goals?**
  1. Increase daily customer turnover by 20% (from ~1M to ~1.2M customers/day)
  2. Build a unified data pipeline consolidating all customer touchpoints
  3. Enable AI-powered personalized product suggestions via email (primary) and mobile app (secondary)
  4. Become "AI enabled and data enabled" as an organization

- **How will success be measured? (KPIs)**
  - 🔴 Primary: +20% daily customer count (from ~1M to ~1.2M)
  - ❓ Email campaign open rate / click-through rate
  - ❓ Conversion rate from suggestions to purchases
  - ❓ Revenue per customer increase
  - ❓ Mobile app engagement uplift (if mobile channel activated)

### 1.4 Team Topology & Organizational Context

> → Maps to: **§11 Team Composition**, **§7 Architecture** (Conway's Law)

- **How many teams will work on the solution?** ❓ TBD — at minimum: consulting team (us) + client internal team + mobile vendor (external)
- **Are teams cross-functional or siloed?** Client internal team is not deeply technical. Mobile vendor is fully separate (outsourced). Likely siloed.
- **Communication between teams:** Distributed — mobile vendor communication is email-only (no direct access)
- **Existing team expertise:** No data team, no plans to hire, no expertise — "be the change." WordPress/PHP likely. No data engineering skills confirmed.
- **Knowledge concentration risk:** 🔴 Mobile app — external vendor is the only entity understanding the mobile architecture and data model
- **Organizational boundaries that affect architecture:**
  - WordPress webshop ↔ Mobile app = hard boundary (separate vendor, separate codebase, separate data)
  - Client ↔ Wholesalers = external boundary (multiple partners, varying data formats likely)
  - Client ↔ Mobile vendor = contractual boundary (APIs exist for BE; DB available on request)

> 💡 **Conway's Law reminder:** The mobile app being a separate vendor creates a natural service boundary.
> The data pipeline must be designed to tolerate this boundary — async, batch-oriented data exchange
> rather than real-time integration with mobile.

### 1.5 Informal Discovery Notes

- **Unspoken priorities or political dynamics:**
  - Client wants to be seen as "AI enabled" — there may be board-level pressure to adopt AI/data buzzwords
  - WordPress migration is politically sensitive — proposing it will be "heavily scrutinized"
  - The mobile vendor relationship may be fragile — 5 years of outsourcing, no direct data access suggests limited trust or contract flexibility
  - The architect is positioned as an existing vendor — failure could mean losing the vendor contract

- **Things stakeholders said "off the record":**
  - "Can you help our business grow through AI and data and everything you can imagine?" — very open-ended, signals they want to be guided, not prescriptive
  - "Your AI is only as good as your data" — Client Representative emphasized data quality as critical foundation
  - Client Representative explicitly named Snowflake and Databricks as technology hints — suggests familiarity or preference at the organizational level

- **Observed workflows vs. documented workflows:**
  - Confirmed: emails, basic reporting, ad-hoc campaigns — run as background jobs (tooling TBD: WordPress plugins vs. custom scripts vs. external)
  - Email delivery via AWS SES — already operational

- **Team morale / change appetite observations:**
  - Client appears eager to modernize ("AI enabled, data enabled")
  - But resistant to disrupting existing operational systems (no WordPress migration)
  - Appetite for change in analytics/data layer, not in transactional layer


## 2. Architecture Principles

> → Maps to: **§4 Architecture Principles**

Based on the meeting, the following principles are assumed:

- [x] **Data as an Asset** — data quality, lineage, governance are first-class _(explicitly emphasized: "your AI is only as good as your data")_
- [x] **Cost-Optimized** — enterprise will scrutinize spend; must justify ROI
- [ ] API-First — mobile vendor has APIs; internal pipeline is SQL/batch-oriented, not API-first
- [x] **Cloud-Native (Hybrid)** — AWS for some services, hosting on-prem; new platform on AWS, WordPress stays on-prem
- [x] **Security by Design** — 15 years of EU customer data implies GDPR obligations
- [ ] Observability by Default — ❓ no discussion yet
- [ ] Vendor-Neutral — ❓ Snowflake/Databricks hints suggest cloud-native preference but potential lock-in
- [x] **Incremental Adoption** — must work alongside existing WordPress and mobile systems, not replace them

**Are there any existing organizational architecture principles that must be followed?**
❓ TBD — need to ask if the client has an enterprise architecture governance body or existing principles


## 3. Functional Requirements

> → Maps to: **§5 Problem Statement**, **§9 Key Flows**, **§19 Business Process Flows**

### 3.1 Core Features

| # | Feature | MoSCoW | Notes |
|---|---------|--------|-------|
| 1 | Data ingestion from WordPress DB (replication) | Must | Free access confirmed; replication preferred over copy |
| 2 | Data ingestion from mobile app (via vendor) | Must | APIs exist for BE; own DB available on request; 2M installs — primary channel |
| 3 | Data ingestion from wholesaler feeds | Should | Multiple wholesalers; "everything, no standard" — high format variability |
| 4 | ETL pipeline (Extract, Transform, Load) | Must | Core data processing layer; transform into analytical format |
| 5 | Analytical data store (OLAP) | Must | Snowflake or Databricks — centralized analytical database |
| 6 | Customer segmentation / profiling engine | Must | Understand what each customer wants / will buy |
| 7 | Personalized product suggestion algorithm | Must | Match customer profiles with available products/deals |
| 8 | Email suggestion delivery channel | Must | Primary channel; send personalized emails to customers |
| 9 | Mobile app push notification channel | Must | **Elevated from Should** — 2M installs makes mobile a primary channel, not secondary |
| 10 | Email deliverability / validation layer | Should | Many emails are stale (10-minute mailboxes); need validation |
| 11 | Customer consent management | Must | GDPR requirement for EU customer base |
| 12 | Suggestion performance analytics / dashboards | Should | Measure KPIs: open rate, CTR, conversion |
| 13 | Mobile install base measurement | Could | Currently unknown; need analytics to measure it |
| 14 | AI model training pipeline | Could | Databricks capability; advanced personalization |

> 💡 **"Won't" boundaries (explicit):**
> - Won't replace WordPress e-commerce platform
> - Won't rebuild the mobile application
> - Won't manage wholesaler relationships (only consume their data)

- **What are the primary user personas and their use cases?**
  - **Existing Customer (email):** Receives personalized product suggestions via email based on purchase history and browsing patterns → clicks through to webshop → purchases
  - **Existing Customer (mobile):** Receives push notifications with personalized deals → opens app → purchases
  - **Marketing Team (internal):** Configures suggestion campaigns, reviews performance dashboards, manages customer segments
  - **Data Analyst (internal):** Queries analytical database, builds reports, monitors data quality

### 3.2 User Interactions
- **How will users interact with the system?**
  - End customers: via email (passive recipient) and mobile app (push notifications)
  - Internal users: ❓ web-based dashboards/admin panel for campaign management and analytics
  - Data engineers: ETL pipeline configuration and monitoring tools

- **What are the main user workflows?**
  1. Data flows from sources → ETL pipeline → analytical data store (automated, batch)
  2. Suggestion engine processes customer profiles + product catalog → generates personalized recommendations (automated, scheduled)
  3. Email service sends personalized suggestions to validated customer email addresses (automated, scheduled)
  4. Marketing team reviews campaign performance via dashboards (manual, periodic)

- **Are there any batch processing requirements?**
  - Yes — ETL pipeline will run on a weekly schedule for recommendations (client confirmed weekly is fine; "should not be limited by it")
  - WordPress DB extraction: nightly batch delta + weekly full refresh (see ADR-002)
  - Mobile data sync: daily batch via vendor APIs (see ADR-002)
  - Wholesaler data ingestion: batch, frequency depends on wholesaler data refresh rate
  - Email campaigns: batch send via AWS SES with rate limiting


## 4. Non-Functional Requirements

> → Maps to: **§12 Quality Scenarios**, **§17 Observability & Monitoring**

### 4.1 Performance
- **Expected number of concurrent users:**
  - End customers: ~1M daily (existing), targeting ~1.2M — but they interact via email clicks, not direct system access
  - Internal users (marketing/analysts): ❓ TBD — likely < 50 concurrent
  - Email sending throughput: ❓ TBD — need to determine batch size and frequency

- **Response time requirements:**
  - ETL pipeline completion: ❓ TBD — depends on data volume and freshness requirements
  - Analytical query response: ❓ TBD — likely < 30s for dashboard queries
  - Email delivery: ❓ TBD — batch delivery, not real-time (acceptable latency in hours)
  - API response time (if APIs exposed): default < 200ms P95

- **Peak load expectations:** ❓ TBD — seasonal patterns likely (holiday shopping, promotions)

### 4.2 Scalability
- **Expected growth over time:**
  - Year 1: +20% customers (target KPI), initial data pipeline operational
  - Year 2: ❓ TBD
  - Year 3: ❓ TBD

- **Scaling strategy preference:** ❓ TBD — Snowflake/Databricks auto-scale natively
- **Geographic distribution requirements:** Europe-wide (multi-country webshop) — ❓ data residency implications per EU country?

### 4.3 Availability & Reliability
- **Required uptime (SLA):** ❓ TBD — data pipeline is not customer-facing in real-time; likely lower SLA acceptable (99.5%?)
- **Maximum acceptable downtime:** ❓ TBD — pipeline delay of hours is probably acceptable
- **Recovery Time Objective (RTO):** ❓ TBD
- **Recovery Point Objective (RPO):** ❓ TBD — data replication lag tolerance

### 4.4 Security & Compliance

> → Maps to: **§14 Security Architecture**

- **Authentication requirements:** ❓ TBD — for internal dashboards/admin (likely SSO with existing enterprise identity)
- **Authorization model:** ❓ TBD — RBAC likely (marketing vs. data analyst vs. admin roles)
- **Data classification:**
  - 🔴 **Restricted:** Customer PII (emails, purchase history, browsing data) — 15 years of EU customer data
  - **Confidential:** Wholesaler pricing, deals, discount structures
  - **Internal:** Aggregated analytics, campaign performance metrics
- **Compliance requirements:**
  - 🔴 **GDPR** — mandatory; operating across Europe with customer PII
  - ❓ ePrivacy Directive — email marketing consent requirements vary by EU country
  - ❓ Country-specific data protection laws (beyond GDPR)
- **Data encryption requirements:**
  - At rest: Required (customer PII in analytical DB)
  - In transit: Required (all data flows between systems)
- **Network security requirements:** ❓ TBD — depends on hosting model (cloud vs. on-prem for WordPress)

### 4.5 Data Requirements

> → Maps to: **§8 Data Architecture**

- **Data volume:**
  - Current: 15 years × ~1M daily customers = potentially billions of transaction records
  - WordPress DB: **900GB, heavily customized MySQL** (not standard WooCommerce)
  - Mobile app: **2M installs**; own DB on vendor backend (size unknown — see questions-002)
  - Wholesaler data: volume unknown; format is non-standard ("everything, no standard")
  - Projected: +20% growth in Year 1

- **Data retention policies:** ❓ TBD — GDPR requires purpose limitation and data minimization; 15-year-old records may need to be purged

- **Data backup requirements:** ❓ TBD — analytical data store backup strategy

- **Data archival requirements:** ❓ TBD — historical data archival for analytics vs. operational data

- **Data sovereignty / residency requirements:** 🔴 ❓ EU data residency — customer data must likely stay within EU (or EEA); depends on cloud provider region selection


## 5. Technical Requirements

> → Maps to: **§6 C4 Context**, **§7 Architecture**, **§15 API Design**

### 5.1 Technology Stack Preferences
- **Programming languages:** ❓ TBD — existing: PHP (WordPress). Data pipeline: Python likely (common for ETL/ML)
- **Frameworks:** ❓ TBD
- **Database preferences:**
  - Existing: MySQL 900GB heavily customized (WordPress webshop)
  - Analytical: Snowflake on AWS (chosen — ADR-001)
  - Mobile app: own DB on vendor backend (type/schema unknown — see questions-002)
- **Cloud provider preference:** AWS for new services (confirmed); WordPress hosting on-prem (hybrid architecture)
- **Containerization:** ❓ TBD

### 5.2 Integration Requirements

| System | Protocol | Purpose | Direction |
|--------|----------|---------|-----------|
| WordPress DB (MySQL) | Direct SQL read via VPN (ADR-002) | Customer data, orders, products | In (extract) |
| Mobile App (external vendor) | REST API (vendor has APIs for BE) | Mobile customer behavior data | In (extract) |
| Wholesaler Systems (multiple) | ❓ TBD — "everything, no standard" | Product amounts, discounts, deals | In (extract) |
| Email Service Provider | AWS SES (API) | Send personalized suggestions | Out (deliver) |
| Mobile Push Service | ❓ TBD (APNs/FCM) | Push notifications to app users | Out (deliver) |

- **Third-party services/APIs:** AWS SES (confirmed — already in use for email), push notification service (TBD)

- **API Verification Checklist:**

  | System | Sandbox Available? | Auth Method | Rate Limits | SLA | Documentation Quality |
  |--------|--------------------|-------------|-------------|-----|----------------------|
  | WordPress DB | N/A (direct replication) | DB credentials | N/A | N/A | WordPress schema docs |
  | Mobile App Vendor | ❓ (see questions-002) | ❓ (see questions-002) | ❓ (see questions-002) | ❓ (see questions-002) | APIs confirmed; docs needed |
  | Wholesaler APIs | Unknown | Unknown | Unknown | Unknown | Unknown |

  > ⚠️ **Mobile vendor integration risk reduced.** APIs confirmed; DB available on request. Details (auth, rate limits, docs) in questions-002-data-ingestion.
  > Budget still 2× initial estimate for this integration due to unknown API specifics.

- **Message queue/event streaming requirements:** ❓ TBD — may need event streaming for real-time data ingestion (Kafka, Kinesis) or batch processing may suffice

### 5.3 API Requirements
- **API style preference:** ❓ TBD — internal APIs for pipeline orchestration; may not need external-facing APIs
- **API versioning strategy:** ❓ TBD
- **Expected number of API consumers:** ❓ TBD — primarily internal (pipeline components, dashboards)
- **Rate limiting requirements:** ❓ TBD — email sending rate limits, wholesaler API rate limits

### 5.4 Data Flow

```
[WordPress DB] ──replication──→ [Staging/Replica DB]
                                       │
[Mobile App DB] ──batch export──→      │
                (via vendor)           │
                                       ▼
[Wholesaler Feeds] ──batch──→  [ETL Pipeline]
                               (Extract, Transform, Load)
                                       │
                                       ▼
                              [Analytical Data Store]
                              (Snowflake / Databricks)
                                       │
                                       ▼
                              [Suggestion Engine]
                              (Customer Profiling + AI)
                                       │
                              ┌────────┴────────┐
                              ▼                  ▼
                        [Email Service]   [Mobile Push]
                              │                  │
                              ▼                  ▼
                        [Customer Inbox]   [Mobile App]
```

- **Data sources:** WordPress DB, Mobile App (vendor-gated), Wholesaler feeds (multiple)
- **Data destinations:** Analytical Data Store → Suggestion Engine → Email / Mobile channels
- **Real-time vs batch processing:** Primarily batch (ETL runs on schedule); ❓ real-time streaming could be considered for high-value triggers (e.g., flash sale notifications)


## 6. Architecture Patterns

> → Maps to: **§7 Architecture**, **§22 ADRs**

### 6.1 Architecture Style
- **Preferred architecture pattern:** Data pipeline / ETL architecture with analytical data store
  - Not a typical application architecture (microservices/monolith) — this is primarily a data platform
  - Pipeline architecture: Sources → Ingestion → Transformation → Storage → Consumption
  - ❓ Depending on scale: could be a Lambda architecture (batch + stream) or pure batch

- **Reason for choice:** The problem is fundamentally about data consolidation and analytics, not transactional processing. The existing transactional systems (WordPress, mobile app) stay as-is. We add a data layer on top.

> ⚠️ **Note:** This assignment does not fit the typical microservices vs. monolith decision.
> The core architecture decision is about the **data platform** (Snowflake vs. Databricks vs. custom)
> and the **pipeline orchestration** approach (batch ETL vs. streaming vs. hybrid).

### 6.2 Components

1. **Data Ingestion Layer** — connectors to WordPress DB (replication), mobile vendor (batch), wholesalers (batch/API)
2. **ETL Pipeline** — extract, transform, load orchestration (❓ Airflow, dbt, Databricks Jobs?)
3. **Analytical Data Store** — centralized OLAP database (Snowflake or Databricks)
4. **Suggestion Engine** — customer profiling + product recommendation algorithm
5. **Email Delivery Service** — personalized email composition and sending
6. **Mobile Push Service** — push notification delivery (optional, secondary channel)
7. **Analytics Dashboard** — campaign performance monitoring, data quality monitoring
8. **Email Validation Service** — verify/clean stale email addresses before sending

- **Shared services needed:** ❓ Authentication (for internal dashboards), Logging, Monitoring, possibly API Gateway (if exposing internal APIs)


## 7. Infrastructure & Deployment

> → Maps to: **§16 Deployment & Infrastructure**, **§6.3 Deployment Diagram**

### 7.1 Deployment Model
- **Deployment environment:** Hybrid — WordPress on-prem, new data platform on AWS. VPN/Direct Connect required between on-prem and AWS VPC (see ADR-002).
- **Deployment strategy:** ❓ TBD
- **CI/CD requirements:** ❓ TBD
- **Infrastructure as Code tool:** ❓ TBD

### 7.2 Environment Strategy

| Environment | Purpose | Infrastructure Level | Data Strategy |
|-------------|---------|---------------------|---------------|
| Development | Pipeline development & testing | Minimal compute | Anonymized sample data |
| Staging | Pre-production validation | Production-like | Subset of production data (anonymized) |
| Production | Live data pipeline & suggestions | Full compute | Real customer data (GDPR compliant) |

### 7.3 Infrastructure Components
- **Compute requirements:**
  - ETL pipeline workers: ❓ TBD (depends on Snowflake vs. Databricks)
  - Suggestion engine compute: ❓ TBD
  - Email sending infrastructure: ❓ TBD (or use managed service)

- **Storage requirements:**
  - Analytical data store: ❓ TBD — depends on data volume (potentially TB-scale with 15 years of data)
  - File storage: ❓ TBD — for wholesaler data dumps, batch exports from mobile vendor

- **Networking requirements:**
  - CDN needed: No (no customer-facing web UI)
  - Load balancer: ❓ TBD
  - VPN requirements: **Required** — secure connection from on-prem WordPress DB to AWS VPC for data extraction (see ADR-002)


## 8. Observability & Monitoring

> → Maps to: **§17 Observability & Monitoring**

### 8.1 Logging
- **Log aggregation requirements:** ❓ TBD — pipeline execution logs, data quality logs, email delivery logs
- **Log retention period:** ❓ TBD
- **Log analysis needs:** Data quality issues, pipeline failures, email bounce analysis

### 8.2 Monitoring
- **Key metrics to monitor:**
  - Application metrics: Pipeline execution time, data volume processed, transformation success/failure rates
  - Infrastructure metrics: ❓ Snowflake/Databricks cluster utilization, storage growth
  - Business metrics: Emails sent, open rate, CTR, conversion rate, customer engagement uplift

- **Alerting requirements:** Pipeline failure alerts, data quality threshold alerts, email delivery issues

### 8.3 Tracing
- **Distributed tracing needed:** ❓ Probably not initially — pipeline is sequential, not request-based
- **Performance profiling requirements:** ETL job profiling, query performance in analytical store


## 9. Disaster Recovery & Business Continuity

> → Maps to: **§16 Deployment & Infrastructure**, **§12 Quality Scenarios**

### 9.1 Backup Strategy
- **Backup frequency:** ❓ TBD — analytical data store can be rebuilt from sources (reprocessable)
- **Backup retention:** ❓ TBD
- **Backup testing requirements:** ❓ TBD

### 9.2 Disaster Recovery
- **Disaster recovery plan requirements:** ❓ TBD — since data can be re-extracted and re-processed, full DR may not be critical
- **Failover strategy:** ❓ TBD
- **Multi-region deployment:** ❓ TBD — likely single EU region initially


## 10. Testing Requirements

> → Maps to: **§12 Quality Scenarios**, **§11 Option Detail**

### 10.1 Testing Strategy
- **Unit test coverage target:** ❓ TBD — for ETL transformation logic
- **Integration testing approach:** End-to-end pipeline testing with sample data
- **Performance / load testing requirements:** ETL throughput testing with production-scale data volumes
- **Security testing requirements:** Data classification verification, PII handling validation, GDPR compliance testing

### 10.2 Acceptance Criteria
- **Who defines acceptance criteria?** ❓ TBD — likely enterprise leadership + marketing team
- **UAT process:** ❓ TBD — marketing team validates suggestion relevance
- **Performance benchmarks:** 20% turnover increase as ultimate success metric


## 11. Migration (if applicable)

> → Maps to: **§21 Migration & Transition**

- **Is this a migration from an existing system?** No — this is a new data platform layer on top of existing systems
- **Migration strategy preference:** N/A — additive, not replacing
- **Data migration requirements:** Historical data from WordPress DB (15 years) needs to be ingested into analytical store
- **Feature parity requirements:** N/A
- **Rollback plan:** ❓ TBD — can stop email campaigns and disable pipeline without affecting existing systems (low-risk rollback)


## 12. Constraints & Assumptions

> → Maps to: **§12 Assumptions, Constraints & Quality**

### 12.1 Constraints
- **Budget constraints:** **$500K total budget** (confirmed 2026-02-19)
- **Budget structure preference:** ❓ TBD (T&M / Fixed Price / Hybrid)
- **Is there a budget envelope or target range?** **$500K** — eliminates Option 3 (Databricks, $800K–$1.5M)
- **Time constraints:** **April 2027 go-live** (next fiscal year), with proved results before 2028
- **Technical constraints:**
  - 🔴 WordPress must remain as-is (no migration)
  - 🔴 Mobile app data access requires vendor email communication (no direct access)
  - WordPress DB replication is possible but must not impact live operations
  - Some customer emails are non-functional (10-minute mailboxes)
- **Regulatory constraints:**
  - 🔴 GDPR — EU customer data, email marketing consent, data minimization, right to erasure
  - ❓ ePrivacy — country-specific email marketing regulations across Europe
- **Team size / skill constraints:**
  - Client internal team is not deeply technical
  - **No data team, no plans to hire, no expertise** — "be the change" (confirmed 2026-02-19)
  - Mobile vendor is external; APIs exist for BE integration
- **Organizational constraints:**
  - ❓ Procurement / approval lead times: Unknown
  - ❓ Change Advisory Board (CAB) requirements: Unknown
  - ❓ Deployment windows / blackout periods: Unknown (e.g., holiday season freezes)
  - Cross-team dependencies: Mobile vendor (email-gated), Wholesalers (multiple external parties)

### 12.2 Assumptions
- **Technical assumptions:**
  - WordPress uses MySQL, **900GB, heavily customized schema** (not standard WooCommerce) — confirmed; requires custom SQL extraction (ADR-002)
  - WordPress DB can be read without impacting live operations — **read replica recommended** (see questions-002 Q2)
  - Customer email addresses exist for all registered users
  - Snowflake deployed on AWS in EU region — AWS confirmed (hybrid with on-prem hosting)
  - **AWS SES** is the email delivery platform (already in use) — confirmed

- **Business assumptions:**
  - The 20% turnover increase is achievable through personalized suggestions (needs market research validation)
  - Customer base is receptive to email marketing — **GDPR consent confirmed (yes)**
  - Wholesalers will cooperate with data sharing — format is non-standard ("everything, no standard"); cooperation TBD
  - Mobile vendor will provide API access — **APIs exist; DB available on request** (lower risk than assumed)
  - ~~Budget exists for enterprise-scale investment~~ → **$500K confirmed** — fits Option 2 (Snowflake), eliminates Option 3 (Databricks)


## 13. Future Considerations

> → Maps to: **§13 Recommended Next Steps**, **§19 Feature Breakdown**

### 13.1 Roadmap
- **Planned features for future releases:**
  - Phase 1: WordPress data pipeline + email suggestions (core)
  - Phase 2: Mobile app data integration + push notifications
  - Phase 3: Wholesaler data integration + dynamic deal suggestions
  - Phase 4: AI model training for advanced personalization (Databricks capability)
  - Future: Real-time streaming pipeline (Lambda architecture), A/B testing for suggestions

- **Technology migration plans:**
  - ❓ Long-term: should WordPress be eventually migrated to a modern e-commerce platform?
  - ❓ Could the data platform become a broader enterprise data hub beyond suggestions?

- **Scaling plans:**
  - Handle customer base growth beyond 1.2M/day
  - Expand to additional channels (SMS, in-app messaging, web personalization)
  - Multi-country suggestion optimization (language, product availability, regulations)

### 13.2 Technical Debt
- **Known technical debt:**
  - WordPress e-commerce plugin is legacy (15 years)
  - Mobile app built on 5-year-old architecture by external vendor
  - Customer data quality is poor (stale emails, potential duplicates across systems)
  - No unified customer identity across WordPress and mobile app

- **Refactoring plans:** ❓ Not discussed — but data quality improvement is implicitly required


## 14. Options & Decision Factors

> → Maps to: **§10 Options Comparison**, **§11 Option Detail**

- **Are there already identified solution options to compare?**
  - Option 1: **Snowflake-based Data Lake** — simpler, query-focused, popular on AWS. Good for ETL + analytics. Basic suggestion engine via SQL-based segmentation.
  - Option 2: **Databricks Data Lakehouse** — more complex/robust, supports ML model training, advanced pipeline types. Full AI-powered recommendation engine.
  - Option 3: **Custom ETL + Open Source** — self-managed pipeline (Airflow + dbt + PostgreSQL/BigQuery). Lower license cost, higher operational burden.

- **What criteria matter most for option evaluation? (rank 1-5)**
  - Time to market: 4 (confirmed: April 2027 deadline)
  - Total cost: 5 — **$500K budget confirmed; Option 3 eliminated**
  - Scalability: 3 (already at scale, needs to handle growth)
  - Feature completeness: 4 (AI/data capabilities important)
  - Operational risk: 4 (client team is not deeply technical)
  - Team expertise fit: 5 (no data team — must keep simple enough to learn)

---

## 15. Unanswered Questions → Confirmed Answers & Impact

> → Maps to: **§12 Assumptions**, **§10 Options Comparison**
>
> All 12 questions answered by client on 2026-02-19 (see questions-001-initial.md).
> 5 assumptions were **wrong** — impacts noted below.

| # | Question | Assumed Answer | ✅ Confirmed Answer (2026-02-19) | Impact |
|---|---------|----------------|----------------------------------|--------|
| 1 | 🔴 What is the budget envelope? | $200K–$1M+ range | **$500K** | ✅ Assumption correct (within range). Option 2 (Snowflake, $300K–$600K) fits. **Option 3 eliminated** ($800K–$1.5M exceeds budget). |
| 2 | 🔴 What data does the mobile vendor store? Can they export it? | Batch CSV/JSON export is negotiable | **Own DB on vendor BE, available on request; APIs exist for BE** | ⚠️ **Assumption was WRONG** — vendor is more accessible than assumed. APIs exist (not email-gated). Risk reduced. Integration strategy: REST API (ADR-002). |
| 3 | 🔴 Is there GDPR consent for email marketing? | Consent for transactional only; partial opt-in | **Yes** | ✅ Assumption was conservative — full consent confirmed. GDPR risk **resolved**. Email campaigns can launch without consent collection flow. |
| 4 | 🔴 What is the WordPress DB size and schema? | Standard WooCommerce schema, < 1TB | **900GB, heavily customized** | ⚠️ **Assumption was WRONG** — not standard WooCommerce. Off-the-shelf CDC connectors won't work. Custom SQL extraction required (ADR-002). ETL complexity increased. |
| 5 | 🟡 What cloud provider does the client use? | AWS | **AWS for some services, hosting on-prem** | ⚠️ **Partially wrong** — hybrid architecture, not pure AWS. VPN/Direct Connect required between on-prem and AWS VPC. Infrastructure work added to critical path. |
| 6 | 🟡 How do wholesalers share data today? | Manual/email-based, no APIs | **"Everything, there is no standard"** | ✅ Assumption roughly correct (no standard). High format variability confirmed — need flexible ingestion pipeline. Follow-up questions in questions-002. |
| 7 | 🟡 Does the client have an existing email marketing platform? | No existing platform | **AWS SES** | ⚠️ **Assumption was WRONG** — AWS SES already in use. Positive: no need to procure ESP. OPEX estimate reduces significantly ($100–$500/mo vs. $1K–$4K). |
| 8 | 🟡 What background jobs exist? | Basic WordPress cron jobs | **Emails, basic reporting, ad-hoc campaigns** | ✅ Assumption roughly correct. Background jobs are operational but not complex ETL. No reuse opportunity, no conflict risk. Tooling details needed (questions-002). |
| 9 | 🟡 How many customers have the mobile app? | < 30% of total customer base | **2M installs** | ⚠️ **Assumption was WRONG** — 2M installs makes mobile a **primary channel**, not secondary. Mobile push elevated from Should to Must. Channel strategy revised. |
| 10 | 🟡 What is the desired frequency of suggestions? | Weekly batch emails | **Weekly is fine; "should not be limited by it"** | ✅ Assumption correct. Batch architecture confirmed. Client open to higher frequency later — architecture should not preclude it. |
| 11 | 🟢 Is there a data analytics team or hire plan? | No dedicated team; will need training | **No team, no plans, no expertise — "be the change"** | ✅ Assumption correct but **worse than expected**. No hire plan means consulting team must build capability, not just deliver platform. Knowledge transfer is critical path. |
| 12 | 🟢 Are there any existing BI tools? | None | **No** | ✅ Assumption correct. Greenfield for analytics/BI — Snowflake + dbt + dashboard tool (Metabase/Preset) is the full stack. |

> 💡 "A TBD in the questionnaire becomes a risk in the design and a surprise in the invoice."
> ✅ **All 12 TBDs resolved.** 5 assumptions corrected. Key architectural shifts: mobile elevated to primary channel, hybrid on-prem/AWS, AWS SES confirmed, WordPress schema heavily customized.

---

## Additional Notes

**Key insight from meeting:** The client provides a generic business goal (increase sales), not a technical specification. The architect must translate this into a data-driven technical solution. The client wants to be guided — "how is up to you" — but will scrutinize changes to existing systems.

**Phased approach is critical:** Given the number of unknowns, recommend a phased delivery starting with the most accessible data source (WordPress) and the most straightforward channel (email), then expanding to mobile and wholesaler integration in subsequent phases.

**Data quality is the hidden risk:** 15 years of accumulated customer data likely contains significant quality issues (duplicates, stale records, inconsistent formats). A data quality assessment should be the very first technical activity.

---

**Questionnaire completed by:** Solution Architect
**Date:** 2026-02-13 (initial), 2026-02-19 (updated with client answers)
**Version:** 1.1 (updated with confirmed answers from questions-001-initial)
