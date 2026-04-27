# YAGNI Analysis — Reinsurance Reconciliation Platform

**Type:** AI-assisted YAGNI Analysis
**Author:** Tomasz Mosur
**Date:** 2026-04-26
**Subject:** What to build now vs defer, given actual scale and team constraints

---

## Context

Monthly batch reconciliation between a UK reinsurer and 15–20 counterparties. 6-person team. Modular monolith on ECS Fargate + PostgreSQL RDS. Solvency II Art. 259 + FCA SYSC 9.1 compliance in scope.

This document applies YAGNI discipline to the architecture: identify what is genuinely required now, what is speculative over-engineering, and what should be lifted from existing patterns rather than designed from scratch.

---

## Section 1: Worth the Complexity — Build Now

These components are non-negotiable or cheap enough that deferring them creates disproportionate rework.

### 1.1 PostgreSQL Row-Level Security (RLS) multi-tenancy

Getting tenant isolation wrong at the database level means a full data access rewrite later — not a refactor, a rewrite with a security incident in the gap. The complexity is in the initial setup (policies, role configuration, connection pool session variable handling). Day-to-day operation adds zero overhead. Do it once, do it right.

**Known failure mode:** RDS Proxy with RLS has a session variable race condition. Mitigation: set `app.tenant_id` at statement level, not connection level, or use dedicated proxy endpoints per tenant. Document this explicitly in the runbook.

### 1.2 S3 Object Lock for audit trail

Solvency II Art. 259 requires a 10-year actuarial audit trail. The regulatory requirement is permanent, not speculative. Object Lock in COMPLIANCE mode prevents deletion or overwrite by any principal including root — the only mechanism that satisfies the "immutable record" test under regulatory examination. This is not over-engineering; it is the minimum viable compliance posture.

### 1.3 Idempotent file ingestion

Implementation: hash the file on receipt, store the hash, reject duplicates before processing. Low effort — one table, one check. Without it, the failure mode is a reconciliation manager double-submitting at month-end stress and the system processing both. That is a real operational incident that requires manual reconciliation of the reconciliation platform. Use S3 ETags plus a conditional PUT rather than building custom hash storage — this is the Idempotent Receiver pattern; the reference implementation already exists.

### 1.4 Correlation IDs

Generate a `cycle_id` at file receipt. Propagate it through every downstream call, log line, and audit event. Implementation cost: near zero. Debugging value at 2am during month-end: very high. No correlation ID means grepping logs by timestamp and hoping. There is no argument for deferring this.

### 1.5 Temporal tables on contracts and cycles

One PostgreSQL extension (`temporal_tables` or native `PERIOD` with triggers), one migration on contract and reconciliation cycle tables. Adds `valid_from`/`valid_to` to key rows. Without it: a counterparty disputes an eligibility decision from 8 months ago and the team reconstructs state from application logs — slow, error-prone, and not auditable. With it: one query returning the exact contract terms and cycle state as they existed at the disputed date. Solvency II audit examiners will ask this question. Answer it with a query, not with a narrative.

### 1.6 Modular boundaries in the monolith

Not complexity — structural discipline. Clean interfaces between Ingestion, Eligibility, Approval, and Audit modules cost nothing extra during initial build and prevent the accretion of cross-module direct calls that make future extraction or replacement expensive. Enforce with ArchUnit or equivalent. The cost is a conversation about boundaries at design time; the payoff is not paying for it in refactoring debt later.

---

## Section 2: YAGNI — Don't Build Yet

These components are over-engineered for current scale and should be deferred until specific triggers are met.

### 2.1 Generic expression tree rules engine / DSL

There are 3 contract types in scope. The rules have not been extracted from Excel yet. Building a configurable DSL before seeing the actual rules is the canonical YAGNI violation — designing the abstraction before you have the instances.

Build hardcoded rule evaluators per contract type. When you have 5–6 types and spot duplication across evaluators, you have the information needed to design the abstraction correctly. The complexity ceiling gate in the design is the right instinct; the gate should read "extract rules from real contracts first, then build the engine to fit what you find" — not "build the engine speculatively."

### 2.2 Step Functions for approval workflow

Scale: 15–20 counterparties × 12 cycles = 180–240 workflows per year. A `reconciliation_state` column on the cycle table and a background job runner (pg-boss, or a scheduled Fargate task) handles this without managed workflow infrastructure.

Step Functions earns its operational complexity when you have many concurrent workflows with multi-week execution lifetimes, complex branching hard to express in application code, or a need for visual audit of workflow execution state. The L1→L2 approval loop is a Four-Eyes state machine with two transitions — a state column and a timestamp are sufficient.

If the team already knows Step Functions well and delivery schedule has no pressure, keep it. But it is not required, and treating it as required adds infrastructure, IAM, and operational overhead for no functional gain at this scale.

### 2.3 Multi-region DR (eu-west-1 failover)

The relevant question: what happens if the platform is unavailable for one day at month-end? Reconciliation managers process manually and catch up when the platform returns. Painful, not catastrophic. There is no contractual SLA that requires sub-4-hour RTO in the current scope.

Cross-region replication adds ongoing cost (data transfer, read replica lag monitoring, failover runbook complexity) for a risk profile that does not justify it. Start with automated daily RDS snapshots, a tested restore runbook, and documented RTO (likely 2–4 hours for a single-region restore). Add active-standby when the client presents a contractual RTO requirement that automated restore cannot meet.

### 2.4 CloudFront CDN

This is a B2B portal accessed by a fixed set of reconciliation managers and counterparty contacts. All content is authenticated, dynamic, and per-tenant. CDN edge caching provides zero benefit for this access pattern — you cannot cache responses that are tenant-specific and session-authenticated. WAF is worth keeping as a security baseline. CloudFront as a CDN layer is not justified. Skip it entirely.

### 2.5 SAML federation

Some counterparties will not have corporate IdPs. Those that do may have IT teams that take weeks to configure a SAML integration. Cognito user pools with email + MFA works on day one for every counterparty regardless of their enterprise IT posture. SAML integration is a per-counterparty configuration effort that should be triggered by a specific counterparty requirement, not built speculatively.

Build the Cognito hook that allows an external IdP to be attached. Do not build and test the SAML integration until the first counterparty IT team asks for it.

### 2.6 SQS queue for file ingestion

15–20 files per month. There is no queue problem to solve. Files land in S3; an S3 event notification triggers the ingestion task. Sequential processing is correct at this volume. Adding SQS introduces DLQ management, visibility timeout tuning, and at-least-once delivery handling for a problem that does not exist. Add when there is evidence of concurrent submission collisions causing processing failures.

### 2.7 Splitter/Aggregator fan-out for file processing

10,000 records per file processed sequentially on a Fargate task takes seconds. Parallel fan-out adds distributed coordination overhead (partial failure handling, result aggregation, idempotency across shards) for a scale problem that does not exist. Add when single-file processing duration approaches the intra-day processing SLA.

### 2.8 Per-tenant envelope encryption

Standard KMS encryption at rest, combined with RLS tenant isolation, is the appropriate phase 1 data security posture. Per-tenant data keys (customer-managed CMKs per tenant) is a feature for contractual key isolation requirements — "our data must be encrypted with a key only we control." Build this when a specific tenant's contract requires it, not before.

---

## Section 3: Use Existing Patterns — Don't Reinvent

The following patterns have names, documented trade-offs, and reference implementations. Name them explicitly in ADRs — it anchors the team to existing knowledge and makes the regulatory justification legible.

| Pattern | Application in this system |
|---------|---------------------------|
| **Transactional Outbox** | Dual-write: state change + audit event. S3-first write with async PostgreSQL index update is a variant. Do not build custom retry logic for this — the pattern is the solution. |
| **Four-Eyes Principle** | L1 → L2 approval is the financial services implementation. Naming it makes the FCA regulatory justification self-evident in the ADR. |
| **Anti-Corruption Layer** | Per-counterparty file format translator at the ingestion boundary. Each counterparty's format normalised to the internal canonical model before any business logic runs. External format variation must not leak into the eligibility engine. |
| **Aggregate Root (DDD)** | `ReconciliationCycle` is the aggregate root. All state changes are operations on this aggregate. Prevents direct writes to child tables from outside the aggregate — a boundary that is easy to violate and expensive to fix. |
| **Domain Events** | `FileReceived`, `EligibilityCalculated`, `ApprovalGranted`, `CycleCompleted`. Name them explicitly. The audit schema becomes self-documenting when event names match regulatory vocabulary. |
| **Idempotent Receiver** | File deduplication using S3 ETags + conditional PUT. Don't build custom hash storage — use the ETag as the idempotency key. |
| **Correlation ID** | Generate `cycle_id` at file receipt, propagate through all downstream calls, log entries, and audit events. |
| **Process Manager** | If Step Functions is adopted, it IS the Process Manager pattern. AWS publishes a reference implementation for human-approval callback workflows using task tokens — use it as a template, don't design from scratch. |
| **Scheduled Scale-Up** | ECS Service Auto Scaling with scheduled actions before month-end. AWS documented pattern for predictable peak workloads. One Terraform resource, no custom logic. |

---

## Section 4: YAGNI Decision Table

| Component | Decision | When to revisit |
|-----------|----------|----------------|
| RLS multi-tenancy | Build now | — |
| S3 Object Lock audit | Build now | — |
| Idempotent file ingestion | Build now | — |
| Correlation IDs | Build now | — |
| Temporal tables | Build now | — |
| Modular boundaries | Build now | — |
| Per-contract hardcoded rules | Build now | Refactor when 5+ contract types show duplication |
| Application state machine | Build now | Replace with Step Functions when workflow types exceed ~5 concurrent |
| Step Functions | Defer | When application state machine hits complexity ceiling |
| Expression tree / DSL | Defer | After extracting rules from 5+ real contracts |
| SAML federation | Defer | When first counterparty IT team requests it |
| Multi-region DR | Defer | When client requires contractual RTO < 4h |
| CloudFront CDN | Skip | Never — WAF without CDN is sufficient for this B2B portal |
| SQS file ingestion queue | Defer | When concurrent submission collisions are observed |
| Fan-out file processing | Defer | When single-file processing exceeds intra-day SLA |
| Per-tenant KMS keys | Defer | When contractually required by a specific tenant |

---

## Section 5: The Guiding Principle

Build the things that are **wrong to add later** — RLS, Object Lock, correlation IDs, module boundaries, temporal tables. These are architectural decisions where retrofitting means rewriting, migrating live data under compliance obligations, or accepting a gap in audit continuity. The cost of adding them later is not "a sprint of work," it is "a project with risk."

Defer the things that are **easy to add later** — queues, fan-out, SAML federation, cross-region DR, the expression engine. These are incremental additions to an already-working system. The cost of adding them later is a sprint of work. The cost of building them now and getting the abstraction wrong (because you lacked the real-world cases to design against) is carrying the wrong abstraction for the life of the system.

The asymmetry is the filter. If the wrong decision now creates irreversible or high-cost consequences, build it now and build it right. If the wrong decision now just means adding something later when you understand it better, defer it.

---

*This document is an AI-assisted internal review and is not a client-facing deliverable.*
