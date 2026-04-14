# Solution Architecture Questionnaire — Case Study 03

> **Purpose:** Gather requirements and context before creating a solution design.
> Answers feed directly into the [Solution Design Template](../../template/solution-design-template.adoc).
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
- **Project Name:** Reinsurance Reconciliation Platform (working title)
- **Business Domain:** Financial Services / Reinsurance / Longevity Risk
- **Primary Business Objective:** Automate inter-company reconciliation between the reinsurer and its insurer counterparties, replacing manual Excel-based workflows with a verifiable, auditable digital platform
- **Project Sponsor:** ❓ TBD — innovation initiative; likely senior leadership (CDO or CTO equivalent)
- **Target Start Date:** ❓ TBD
- **Target Go-Live Date:** ❓ TBD — phased delivery expected; initial counterparty onboarding in Phase 1

### 1.2 Stakeholder Register

| Name / Role | Organization | Key Concerns | Communication Needs |
|-------------|-------------|--------------|---------------------|
| Innovation Sponsor (CDO/CTO) | Reinsurer (client) | Strategic ROI, headcount reduction, competitive positioning | Executive summaries, milestone sign-offs |
| Reconciliation Operations Manager | Reinsurer | Operational continuity, workflow accuracy, auditability | Process workshops, UAT sign-off |
| Compliance / Audit Lead | Reinsurer | UK FCA regulatory adherence, Solvency II reporting, immutable records | Compliance review sessions |
| IT / Platform Lead | Reinsurer | Infrastructure ownership, security, integration with internal systems | Architecture reviews, ADRs |
| Counterparty Integration Lead | Reinsurer | Onboarding process for insurer counterparties, file exchange protocols | Integration specs, onboarding runbooks |
| ❓ Legal / Contracts Team | Reinsurer | Contract representation in the platform, legal admissibility of digital records | Review of contract data model |
| ❓ Counterparty Technical Contact | Each insurer (external) | File format requirements, secure file transfer, data privacy | Integration documentation, support channel |
| ❓ Data Protection Officer | Reinsurer | GDPR compliance for EU counterparty data, cross-border data flows | Compliance documentation |

> 💡 **Hidden Stakeholder Check:**
> - ❓ **UK FCA / Prudential Regulation Authority (PRA)** — audit trail requirements for Solvency II reporting; the platform's immutability model may need regulatory sign-off
> - ❓ **External auditors** — if counterparties or regulators require third-party audit access, the platform must support read-only audit views
> - ❓ **Counterparty legal / compliance teams** — each insurer may have their own data governance requirements before onboarding

### 1.3 Business Drivers
- **What business problem does this solution solve?**
  The reinsurer currently operates with a large team of reconciliation managers who manually exchange Excel files with multiple independent insurer counterparties, verify data integrity by hand, and manage multi-round approval chains to sign off on monthly pension/longevity risk calculations. This process is labor-intensive, error-prone, and scales poorly as the counterparty portfolio grows. The absence of a shared digital trust layer means trust is established entirely through human effort.

- **What are the key business goals?**
  1. Reduce reconciliation manager headcount by 50–75% through automation (from an illustrative baseline of ~100 managers to 25–50)
  2. Replace manual trust-establishment with a verifiable, tamper-evident digital platform
  3. Accelerate the monthly reconciliation cycle — reduce the number of back-and-forth rounds required
  4. Enable the reinsurer to scale its counterparty portfolio without proportionally scaling headcount
  5. Establish a defensible audit trail for UK FCA and Solvency II compliance

- **How will success be measured? (KPIs)**
  - 🔴 Primary: Reduction in reconciliation manager FTEs required per contract cycle
  - ❓ Cycle time: reduction in calendar days from file receipt to signed-off reconciliation
  - ❓ Error rate: reduction in correction rounds per cycle (backtracks/adjustments)
  - ❓ Counterparty onboarding time: weeks to onboard a new insurer counterparty
  - ❓ Audit readiness: percentage of reconciliation records with complete, machine-readable audit trail

### 1.4 Team Topology & Organizational Context

> → Maps to: **§11 Team Composition**, **§7 Architecture** (Conway's Law)

- **How many teams will work on the solution?** ❓ TBD — at minimum: consulting/delivery team + reinsurer IT + counterparty integration team
- **Are teams cross-functional or siloed?** ❓ TBD — likely siloed by org boundary (delivery team builds, reinsurer IT operates, counterparties integrate)
- **Communication between teams:** Counterparties are external; communication will be formal (API specs, onboarding docs, support SLA)
- **Existing team expertise:** ❓ TBD — reinsurer IT team size and stack unknown; reconciliation managers have deep domain knowledge but limited technical background
- **Knowledge concentration risk:** 🔴 Excel logic — reconciliation managers hold contract formula knowledge in undocumented Excel files; this must be extracted and codified during discovery
- **Organizational boundaries that affect architecture:**
  - Reinsurer ↔ each insurer counterparty = hard external boundary (separate legal entity, separate data ownership)
  - Reinsurer IT ↔ reconciliation ops = internal boundary (different owners of the platform vs. the workflow)

> 💡 **Conway's Law reminder:** Each insurer counterparty being a fully separate entity creates a natural multi-tenant boundary.
> The platform must enforce strict tenant isolation — insurer A must never see insurer B's data, even within the same reconciliation cycle for the same product type.

### 1.5 Informal Discovery Notes

- **Unspoken priorities or political dynamics:**
  - Reconciliation managers may resist automation as a threat to their roles — change management and framing the platform as a "tool for managers" rather than a "replacement for managers" will be important
  - Excel formula owners may claim the logic is too complex to migrate to code — this is a known pattern; prior projects have successfully migrated similar "dark Excel magic"
  - Counterparties are contractually bound to adopt the platform — adoption itself is not a concern, but the onboarding experience will determine how smooth the transition is

- **Things stakeholders said "off the record":**
  - This is an innovation initiative — the client is receptive to greenfield approaches; they are not constrained by legacy system preservation
  - The existing process relies on human trust as a control mechanism; the platform must provide a technically equivalent (or stronger) control

- **Observed workflows vs. documented workflows:**
  - Reconciliation cycle is nominally monthly, but corrections and backtracks mean the effective cadence is irregular
  - Multi-round approval chains suggest the current process has no formal state machine; parties iterate informally until both sides agree

- **Team morale / change appetite observations:**
  - Senior leadership is committed (innovation budget confirmed)
  - Operational team (reconciliation managers) is the change risk — discovery should include their workflow in detail


## 2. Architecture Principles

> → Maps to: **§4 Architecture Principles**

Based on the meeting, the following principles are assumed:

- [x] **Trust by Design** — the platform's primary value is trustworthiness; every data mutation, file exchange, and approval must be auditable and verifiable _(core architectural principle, unique to this case study)_
- [x] **Auditability by Default** — every state change is recorded immutably; no record is ever deleted or silently overwritten
- [x] **Multi-Tenant Security** — insurer counterparties are fully isolated tenants; data leakage between tenants is a critical risk
- [x] **Simplicity over Novelty** — blockchain and exotic databases have been explicitly ruled out; prefer battle-tested solutions (PostgreSQL + extensions) over specialist tooling _(explicitly confirmed in meeting)_
- [x] **Contract-Driven Flexibility** — the platform is schema-agnostic per contract; contract definitions drive file parsing rules dynamically
- [ ] API-First — ❓ TBD; file-based exchange may be primary initially, with API integration as a later phase
- [ ] Cloud-Native — ❓ TBD — cloud provider not confirmed; likely AWS given UK enterprise context
- [ ] Observability by Default — ❓ not discussed; assumed required given regulatory context

**Are there any existing organizational architecture principles that must be followed?**
❓ TBD — need to ask if the client has an enterprise architecture governance body or existing technical standards


## 3. Functional Requirements

> → Maps to: **§5 Problem Statement**, **§9 Key Flows**, **§19 Business Process Flows**

### 3.1 Core Features

| # | Feature | MoSCoW | Notes |
|---|---------|--------|-------|
| 1 | Contract management — upload, versioning, structured metadata | Must | Contract defines parsing rules and eligibility logic for all subsequent file processing |
| 2 | Counterparty file ingestion (monthly data files) | Must | Primary input: tables of insured individuals still alive; must support multiple file formats per contract |
| 3 | Eligibility engine — apply contract rules to incoming file data | Must | Calculates who is in the risk zone and what compensation is owed; replaces manual Excel calculation |
| 4 | Multi-step approval workflow (propose → review → adjust → sign off) | Must | Mirrors the existing multi-round manual process; chain of 2–4+ approvers per cycle |
| 5 | Immutable audit log — every mutation cryptographically or transactionally logged | Must | Core trust mechanism; replaces manual email trails and Excel version history |
| 6 | Adjustment and backtrack handling | Must | Prior-month corrections must be explicitly recorded as adjustment events, not silent overwrites |
| 7 | Multi-tenant portal — each counterparty sees only their data | Must | Strict tenant isolation; counterparties log in and see only their contracts and reconciliation cycles |
| 8 | Signed reconciliation record — final state requires explicit sign-off from both parties | Must | Digital equivalent of the manual "agreed and signed" step |
| 9 | Counterparty onboarding workflow | Must | New insurers must be onboardable without manual platform configuration per counterparty |
| 10 | Notification system — approval requests, file received, cycle status | Should | Reduces the email overhead that currently coordinates the multi-round process |
| 11 | Reconciliation operations dashboard | Should | Internal reinsurer view: all active cycles, stuck approvals, exception summary |
| 12 | Reporting for regulatory / audit purposes | Should | Machine-readable export of reconciliation records for Solvency II reporting |
| 13 | Self-service counterparty onboarding | Could | Currently assumed to require reinsurer IT involvement; self-service reduces onboarding time |
| 14 | Contract template library | Could | Reusable contract structures to accelerate new counterparty setup |

> 💡 **"Won't" boundaries (explicit):**
> - Won't integrate with a payment service provider — B2B money movement is handled via bank transfers outside the platform; the platform records the obligation, not the payment
> - Won't implement blockchain — single-custodian platform; blockchain overhead is not justified
> - Won't migrate existing closed reconciliation history from Excel — historical records remain in Excel; the platform starts fresh for new cycles

- **What are the primary user personas and their use cases?**
  - **Reconciliation Manager (reinsurer, internal):** Initiates a reconciliation cycle, reviews incoming files, applies contract rules (or reviews auto-applied results), proposes settlements, manages adjustment rounds, and gives final sign-off
  - **Counterparty Administrator (insurer, external):** Uploads the monthly data file for their contract, reviews the reinsurer's eligibility and compensation proposal, raises objections or adjustments, and counter-signs the final record
  - **Compliance / Audit User (reinsurer, internal):** Read-only access to all reconciliation records, audit logs, and signed states for regulatory reporting
  - **Platform Administrator (reinsurer IT):** Manages counterparty tenants, contract definitions, user access, and system health

### 3.2 User Interactions
- **How will users interact with the system?**
  - Reconciliation managers and compliance users: web-based portal (internal, reinsurer-hosted)
  - Counterparty administrators: web-based portal (external, multi-tenant login with counterparty-scoped access)
  - File exchange: ❓ TBD — SFTP, secure web upload, or API; likely web upload initially
  - Notifications: email (at minimum); ❓ in-app notifications as enhancement

- **What are the main user workflows?**
  1. Contract lifecycle: reinsurer uploads contract → parser extracts rules → contract is active for a counterparty tenant
  2. Monthly cycle: counterparty uploads data file → system ingests and validates → eligibility engine runs → proposal generated → approval chain starts → adjustments if needed → both parties sign off → immutable record sealed
  3. Adjustment cycle: correction from a prior month → uploaded as explicit adjustment record → linked to original cycle → requires separate sign-off
  4. Audit workflow: compliance user queries all records for a period → exports to regulatory report format

- **Are there any batch processing requirements?**
  - Monthly reconciliation is inherently batch-oriented — data files arrive once per month per contract
  - Eligibility calculation can be batch (run after file ingestion, not real-time)
  - Regulatory reporting export: periodic batch (❓ quarterly? annually?)


## 4. Non-Functional Requirements

> → Maps to: **§12 Quality Scenarios**, **§17 Observability & Monitoring**

### 4.1 Performance
- **Expected number of concurrent users:**
  - Internal reconciliation managers: ❓ TBD — likely tens, not hundreds (small specialist team)
  - External counterparty users: ❓ TBD — one or two contacts per counterparty; low concurrency expected
  - The system is not high-traffic; correctness and auditability matter more than throughput

- **Response time requirements:**
  - Eligibility engine: ❓ TBD — batch run; acceptable to complete within minutes, not milliseconds
  - Web portal interactions: < 2s P95 for page loads and action confirmations
  - File ingestion: ❓ TBD — depends on file size; files likely < 100MB; ingestion within minutes is acceptable

- **Peak load expectations:** Month-end creates a predictable peak (all counterparties submit files in a narrow window); platform must handle concurrent ingestion from multiple counterparties

### 4.2 Scalability
- **Expected growth over time:**
  - Year 1: Initial counterparty set (❓ number unknown — ask client); validate platform
  - Year 2+: Expand counterparty portfolio without headcount growth — this is the core business case
  - ❓ Number of active contracts and counterparties: critical input for capacity planning

- **Scaling strategy preference:** ❓ TBD — horizontal scaling of eligibility processing likely needed as counterparty portfolio grows
- **Geographic distribution requirements:** Counterparties are international (multi-country Europe and beyond) — platform must handle data from EU jurisdictions with GDPR implications

### 4.3 Availability & Reliability
- **Required uptime (SLA):** 🔴 High — month-end reconciliation cycle is time-critical; downtime during the submission window could constitute a breach of counterparty agreements
- **Maximum acceptable downtime:** ❓ TBD — likely < 4 hours per month; month-end window specifically must be protected
- **Recovery Time Objective (RTO):** ❓ TBD — suggest < 1 hour given business criticality
- **Recovery Point Objective (RPO):** ❓ TBD — immutable audit log must never be lost; suggest zero data loss (synchronous replication)

### 4.4 Security & Compliance

> → Maps to: **§14 Security Architecture**

- **Authentication requirements:** 🔴 Strong authentication required — multi-factor authentication for all users (financial services standard); SSO with reinsurer's identity provider for internal users; external counterparty users via dedicated credentials or federation
- **Authorization model:** 🔴 RBAC with tenant isolation — role assignments are scoped per tenant; a counterparty user can never access another counterparty's data regardless of role
- **Data classification:**
  - 🔴 **Restricted:** Contract terms, eligibility calculations, compensation amounts — commercially sensitive between parties
  - 🔴 **Restricted:** Counterparty data files containing insured individual data (PII under GDPR for EU data subjects)
  - **Confidential:** Reconciliation records and audit logs — available to authorized internal users and regulators
  - **Internal:** Platform operational metrics, anonymized usage data
- **Compliance requirements:**
  - 🔴 **UK FCA** — financial services regulation; audit trail requirements
  - 🔴 **Solvency II** (UK/EU) — capital adequacy reporting; requires defensible, auditable records of risk transfer
  - 🔴 **GDPR** — EU counterparties send files containing PII (insured individual data); data processing agreements (DPAs) required per counterparty
  - ❓ **PRA (Prudential Regulation Authority)** — UK-specific prudential standards for insurers and reinsurers
- **Data encryption requirements:**
  - At rest: Required — all contract data, file contents, and audit logs encrypted at rest
  - In transit: Required — TLS 1.2+ for all platform interactions; secure file transfer for counterparty uploads
- **Network security requirements:** ❓ TBD — counterparties are external; IP allowlisting or mTLS for machine-to-machine file exchange may be required

### 4.5 Data Requirements

> → Maps to: **§8 Data Architecture**

- **Data volume:**
  - Monthly data files: ❓ TBD — size depends on counterparty portfolio size; likely thousands to tens of thousands of records per file per contract
  - Number of contracts: ❓ TBD — critical input; determines overall data scale
  - Audit log: append-only, grows indefinitely; retention policy needed
  - Immutable record store: proportional to number of reconciliation cycles × number of contracts

- **Data retention policies:**
  - 🔴 Regulatory minimum: Solvency II requires records retained for the lifetime of the contract + regulatory run-off period (❓ confirm exact duration with compliance team; likely 10+ years)
  - GDPR: PII in counterparty data files must be subject to data minimization and right-to-erasure — this creates a tension with immutability requirements that must be architecturally resolved (e.g., hashed references rather than raw PII in the immutable log)

- **Data backup requirements:** ❓ TBD — immutable audit store must be backed up to a geographically separate region; daily snapshots minimum
- **Data sovereignty / residency requirements:** 🔴 UK data residency for core platform data; ❓ EU residency required for EU counterparty data subject PII (GDPR)


## 5. Technical Requirements

> → Maps to: **§6 C4 Context**, **§7 Architecture**, **§15 API Design**

### 5.1 Technology Stack Preferences
- **Programming languages:** ❓ TBD — no constraint from meeting; recommend mainstream stack for long-term maintainability
- **Frameworks:** ❓ TBD
- **Database preferences:**
  - Core data store: PostgreSQL recommended (battle-tested, strong extension ecosystem for immutability and temporal queries)
  - Immutability approach: PostgreSQL + audit extension (pgaudit, temporal tables, or application-level append-only pattern) preferred over specialized DBs such as immuDB (operational complexity at scale) or AWS QLDB (discontinued)
  - ❓ Consider: separate append-only audit ledger vs. integrated immutability within primary database
- **Cloud provider preference:** ❓ TBD — likely AWS given UK enterprise context; confirm with client
- **Containerization:** ❓ TBD — Kubernetes or ECS likely; enables multi-tenant isolation and deployment repeatability

### 5.2 Integration Requirements

| System | Protocol | Purpose | Direction |
|--------|----------|---------|-----------|
| Counterparty file submission | ❓ TBD (SFTP / HTTPS upload / API) | Monthly data files from insurers | In (ingest) |
| Identity provider (reinsurer) | SAML / OIDC (SSO) | Internal user authentication | In (auth) |
| Identity provider (counterparty) | ❓ TBD — dedicated credentials or federation | External user authentication | In (auth) |
| Notification / email service | ❓ TBD (SES or equivalent) | Approval requests, cycle status alerts | Out (notify) |
| Regulatory reporting export | ❓ TBD (structured data format per Solvency II) | Compliance data export | Out (report) |

- **Third-party services/APIs:** ❓ TBD — email delivery service; no payment provider required

- **API Verification Checklist:**

  | System | Sandbox Available? | Auth Method | Rate Limits | SLA | Documentation Quality |
  |--------|--------------------|-------------|-------------|-----|----------------------|
  | Counterparty file exchange | ❓ | ❓ | N/A (batch) | ❓ | To be defined in onboarding spec |
  | Reinsurer identity provider | ❓ | SAML/OIDC assumed | ❓ | ❓ | ❓ |

- **Message queue/event streaming requirements:** ❓ TBD — internal event bus for decoupling ingestion, eligibility calculation, and approval workflow is recommended; Kafka or AWS SQS/SNS are candidates

### 5.3 API Requirements
- **API style preference:** ❓ TBD — REST API for counterparty portal; ❓ event-based or file-based for bulk data exchange
- **API versioning strategy:** ❓ TBD — counterparties will integrate against a stable API; breaking changes are costly
- **Expected number of API consumers:** Low — one integration per counterparty for automated file exchange; human users via web portal
- **Rate limiting requirements:** ❓ TBD — not high-volume; rate limiting primarily as a security control

### 5.4 Data Flow

```
[Contract Upload (Reinsurer)] ──────────────→ [Contract Registry]
                                                      │
                                             (defines parsing rules)
                                                      │
[Monthly Data File (Insurer/Counterparty)] ───────────┘
                                                      │
                                                      ▼
                                          [File Ingestion & Validation]
                                          (format check, schema validation)
                                                      │
                                                      ▼
                                          [Eligibility Engine]
                                          (apply contract rules to file data)
                                                      │
                                                      ▼
                                          [Compensation Proposal]
                                                      │
                                          ┌───────────┴───────────┐
                                          ▼                       ▼
                               [Reinsurer Review]        [Counterparty Review]
                               (internal approval)        (external approval)
                                          │                       │
                                          └───────────┬───────────┘
                                                      ▼
                                          [Adjustment Rounds]
                                          (if disputed — iterative)
                                                      │
                                                      ▼
                                          [Signed Reconciliation Record]
                                          (immutable, both parties signed)
                                                      │
                                                      ▼
                                          [Audit Log / Immutable Ledger]
```

- **Data sources:** Counterparty monthly data files; contract definitions; user approval events
- **Data destinations:** Immutable audit ledger; reconciliation portal; regulatory reporting export
- **Real-time vs batch processing:** Primarily batch (monthly cycle); eligibility calculation is triggered per file ingestion, not continuous


## 6. Architecture Patterns

> → Maps to: **§7 Architecture**, **§22 ADRs**

### 6.1 Architecture Style
- **Preferred architecture pattern:** Multi-tenant SaaS platform with a workflow engine and an append-only audit store
  - Not a consumer-facing app (no high-concurrency UX demands)
  - Not a data analytics platform (no ML, no ETL pipelines)
  - The core is a **state machine** (reconciliation cycle states) backed by an **immutable event log** (every state transition is recorded)
  - Multi-tenancy is enforced at the data layer (row-level or schema-level isolation per counterparty)

- **Reason for choice:** The problem is fundamentally about trustworthy state transitions — moving a reconciliation cycle through defined stages (submitted → validated → proposed → approved → signed) in a way that both parties can independently verify. This maps naturally to an event-sourced or audit-logged state machine architecture.

> ⚠️ **Note:** Blockchain is explicitly out of scope. The reinsurer is the single custodian of the platform.
> Trust is achieved through cryptographic audit logs and multi-party digital sign-off, not distributed consensus.

### 6.2 Components

1. **Contract Registry** — stores contract definitions as structured metadata; drives parsing rules and eligibility logic
2. **File Ingestion Service** — receives and validates counterparty data files; maps file schema to contract-defined structure
3. **Eligibility Engine** — applies contract rules to ingested data; produces a compensation proposal
4. **Workflow Engine** — manages the approval state machine; routes proposals through the configured approval chain
5. **Audit Ledger** — append-only, tamper-evident store of all state transitions, file hashes, and signed records
6. **Multi-Tenant Portal** — web application serving both internal (reinsurer) and external (counterparty) users with strict tenant isolation
7. **Notification Service** — emails or in-app alerts for workflow events (file received, approval requested, cycle signed)
8. **Reporting & Export Service** — generates regulatory-format reports from the audit ledger

- **Shared services needed:** Identity & Access Management (internal SSO + external counterparty auth), Encryption Key Management, Logging & Monitoring


## 7. Infrastructure & Deployment

> → Maps to: **§16 Deployment & Infrastructure**, **§6.3 Deployment Diagram**

### 7.1 Deployment Model
- **Deployment environment:** ❓ TBD — cloud-hosted (likely AWS UK region); no on-premises component expected for the new platform
- **Deployment strategy:** ❓ TBD — blue/green or rolling deployment; month-end blackout windows likely required
- **CI/CD requirements:** ❓ TBD
- **Infrastructure as Code tool:** ❓ TBD — Terraform likely

### 7.2 Environment Strategy

| Environment | Purpose | Infrastructure Level | Data Strategy |
|-------------|---------|---------------------|---------------|
| Development | Feature development and unit testing | Minimal compute | Synthetic contract and file data |
| Staging | Pre-production validation and counterparty UAT | Production-like | Anonymized sample data per contract |
| Production | Live reconciliation platform | Full compute + HA | Real contract and counterparty data (encrypted) |

### 7.3 Infrastructure Components
- **Compute requirements:** ❓ TBD — eligibility engine may need burst capacity at month-end; auto-scaling recommended
- **Storage requirements:**
  - Counterparty data files: object storage (S3 or equivalent); encrypted; retained per regulatory policy
  - Audit ledger: durable, geographically replicated database storage
  - ❓ Separate cold storage tier for long-term regulatory retention (10+ years)
- **Networking requirements:**
  - No CDN required (not a public-facing consumer product)
  - External access: HTTPS for counterparty portal and file upload; ❓ SFTP endpoint as alternative file exchange channel
  - Internal services: private VPC; no public exposure of internal APIs


## 8. Observability & Monitoring

> → Maps to: **§17 Observability & Monitoring**

### 8.1 Logging
- **Log aggregation requirements:** Centralized log aggregation for all platform components; audit log must be separate from operational logs and treated as immutable
- **Log retention period:** ❓ TBD — operational logs: 90 days minimum; audit logs: align with regulatory retention (10+ years)
- **Log analysis needs:** Workflow bottleneck detection, file ingestion failures, approval chain delays, security anomalies

### 8.2 Monitoring
- **Key metrics to monitor:**
  - Application metrics: reconciliation cycle throughput, eligibility engine execution time, file ingestion success/failure rate
  - Workflow metrics: average cycle duration, stuck approvals (cycles in a single state > N days), backtrack frequency
  - Infrastructure metrics: ❓ database replication lag, compute utilization (especially at month-end)
  - Business metrics: cycles completed per month, headcount per cycle (to validate the reduction KPI)

- **Alerting requirements:** Ingestion failures during month-end window; workflow stuck for > 48 hours; platform unavailability > SLA threshold; audit log write failures (critical — must page on-call immediately)

### 8.3 Tracing
- **Distributed tracing needed:** ❓ Recommended — a reconciliation cycle spans multiple services (ingestion → eligibility → workflow → audit); tracing is valuable for debugging and performance analysis
- **Performance profiling requirements:** Eligibility engine profiling for large counterparty files; database query performance on the audit ledger


## 9. Disaster Recovery & Business Continuity

> → Maps to: **§16 Deployment & Infrastructure**, **§12 Quality Scenarios**

### 9.1 Backup Strategy
- **Backup frequency:** ❓ TBD — at minimum, nightly full backup; continuous replication for audit ledger (zero data loss)
- **Backup retention:** Align with regulatory retention requirements (10+ years for closed reconciliation records)
- **Backup testing requirements:** ❓ Quarterly restore tests; audit ledger integrity verification

### 9.2 Disaster Recovery
- **Disaster recovery plan requirements:** ❓ TBD — given month-end criticality, a documented DR runbook with tested recovery steps is required
- **Failover strategy:** ❓ TBD — active-passive or active-active across availability zones; cross-region for audit ledger backup
- **Multi-region deployment:** ❓ TBD — single UK region for primary; cross-region backup for DR; EU region may be required for EU counterparty data residency


## 10. Testing Requirements

> → Maps to: **§12 Quality Scenarios**, **§11 Option Detail**

### 10.1 Testing Strategy
- **Unit test coverage target:** ❓ TBD — eligibility engine logic must be comprehensively unit-tested (contract rules are financial calculations)
- **Integration testing approach:** End-to-end reconciliation cycle test with synthetic contract definitions and counterparty files; multi-tenant isolation tests (attempt cross-tenant data access, verify denial)
- **Performance / load testing requirements:** Month-end simulation — concurrent file ingestion from multiple counterparties; eligibility engine under load
- **Security testing requirements:** Penetration testing of external-facing portal; tenant isolation boundary testing; audit log tamper-attempt testing

### 10.2 Acceptance Criteria
- **Who defines acceptance criteria?** Reconciliation operations manager (process correctness) + compliance lead (audit trail completeness) + counterparty UAT contacts (integration experience)
- **UAT process:** ❓ TBD — staged counterparty onboarding; first counterparty in UAT before production rollout
- **Performance benchmarks:** Full monthly reconciliation cycle (file ingestion to signed record) completed within ❓ TBD hours; audit log queryable for regulatory export within ❓ TBD minutes


## 11. Migration (if applicable)

> → Maps to: **§21 Migration & Transition**

- **Is this a migration from an existing system?** No — greenfield platform replacing a manual Excel-based process; no legacy system to migrate from
- **Migration strategy preference:** Parallel run — new counterparties onboarded to the platform first; existing active contracts may run in parallel (Excel + platform) during a transition window per counterparty
- **Data migration requirements:** Closed historical reconciliation records remain in Excel; the platform starts fresh with new cycles (no historical data import)
- **Feature parity requirements:** The platform must fully replace the Excel workflow for each counterparty before Excel decommission for that counterparty
- **Rollback plan:** Per-counterparty rollback — if a counterparty experiences issues, they can revert to the Excel process for their next cycle; the platform can be re-onboarded when issues are resolved


## 12. Constraints & Assumptions

> → Maps to: **§12 Assumptions, Constraints & Quality**

### 12.1 Constraints
- **Budget constraints:** ❓ TBD — budget is described as "not a concern" (innovation initiative); however, cost model should be presented for ongoing OPEX
- **Budget structure preference:** ❓ TBD
- **Time constraints:** ❓ TBD — no deadline specified; phased delivery recommended
- **Technical constraints:**
  - 🔴 No blockchain — explicitly ruled out; single-custodian platform does not require distributed consensus
  - 🔴 No payment service provider integration — B2B money movement is out of scope; the platform records the obligation, not the settlement
  - 🔴 Immutable audit log — once a reconciliation record is signed, it cannot be modified or deleted; corrections are new records
- **Regulatory constraints:**
  - 🔴 UK FCA — audit trail and record-keeping requirements for financial services
  - 🔴 Solvency II — capital adequacy reporting requires defensible records of risk transfer amounts
  - 🔴 GDPR — EU counterparty data files may contain PII; data processing agreements required; data residency obligations apply
- **Team size / skill constraints:**
  - ❓ Reinsurer IT team capacity and technology stack unknown
  - Reconciliation managers have deep domain knowledge but limited technical background — they must be involved in UAT and workflow design
- **Organizational constraints:**
  - Counterparty adoption is contractually mandated — counterparties must onboard; however, onboarding experience will determine timeline
  - ❓ Procurement / approval lead times: unknown

### 12.2 Assumptions
- **Technical assumptions:**
  - PostgreSQL with audit extensions is sufficient for the immutability requirement (validated by mentor based on production experience)
  - File exchange will be HTTPS-based (web upload or API); SFTP as a fallback for counterparties with legacy systems
  - Cloud deployment on AWS UK region (to be confirmed)
  - Eligibility calculations can be expressed as structured rule sets derived from contract metadata — they do not require arbitrary code execution

- **Business assumptions:**
  - The reinsurer is the single trusted custodian of the platform; counterparties trust the reinsurer's platform rather than requiring peer-to-peer verification
  - Monthly reconciliation cycle frequency is the baseline; some contracts may reconcile quarterly (to be confirmed per contract type)
  - Counterparties will provide a technical contact for integration; onboarding time estimated at ❓ TBD weeks per counterparty
  - Reconciliation manager headcount reduction is the primary KPI; the client is prepared for the organizational change this implies


## 13. Future Considerations

> → Maps to: **§13 Recommended Next Steps**, **§19 Feature Breakdown**

### 13.1 Roadmap
- **Planned features for future releases:**
  - Phase 1: Core reconciliation platform — contract registry, file ingestion, eligibility engine, approval workflow, immutable audit log (first 1–3 counterparties)
  - Phase 2: Self-service counterparty onboarding — reduce onboarding effort as counterparty portfolio grows
  - Phase 3: Regulatory reporting — automated Solvency II export; read-only regulator access portal
  - Phase 4: API-based file exchange — replace manual uploads with machine-to-machine integration for technically capable counterparties
  - Future: Real-time eligibility calculations; predictive analytics on reconciliation cycle duration; AI-assisted anomaly detection in incoming files

- **Technology migration plans:**
  - ❓ Long-term: should the eligibility engine support arbitrary rule languages (e.g., a DSL for contract authors) rather than structured metadata?
  - ❓ Could the platform become a market offering — sold to other reinsurers?

- **Scaling plans:**
  - Expand counterparty portfolio from initial pilot to full book of business
  - Handle increasing file volumes as portfolios mature
  - Multi-jurisdiction expansion (US, Asia) would require additional regulatory compliance work

### 13.2 Technical Debt
- **Known technical debt:**
  - Contract rule extraction from Excel — initial contracts may require manual translation by domain experts; a rule authoring tool should be a Phase 2 investment
  - ❓ Legacy file formats — some counterparties may use non-standard Excel or CSV formats; the ingestion layer must handle format variability

- **Refactoring plans:** ❓ Not discussed — eligibility engine design should accommodate future rule complexity without requiring core platform changes


## 14. Options & Decision Factors

> → Maps to: **§10 Options Comparison**, **§11 Option Detail**

- **Are there already identified solution options to compare?**
  - **Option 1: PostgreSQL + Audit Extension (Pragmatic Monolith)**
    — PostgreSQL as the primary data store with application-level append-only audit tables or pgaudit; modular monolith architecture; battle-tested operationally; lowest operational risk; highest team familiarity
  - **Option 2: Event-Sourced Architecture (Append-Only Event Store)**
    — All state changes are immutable events; the current state is derived by replaying the event log; provides full auditability and temporal queries by design; higher complexity but strongest architectural fit for the audit requirement
  - **Option 3: Managed Ledger Database (AWS QLDB successor or equivalent)**
    — Fully managed, cryptographically verifiable ledger; lower operational burden; potential vendor lock-in; AWS QLDB is discontinued, so a current equivalent must be evaluated (❓ Amazon Aurora with pgaudit? Azure Confidential Ledger?)

- **What criteria matter most for option evaluation? (rank 1-5)**
  - Auditability / tamper-evidence: 5 — core product requirement
  - Operational simplicity: 5 — reinsurer IT team size and expertise unknown; minimize operational burden
  - Total cost of ownership: 4 — budget is flexible but OPEX model must be defensible
  - Regulatory compliance: 5 — Solvency II and FCA requirements are non-negotiable
  - Scalability (counterparty growth): 3 — important long-term but not the immediate bottleneck
  - Time to first counterparty onboarding: 4 — innovation initiative wants visible results

---

## 15. Unanswered Questions for Async Discovery

> → Maps to: **§12 Assumptions**, **§10 Options Comparison**
>
> These questions are recommended for async follow-up with the client before the next session.

| # | Priority | Question | Assumed Answer | Impact if Different |
|---|----------|---------|----------------|---------------------|
| 1 | 🔴 | How many active counterparty contracts does the reinsurer currently have? | ❓ Tens, not hundreds | Directly sizes the platform; more contracts = more complex multi-tenancy |
| 2 | 🔴 | What is the target go-live date or phase timeline? | ❓ No constraint stated | Determines phasing and MVP scope |
| 3 | 🔴 | What cloud provider does the reinsurer use for other systems? | AWS assumed | May change infrastructure choices; Azure or GCP would shift tooling |
| 4 | 🔴 | Does the reinsurer have an existing identity provider for SSO? | ❓ Assumed yes (Azure AD or similar) | No IdP = must provision auth from scratch; adds scope |
| 5 | 🔴 | What data residency jurisdiction is required for counterparty PII? | UK; EU for EU counterparties | Cross-border data flows significantly complicate architecture |
| 6 | 🟡 | What is the typical size of a monthly counterparty data file? | Thousands of records, < 100MB | Very large files change ingestion architecture |
| 7 | 🟡 | Are counterparties expected to integrate via API or manually upload files? | Manual upload initially | API-first requires earlier investment in integration spec |
| 8 | 🟡 | Does the client have a preferred file format standard (CSV, XLSX, XML, JSON)? | ❓ Varies per contract | Mixed formats require a more flexible ingestion parser |
| 9 | 🟡 | What is the reinsurer's internal IT team size and technical stack? | ❓ Unknown | Small IT team favors managed services and lower operational complexity |
| 10 | 🟢 | Is there a requirement for counterparties to export their reconciliation records in a specific format? | ❓ Not discussed | Custom export formats add scope to the reporting service |

---

## Additional Notes

**Key insight from meeting:** This assignment is explicitly about **infrastructure and trust**, not business logic or app development. The architecture review board for this platform should ask "how do we know this record is authentic?" before "what features does this support?" — that inversion of priorities is what makes this case study architecturally distinct.

**Domain research is required:** Reinsurance, longevity risk, Solvency II capital requirements, and UK FCA audit standards are all domain prerequisites before a solution design can be credibly presented. The client should not see a design from an architect who has not done this research.

**The Excel extraction challenge is real but solvable:** Prior projects with "impossible to migrate" Excel logic have been successfully migrated to code. The key is involving the Excel formula authors as domain experts during the requirements phase, not as gatekeepers of an unmigrateable artifact.

---

**Questionnaire completed by:** Solution Architect
**Date:** 2026-04-14 (initial pre-fill from meeting transcription)
**Version:** 1.0 (pre-fill; awaiting client validation)
