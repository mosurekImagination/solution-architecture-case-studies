# Architecture Review — Reinsurance Reconciliation Platform

**Type:** AI-assisted Architecture Review
**Author:** Tomasz Mosur
**Date:** 2026-04-26
**Subject:** Critical review of Option 2 (Full Platform) and evaluation of alternative architectures

---

## 1. Purpose and Scope

This document critically evaluates the solution architecture described in `03/docs/solution-design.adoc`. The recommended option is Option 2 — Full Platform with Workflow Engine and SHA-256 Hash-Chain Audit Ledger. This review challenges that recommendation, proposes alternative architectures not present in the original design, and rates all options on a consistent rubric. The audience is the architect who wrote the original design.

---

## 2. Summary Verdict

**Option 2 is a reasonable choice and will likely succeed, but it carries three genuine risks that the design under-weights:** (a) the Lambda execution model creates a covert RTO exposure at month-end that contradicts the stated 99.9% availability target, (b) the hash-chain design is more complex operationally than the design acknowledges — a misconfigured KMS break-glass procedure or a botched DB snapshot restore could silently corrupt the chain in ways that only surface at audit time, and (c) the 9.5-month timeline is aggressive for a team that has not yet confirmed the language choice or extracted a single contract rule. These are not reasons to abandon Option 2, but they are reasons to consider a lower-variance alternative before signing.

---

## 3. Critical Assessment of Option 2

### 3.1 Lambda + Aurora Serverless v2 at Month-End: The Hidden Availability Trap

The design correctly identifies the monthly-peak workload and uses Lambda + Aurora Serverless v2 to minimise idle costs. The OPEX case is valid. The availability argument is not.

The NFR states 99.9% monthly uptime and RTO < 1 hour. Aurora Serverless v2 Multi-AZ automatic failover takes approximately 20–40 seconds for an AZ failure — fine. What the design does not address is the **Lambda VPC cold start** scenario at month-end.

Lambda functions inside a VPC require an ENI (Elastic Network Interface) per availability zone per function. At month-end, when 20 counterparties simultaneously upload files, the burst of Lambda invocations can exhaust the ENI creation rate in the VPC subnet, causing invocations to fail with `ENILimitReached` or time out waiting for network attachment. This is a well-documented AWS production failure mode. The design mentions "provisioned concurrency for the API function" in the environment table, but provisioned concurrency is only noted for the production API service — the eligibility engine Lambda is the one that fans out massively, and it is not covered.

The mitigation listed (pre-warming Lambda 1 hour before month-end) addresses Aurora ACU scale-up, not ENI provisioning. These are different problems.

**Failure at 2am:** A month-end eligibility submission fails silently because the eligibility Lambda times out on VPC ENI attachment. The Step Functions workflow moves to a failure state. The counterparty's file was accepted (S3 write succeeded) but eligibility was never computed. The reconciliation manager sees a cycle stuck in `AWAITING_ELIGIBILITY`. Nothing in the design specifies alerting for this state, the retry policy on the Step Functions task, or who gets paged.

**Required mitigations the design should add:**
- Provisioned concurrency on the eligibility engine Lambda (not just the API Lambda)
- Explicit Step Functions retry policy with backoff on the eligibility task, with a DLQ for permanently failed invocations
- CloudWatch alarm on `AWAITING_ELIGIBILITY` cycles older than N hours
- Consider moving the eligibility engine to ECS Fargate on a scheduled scale-up at month-end (eliminates ENI cold start entirely)

### 3.2 Hash-Chain Operational Fragility

The hash-chain design is elegant on paper. The per-tenant chain, KMS-signed genesis, and weekly verification Lambda are well thought out. Three operational failure modes are not addressed:

**Failure mode 1 — Aurora point-in-time restore corrupts the chain.** If a storage incident requires restoring Aurora from a snapshot, all audit events written after the snapshot timestamp are lost. The hash chain for affected tenants is broken — the most recent N events no longer link to the restored tip. The design says "RPO = 0 for AZ failure" (synchronous Multi-AZ replication), but RPO = 24h for a full region failure (AWS Backup cross-region snapshots). A full-region DR failover means up to 24 hours of audit events are unrecoverable. For a Solvency II-regulated platform, this is not an RPO footnote — it is a regulatory exposure. The audit ledger needs a separate, lower-RPO backup path (continuous replication via Aurora Global Database or a purpose-built event stream) independent of the operational DB backup.

**Failure mode 2 — Break-glass superuser access breaks the chain silently.** The design documents a break-glass procedure for superuser DB access. An INSERT-only role prevents application writes of UPDATEs. But a superuser (or anyone who escalates via the break-glass procedure) can issue UPDATE/DELETE directly. The chain will fail its next verification sweep, but the sweep runs weekly — meaning up to 7 days elapse before tamper detection. For incident response, this might be legitimate (e.g., correcting a schema migration gone wrong). The design offers no mechanism to distinguish a legitimate superuser write from a malicious one, and no procedure for re-establishing chain integrity after a legitimate break-glass intervention.

**Failure mode 3 — KMS CMK rotation breaks genesis anchors.** The genesis event's `previous_hash` is a KMS signature using a CMK. If the CMK is rotated (AWS automatic rotation or manual rotation on key compromise), historical genesis signatures become unverifiable unless the old key material is retained. AWS KMS key rotation retains old key versions for decryption, so this is manageable — but only if the verification Lambda explicitly handles multi-version KMS signatures. The design does not specify this, and the default assumption (verify against current key version) will silently fail verification for any tenant provisioned before the last rotation.

### 3.3 The Expression Tree Complexity Ceiling Is a Schedule Risk

The design introduces a "complexity ceiling gate" at Phase 1→2: if more than 20% of contract types require node types beyond the initial set, the team escalates to a constrained formula DSL. This is good gate discipline. However, the design does not quantify what "a constrained formula DSL" means in terms of additional effort or team composition, and it does not specify the decision-making timeline.

If the Phase 1→2 gate triggers the escalation (which is a realistic outcome given the domain description — reinsurance contracts routinely involve mortality table lookups, annuity factor tables, and multi-dimensional tiered rates), the team hits a scope expansion at month 2.5 of a 9.5-month plan. The Phase 1 cost is sunk. Phase 2 scope is now undefined. The contingency (20%) is unlikely to absorb a DSL build — it was sized for integration unknowns, not a fundamental engine design change.

The design should either (a) include a provisional DSL budget in Phase 2 if the gate triggers, or (b) start with a more flexible rules engine (see Option B below) so that the gate is not a binary escalation point.

### 3.4 RLS + Connection Pool: The Design Gets This Right — But Incompletely

The design correctly identifies `SET LOCAL` as the solution to the RLS session variable leakage problem and documents the failure mode explicitly. This is a genuine strength. However, it does not address the **Lambda connection model**. Lambda functions do not maintain a persistent connection pool in the traditional sense — each warm Lambda instance holds one connection. But with Lambda scaling to many concurrent instances at month-end, the Aurora Serverless v2 connection limit (which scales with ACU but has a ceiling — 90 connections per ACU) becomes a constraint. At 8 ACU maximum, the ceiling is 720 connections. With 20 concurrent counterparty submissions, each triggering an eligibility Lambda invocation plus an API Lambda invocation per approval step, plus concurrent portal sessions, the connection count under peak load is not modelled anywhere in the design.

RDS Proxy is mentioned nowhere. For a Lambda-heavy architecture, RDS Proxy is the standard mitigation for connection exhaustion. The `SET LOCAL` approach works per-transaction, but RDS Proxy introduces its own RLS complication: the proxy multiplexes connections, and `SET LOCAL` within a multiplexed connection requires careful handling to avoid the session variable leakage the design is specifically designed to prevent. The design needs to either (a) add RDS Proxy with an explicit note on its RLS compatibility (RDS Proxy supports `SET LOCAL` in transaction-pinning mode), or (b) justify why connection exhaustion is not a risk at the stated scale.

### 3.5 Step Functions Standard Workflow Cost at Scale

At 15 counterparties with monthly cycles and an average of 10 state transitions per cycle, the Step Functions cost is low (~$40/month as modelled). However, the "Counterparty Onboarding Runbook" includes 7 steps per counterparty onboarding, and the "Adjustment Loop" in the state machine can iterate multiple times per cycle. The cost model assumes a flat $40/month regardless of the number of adjustment rounds or onboarding events. If a counterparty engages in 5 adjustment rounds per cycle across 30 counterparties, Standard Workflow transitions could reach 150K+ per month. At $0.025 per 1,000 state transitions, this is still cheap ($3.75), but the cost estimate should be sensitive-tested, not hardcoded.

More importantly: Step Functions Standard Workflows have a default account-level limit of 2,000 concurrent executions. At month-end with all counterparties submitting simultaneously, if each reconciliation cycle spawns sub-workflows for L1, L2, and counter-proposal flows, concurrent execution count could approach this limit. The design does not model concurrent Step Functions executions under peak load.

### 3.6 The Timeline Assumes Too Much Up Front

The 9.5-month plan has Phase 1 starting on 2026-05-01 and delivering "Infrastructure, Auth, Contract Registry, Multi-File Ingestion" in 2.5 months with 4 people (Architect + 2 Devs + Security). During Phase 1, the backend language is still unconfirmed (Next Steps item 6). The Phase 1→2 gate requires 100% eligibility regression against 3 contract types — but the contracts have not been extracted from Excel yet. The reconciliation managers who hold the formula knowledge are engaged "in Phase 1 workshops" — these workshops have not been scheduled and depend on reconciliation manager availability, which is not in the team's control.

The Gantt shows "Eligibility Engine — expression tree evaluator" starting at the end of Phase 1 (month 2.5) and taking 4 weeks, concurrent with the approval state machine build. This assumes the expression tree design is stable before Phase 2 begins. But the complexity ceiling gate — which determines whether the initial expression tree design is sufficient — is a Phase 1→2 gate item. In practice, the complexity ceiling assessment takes time: extract contract rules, categorise node types, count the percentage requiring escalation. This work competes directly with Phase 1 infrastructure delivery for engineer hours.

The plan is achievable under optimistic assumptions (language confirmed in week 1, contracts extracted in weeks 2–3, gate passes cleanly). Under realistic assumptions (language decision takes 3 weeks, first contract extraction workshop reveals 4 unsupported node types, compliance workshop surfaces an unexpected Solvency II requirement), Phase 2 starts late and the first counterparty live milestone (month 7.5) slips by 6–8 weeks.

### 3.7 Single-Region Availability vs. 99.9% Uptime Claim

The design states 99.9% monthly uptime. Aurora Serverless v2 Multi-AZ is ~99.99% available. Lambda is ~99.95%. CloudFront is ~99.99%. API Gateway is ~99.95%. Step Functions is ~99.9%. The system-level availability is the product of component availabilities: ~0.9999 × 0.9995 × 0.9999 × 0.9995 × 0.999 ≈ 99.78% — below the 99.9% target, before any application-level failures are counted. This is not unusual for a multi-service architecture, but it should be acknowledged rather than asserted.

---

## 4. Alternative Architectures

### Option A: ECS Fargate + RDS PostgreSQL Multi-AZ (Operationally Predictable Platform)

**Core premise:** Replace Lambda with ECS Fargate for both the API service and the eligibility engine. Keep everything else from Option 2 (Step Functions, Aurora/RDS, hash-chain ledger, Cognito, S3).

**Why it differs from Option 2:**
- Fargate containers are always warm. No ENI cold start, no VPC cold start, no provisioned concurrency configuration to maintain. Connection count to the database is predictable (2 tasks × N replicas = bounded). Month-end peaks are handled by ECS service auto-scaling on a schedule (scale up at day N-1 of month-end, scale down after submission window closes).
- RLS + connection pool interaction is straightforward: each Fargate task maintains a PgBouncer sidecar or uses a fixed-size connection pool; `SET LOCAL` behaviour is well-understood in this configuration.
- ECS Fargate removes the Lambda 15-minute execution limit concern for large eligibility computations without requiring chunked processing complexity.

**Cost trade-off:** Two always-on Fargate tasks (0.5 vCPU / 1 GB each) cost approximately $35/month combined at eu-west-2 pricing. The Lambda + API Gateway baseline is ~$45/month. The cost difference is negligible at this scale. Adding a third task for eligibility engine burst capacity during month-end adds ~$17/month. Total compute OPEX increases by ~$7/month.

**CAPEX impact:** Negligible. The developer skill set (REST API, PostgreSQL) is identical. The Step Functions integration is identical. The infrastructure code changes from Lambda deployment to ECS task definition — roughly equivalent complexity. No timeline impact.

**When this is the better choice:** If the team has prior experience with ECS and not Lambda, or if the eligibility computation for any counterparty is expected to exceed 5 minutes (making Lambda 15-minute limits a genuine operational concern).

**Weaknesses:** Always-on costs scale linearly with the number of running tasks; Lambda scales to zero. For a 2-year-post-launch scenario with 50 counterparties and concurrent month-end peaks, Fargate may require 6–8 tasks, adding ~$100/month. Still cheap, but no longer trivially comparable.

---

### Option B: Modular Monolith + PostgreSQL (Minimal Viable Trust Layer)

**Core premise:** Deploy a single containerised application (ECS Fargate or a single Lambda monolith via Lambda Web Adapter) that handles all business logic — ingestion, eligibility, approval workflow, audit — against a single PostgreSQL RDS Multi-AZ instance. No Step Functions. Approval workflow is a state machine implemented in application code with a `workflow_state` column and a background job runner (Sidekiq, Spring Batch, or equivalent).

**Why this is not Option 1:** Option 1 is a portal with manual email approval and audit triggers. Option B has a full eligibility engine, a full structured approval state machine, and a hash-chain audit ledger — all of the correctness and compliance features of Option 2, minus the AWS orchestration services.

**CAPEX impact:** Removes the Step Functions design and build effort. The approval state machine in application code is simpler than configuring Step Functions sub-workflows with task tokens and callback patterns. Estimated savings: 2–3 developer-weeks. CAPEX ~$620K vs ~$700K.

**OPEX impact:** Removes Step Functions (~$40/month) and the associated API Gateway Lambda invocation overhead. ECS Fargate replaces Lambda (~$35/month for 2 tasks). Net OPEX comparable to Option 2 (~$950/month vs ~$985/month).

**The real argument for Option B:** Step Functions adds operational complexity for a workflow that has exactly one state machine (the reconciliation cycle) and runs at monthly cadence. Step Functions Standard Workflows are valuable when (a) you need built-in retry/backoff across dozens of distinct workflow types, (b) you need audit history that integrates with CloudWatch, or (c) your workflow executions last weeks or months and you cannot tolerate a process restart losing state. All three apply here in principle — but at 15 counterparties × 1 cycle/month, a well-designed application state machine with a `workflow_state` column and a reliable background job system achieves the same outcome without the Step Functions learning curve and task token complexity.

**Weaknesses:** Application-layer state machines require the team to own retry logic, escalation timers (72-hour escalation), and durable execution history — all of which Step Functions provides for free. This is the correct trade-off only if the team has strong background-job-system experience (Sidekiq, BullMQ, Spring Batch) and limited Step Functions experience. If the team knows Step Functions, Option 2 is better here.

**Scale ceiling:** Option B scales comfortably to 50+ counterparties. Beyond 100 concurrent cycles, the background job system becomes the bottleneck — at which point introducing Step Functions or EventBridge is a clean migration (the workflow state transitions are already modelled as state machine transitions; extracting them to Step Functions is a refactor, not a rewrite).

---

### Option C: PostgreSQL + Dedicated Audit Service with S3 Event Archive (Separation of Concerns)

**Core premise:** Keep the Option 2 architecture but split the audit ledger into a separate microservice backed by S3 (primary event archive) with PostgreSQL as a secondary search index. Every audit event is written to S3 as an immutable object (S3 Object Lock — Compliance Mode, WORM) and simultaneously indexed in PostgreSQL for query. The hash chain is maintained in S3 object metadata, not in the database.

**Why this addresses the Option 2 fragility issues:**
- S3 Object Lock in Compliance Mode is genuinely immutable — not even the account root user can delete or overwrite an object within the retention period. No break-glass procedure, no superuser, no DR restore can retroactively alter a written event. This eliminates failure modes 1 and 2 identified in section 3.2 above.
- The audit service is a separate deployment unit. Its availability is decoupled from the operational database. An Aurora incident does not affect audit event durability.
- 10-year Solvency II retention is trivially enforced via S3 Object Lock retention policy — no need for Glacier tiering rules or backup job scheduling.

**Cost trade-off:** S3 Object Lock adds no cost beyond standard S3 PUT and GET pricing. At 15 counterparties × 30 audit events/cycle × 12 months = ~5,400 events/year, even at 1 KB per event, storage cost is negligible. The audit service Lambda (or Fargate sidecar) adds ~$5/month.

**CAPEX impact:** Building and deploying a separate audit service adds approximately 2 developer-weeks. The event schema design and S3 Object Lock configuration is well-understood. Net additional cost ~$25K. CAPEX ~$725K.

**Weaknesses:** Dual-write (S3 + PostgreSQL index) introduces a consistency concern: what happens if the S3 write succeeds but the PostgreSQL index write fails? The audit service must handle this with a transactional outbox or retry queue, or accept that the PostgreSQL index can be rebuilt from S3 (which is the correct answer — S3 is the system of record, PostgreSQL is a queryable index). This complicates the audit service design slightly but is a well-understood pattern.

**When this is the better choice:** When the regulatory team requires the strongest possible immutability guarantee — not "tamper-detectable" but "tamper-impossible." If FCA or a Solvency II auditor reviews the platform design and asks "can the platform operator alter audit records?", Option 2's answer is "no, we would detect it within 7 days." Option C's answer is "no, it is physically impossible." In a regulated financial services context, the second answer is materially stronger.

---

### Option D: Strangler Fig from Lightweight Portal — Phased De-risking

**Core premise:** Start with a scope closer to Option 1 (portal, basic workflow, audit triggers) but design it explicitly as a strangler fig that evolves into Option 2 within 18 months. Phase 1 delivers a working platform with the first counterparty live at month 3. Option 2's components are introduced one at a time: hash-chain ledger replaces audit triggers at month 6, Step Functions replaces email-prompted approval at month 9, eligibility engine replaces manual calculation at month 12.

**Why this is different from simply doing Option 1:** Option 1 is described as "not production-grade" and explicitly scoped to <5 counterparties. Option D is explicitly designed for production with the full Option 2 end state, but delivered incrementally. The architecture from day 1 includes the correct data model (RLS, tenant table, contracts, cycles), the correct security posture (Cognito MFA, WAF, KMS), and the correct API surface — just with simpler implementations of the calculation and workflow components initially.

**Business case for Option D:** The domain knowledge extraction risk (section 3.6) is the highest schedule risk in Option 2. Under Option D, the first counterparty goes live at month 3 using a simplified eligibility calculation (even a manual-upload-and-confirm flow), giving the team 3 months of production operation with a real counterparty before the eligibility engine is built. Domain knowledge is extracted under real operational conditions, not in workshop sessions. The expression tree design is informed by 3 months of production observation rather than speculative domain analysis.

**CAPEX impact:** Total CAPEX is comparable to Option 2 (~$700K) because the same components are built — the sequence is different, not the scope. However, cash flow is front-loaded (value delivered earlier) and the risk of a mid-project scope change (the complexity ceiling gate scenario) is substantially reduced because the engine is built after the rules are validated in production, not before.

**Weaknesses:** The reinsurer bears a period (months 3–12) where the platform exists but does not fully automate eligibility calculation — reconciliation managers still do manual work in parallel. This is not a technical weakness, but it delays the headline ROI metric (headcount reduction) by 6–12 months. The client's innovation framing ("budget is not the primary constraint") suggests they may prefer the faster full-feature delivery of Option 2. This must be a client conversation, not an architect assumption.

---

## 5. Scoring Rubric

**Dimensions and weights:**

| Dimension | Weight | Description |
|---|---|---|
| Fit-for-purpose | 25% | Does the architecture address the core trust, auditability, and multi-tenancy requirements? |
| Operational complexity | 20% | On-call burden, deployment complexity, number of moving parts at 2am |
| Cost (CAPEX + 3yr TCO) | 15% | Total investment relative to delivered value |
| Scalability | 15% | Can it handle 10× counterparty growth without re-architecture? |
| Regulatory compliance | 15% | Solvency II Art. 259, FCA SYSC 9.1, GDPR Art. 17 — strength of audit trail |
| Time-to-market | 10% | Realistic time to first counterparty live, accounting for execution risk |

**Scale: 1 = poor / 5 = excellent**

### Option 1: Lightweight Portal

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 2 | No structured approval state machine, no automated eligibility, DB triggers are weak tamper detection |
| Operational complexity | 5 | Simple — single container, single database, no orchestration services |
| Cost | 5 | ~$165K CAPEX, ~$800/month OPEX — significantly cheapest |
| Scalability | 1 | Explicitly capped at 5 counterparties; requires re-architecture for production scale |
| Regulatory compliance | 2 | DB triggers can be disabled by a DBA; no hash chain; manual export only |
| Time-to-market | 5 | 3 months to first counterparty live |

**Weighted total: (2×0.25) + (5×0.20) + (5×0.15) + (1×0.15) + (2×0.15) + (5×0.10) = 0.50 + 1.00 + 0.75 + 0.15 + 0.30 + 0.50 = 3.20**

### Option 2: Full Platform (Recommended in Design)

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 5 | Covers all requirements: structured approval, hash-chain ledger, RLS, expression tree engine |
| Operational complexity | 3 | Lambda VPC cold start risk, hash-chain operational fragility, Step Functions callback patterns — non-trivial on-call surface |
| Cost | 3 | ~$700K CAPEX, ~$985–$1,800/month OPEX, ~$736K–$765K 3-year TCO — mid-range |
| Scalability | 4 | Handles 50 counterparties comfortably; Lambda/Step Functions limits need attention beyond that |
| Regulatory compliance | 4 | Hash chain is strong but "tamper-detectable not tamper-impossible"; break-glass DR restore gap |
| Time-to-market | 3 | 9.5 months overall; 7.5 months to first counterparty live under optimistic assumptions |

**Weighted total: (5×0.25) + (3×0.20) + (3×0.15) + (4×0.15) + (4×0.15) + (3×0.10) = 1.25 + 0.60 + 0.45 + 0.60 + 0.60 + 0.30 = 3.80**

### Option 3: Event-Sourced Architecture

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 5 | Full event sourcing is architecturally optimal for this domain; every state is reproducible |
| Operational complexity | 1 | Projection rebuilds, event schema migration, specialist knowledge required — highest operational burden |
| Cost | 1 | ~$1.1M CAPEX, ~$4,500–$5,500/month OPEX — 57% more expensive on CAPEX, 4× more expensive on OPEX |
| Scalability | 5 | Designed for unlimited scale; handles 100+ counterparties without architectural changes |
| Regulatory compliance | 5 | Event log replay is the strongest possible audit model; every historical state is reconstructible |
| Time-to-market | 1 | 13 months to go-live; 37% slower than Option 2 |

**Weighted total: (5×0.25) + (1×0.20) + (1×0.15) + (5×0.15) + (5×0.15) + (1×0.10) = 1.25 + 0.20 + 0.15 + 0.75 + 0.75 + 0.10 = 3.20**

### Option A: ECS Fargate + RDS PostgreSQL (Operationally Predictable)

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 5 | Same feature set as Option 2; eliminates Lambda VPC cold start and connection pool concerns |
| Operational complexity | 4 | ECS Fargate is predictable; no cold start, no provisioned concurrency tuning; still requires RLS + connection pool discipline |
| Cost | 3 | Comparable CAPEX (~$700K); OPEX slightly higher than Option 2 at low scale due to always-on tasks (~$1,020–$1,835/month) |
| Scalability | 4 | ECS auto-scaling handles peak well; connection count remains bounded and predictable |
| Regulatory compliance | 4 | Same hash-chain model as Option 2; same DR restore gap |
| Time-to-market | 3 | Same timeline as Option 2; no meaningful difference |

**Weighted total: (5×0.25) + (4×0.20) + (3×0.15) + (4×0.15) + (4×0.15) + (3×0.10) = 1.25 + 0.80 + 0.45 + 0.60 + 0.60 + 0.30 = 4.00**

### Option B: Modular Monolith + PostgreSQL

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 4 | Full eligibility engine and hash-chain ledger; no Step Functions but workflow is correctly modelled in application code |
| Operational complexity | 5 | Simplest possible moving parts; one deployment unit, one database, one background job system |
| Cost | 4 | ~$620K CAPEX (saves 2–3 dev-weeks on Step Functions build); OPEX ~$945–$1,760/month |
| Scalability | 3 | Scales to 50+ counterparties; background job system becomes bottleneck at 100+ concurrent cycles |
| Regulatory compliance | 4 | Hash chain identical to Option 2; same DR restore gap; no Step Functions execution history (but this is an operational artifact, not a regulatory record per ADR-003) |
| Time-to-market | 4 | 2–3 weeks faster than Option 2 due to simpler workflow component; first counterparty live at ~month 7 |

**Weighted total: (4×0.25) + (5×0.20) + (4×0.15) + (3×0.15) + (4×0.15) + (4×0.10) = 1.00 + 1.00 + 0.60 + 0.45 + 0.60 + 0.40 = 4.05**

### Option C: Dedicated Audit Service with S3 Object Lock

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 5 | All Option 2 features plus physically immutable audit trail |
| Operational complexity | 2 | Adds a dual-write consistency concern (S3 + PostgreSQL index) and a separate service deployment; more moving parts |
| Cost | 3 | ~$725K CAPEX (+2 dev-weeks); OPEX marginally higher (~$995–$1,810/month); S3 Object Lock adds negligible storage cost |
| Scalability | 4 | S3 scales infinitely; PostgreSQL audit index is bounded by query patterns only |
| Regulatory compliance | 5 | S3 Object Lock Compliance Mode = tamper-impossible, not just tamper-detectable; strongest possible answer to a regulator |
| Time-to-market | 3 | Same as Option 2 effectively; 2 additional dev-weeks absorbed in Phase 2 |

**Weighted total: (5×0.25) + (2×0.20) + (3×0.15) + (4×0.15) + (5×0.15) + (3×0.10) = 1.25 + 0.40 + 0.45 + 0.60 + 0.75 + 0.30 = 3.75**

### Option D: Strangler Fig (Phased Delivery)

| Dimension | Score | Rationale |
|---|---|---|
| Fit-for-purpose | 4 | Achieves full Option 2 feature set eventually; transitional period has reduced automation |
| Operational complexity | 3 | Two distinct system states to operate; transition period adds complexity; long-term same as Option 2 |
| Cost | 4 | Same total CAPEX as Option 2 but risk-adjusted effective cost is lower (scope change risk reduced substantially) |
| Scalability | 4 | End state is Option 2; same scalability profile |
| Regulatory compliance | 3 | During transition period (months 3–12), audit trail is weaker (triggers not hash chain); full compliance only post month 12 |
| Time-to-market | 5 | 3 months to first counterparty live; 9 months to full feature delivery (comparable to Option 2) |

**Weighted total: (4×0.25) + (3×0.20) + (4×0.15) + (4×0.15) + (3×0.15) + (5×0.10) = 1.00 + 0.60 + 0.60 + 0.60 + 0.45 + 0.50 = 3.75**

---

## 6. Summary Scorecard

| Option | Fit (25%) | Ops (20%) | Cost (15%) | Scale (15%) | Compliance (15%) | TTM (10%) | **Total** |
|---|---|---|---|---|---|---|---|
| Option 1: Lightweight Portal | 2 | 5 | 5 | 1 | 2 | 5 | **3.20** |
| Option 2: Full Platform (recommended) | 5 | 3 | 3 | 4 | 4 | 3 | **3.80** |
| Option 3: Event-Sourced | 5 | 1 | 1 | 5 | 5 | 1 | **3.20** |
| Option A: ECS Fargate + RDS | 5 | 4 | 3 | 4 | 4 | 3 | **4.00** |
| Option B: Modular Monolith | 4 | 5 | 4 | 3 | 4 | 4 | **4.05** |
| Option C: S3 Object Lock Audit | 5 | 2 | 3 | 4 | 5 | 3 | **3.75** |
| Option D: Strangler Fig | 4 | 3 | 4 | 4 | 3 | 5 | **3.75** |

---

## 7. Recommendation

**Do not replace Option 2 wholesale. Make three targeted modifications:**

**Modification 1 (High priority — operational reliability):** Replace Lambda with ECS Fargate for the eligibility engine. Keep Lambda for the API service where cold start risk is acceptable (provisioned concurrency covers it). This eliminates the month-end ENI exhaustion risk on the highest-stakes component. Cost impact: negligible (+~$17/month for an on-demand eligibility Fargate task). This is the single change with the highest risk-reduction-per-cost ratio.

**Modification 2 (High priority — regulatory strength):** Add S3 Object Lock (Compliance Mode) as the primary audit event archive. Keep the PostgreSQL hash-chain index for fast query. The PostgreSQL chain becomes the query layer; S3 Object Lock becomes the immutability guarantee. This resolves the break-glass and DR restore fragility in one move and gives the compliance team a genuinely unambiguous answer to regulatory inquiries about audit record integrity.

**Modification 3 (Medium priority — schedule de-risking):** Add a provisional 3-week budget in Phase 2 for the complexity ceiling escalation scenario. If the gate passes, the budget is returned to contingency. If the gate triggers the DSL escalation, the budget is already allocated and the timeline does not slip. This costs nothing if the gate passes; it prevents a 4–6 week slip if it triggers.

**If the client places strong weight on time-to-first-value over full-feature delivery,** consider Option D (Strangler Fig) for its 3-month first counterparty live milestone. This is a client conversation, not an architect decision.

**Option B (Modular Monolith) is worth a serious second look** if the development team has limited Step Functions experience. Step Functions Standard Workflows with task tokens and sub-workflows for human approval callbacks is non-trivial to build and debug correctly. The marginal benefit over a well-designed application state machine is real but not transformative at this scale. If the team lead's assessment is "we've never built Step Functions callbacks before," build the state machine in application code and save 2–3 development weeks.

---

## 8. Issues Not Raised in the Original Design That Should Be ADRs

The following decisions are made implicitly in the design but lack ADR documentation:

1. **Lambda vs ECS for the eligibility engine** — the design defaults to Lambda for all compute but acknowledges chunked processing for large files and the 15-minute limit. The trade-off between Lambda and Fargate specifically for the eligibility engine deserves an explicit ADR with the ENI cold start risk acknowledged.

2. **Absence of RDS Proxy** — the design relies on Lambda + Aurora Serverless v2 without RDS Proxy. The decision to omit RDS Proxy (and the justification that connection counts at this scale do not warrant it) should be documented. It is a candidate for regression at scale.

3. **S3 Object Lock vs hash chain for immutability** — the design evaluated QLDB, immuDB, blockchain, and event sourcing but did not evaluate S3 Object Lock as a primary audit store. S3 Object Lock Compliance Mode is AWS's own managed solution for the exact regulatory use case described. Its omission from ADR-001 is a gap.

4. **Audit event dual-write atomicity** — the design describes audit events written via INSERT-only role but does not specify the atomicity model: does the application write the audit event in the same database transaction as the operational state change, or as a separate call? If separate, what happens on partial failure? This is the Outbox Pattern decision and it has correctness implications for the compliance audit trail.

---

*This document is an AI-assisted internal review and is not a client-facing deliverable.*
