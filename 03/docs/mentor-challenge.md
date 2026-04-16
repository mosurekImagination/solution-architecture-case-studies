# Mentorship Exercise 03 — Critical Design Challenge

**Exercise:** Reinsurance Reconciliation Platform — B2B Trust Infrastructure  
**Mentee:** Tomasz Mosur  
**Review type:** Senior adversarial critique — all decisions challenged  
**Date:** 2026-04-16

---

## Framing

The initial analysis (see [mentor-analysis.md](mentor-analysis.md)) confirmed the work is production-grade in framing and coverage. This review goes deeper: every major decision is challenged on elegance, scalability, and maintainability. The goal is not to find fault — it is to surface the second-order thinking that separates a good architect from a great one.

---

## Decision-by-Decision Challenge

### 1. Hash Chain: The Write Serialization Trap

**What the design says:** A single `audit.events` table with a global SHA-256 hash chain — each row's `previous_hash` references the preceding row's `event_hash`. Verified weekly by a Lambda job.

**The challenge:**

A global hash chain is a **sequential write bottleneck by design**. To insert row N you must first read row N-1 to get its hash. At low write volume (tens of events per day) this is invisible. But:

- If 20 counterparties submit files simultaneously at month-end, you get 20 concurrent INSERT attempts competing for the chain tip. You must serialize them. This means either a table-level lock (catastrophic for latency) or an application-level mutex (a distributed lock, which is an operational nightmare).
- The design does not address this. It implies a single chain across all tenants.

**More elegant approach:** Partition the hash chain **per tenant**. Each tenant has their own independent chain. Row N's `previous_hash` references the preceding event for the *same tenant_id*. This eliminates write contention entirely — 20 tenants write 20 independent chains in parallel. The compliance query is the same. The verification Lambda runs per-tenant. This is strictly better.

**Second-order question the design misses:** What is row 1's `previous_hash`? The design says "empty string for row 1." That is correct but incomplete — the genesis event (tenant provisioning) should be the chain anchor, signed with a key stored in AWS KMS. Without a signed genesis, an attacker who can delete and re-insert all rows cannot be detected (the chain will re-verify from a new empty-string start). A KMS-signed genesis block closes this gap.

**Verification cadence challenge:** Weekly Lambda verification means a tampered record could sit undetected for up to 7 days. For a platform whose primary value proposition is trust, this is a long window. **Continuous verification on every read** of a sealed cycle is trivial to implement: recompute the chain for the cycle's events at query time. The cost is negligible for a monthly reconciliation system.

---

### 2. AWS Step Functions: Right Tool, Wrong Scope

**What the design says:** AWS Step Functions Standard Workflows with wait-for-callback for the 16-state approval machine.

**The challenge:**

Step Functions Standard Workflows charge **per state transition** (~$0.025 per 1,000 transitions). For a 16-state machine with multiple adjustment rounds, a single reconciliation cycle might traverse 20–40 state transitions. At 30 counterparties × 12 months × 30 transitions = ~10,800 transitions/year. Cost is ~$0.27/year — negligible. So cost is not the issue.

The real challenge is **coupling**: Step Functions execution history is retained for only **90 days** by default (configurable up to 1 year for Standard Workflows, but not indefinitely). The design relies on Step Functions history as a "natural secondary audit artifact." That is wrong — it is an operational convenience, not a compliance artifact. After 90 days the execution history is gone. The hash-chain ledger must be the authoritative audit record, not Step Functions. The design blurs this distinction.

**A more elegant model:** The state machine drives the process; the audit ledger records the truth. Step Functions is the engine, not the archive. This is a small wording correction but a significant architectural clarification — especially for a regulator reading the design.

**Second challenge:** The 16-state machine is described but not diagrammed with explicit guard conditions. What happens if a Step Functions execution is started twice for the same cycle? (Idempotency is not addressed.) What is the compensation logic if the eligibility engine task fails mid-execution? Standard Workflows have at-least-once semantics for Lambda invocations — if the eligibility engine is not idempotent, you could compute and log two different results for the same cycle. This is a trust system — a duplicate result is a compliance incident.

---

### 3. Two Cognito User Pools: Unnecessary Complexity

**What the design says:** Two separate Cognito deployments — one for external counterparty users (standalone User Pool), one for internal users (SAML-federated User Pool).

**The challenge:**

Two Cognito User Pools means two JWT issuers, two sets of token validation logic in the API service, two sets of Cognito configuration to maintain, and two places to audit authentication events. There is no architectural reason for this split.

**More elegant approach:** One Cognito User Pool, two identity providers within it:

- External users: Cognito-native (email/password + MFA)
- Internal users: SAML federation from corporate IdP

The User Pool issues JWTs with a `custom:user_type` claim (`INTERNAL` or `COUNTERPARTY`). The API service validates one JWT issuer, reads one claim. The architecture diagram becomes simpler. The IAM and KMS configuration halves. The cognitive load for a new engineer drops.

The design's justification for two pools is unstated. This looks like an instinct, not a decision. It should be an ADR with a clear rationale — or simplified to one pool.

---

### 4. RLS Session Variable: A Race Condition Waiting to Happen

**What the design says:** `current_setting('app.current_tenant_id')` is set as a PostgreSQL session variable by the API service on each connection. RLS policies reference this setting.

**The challenge:**

This pattern is correct in principle but brittle in practice. The API service uses a **connection pool** (PgBouncer, RDS Proxy, or the ORM's built-in pool). Session variables live for the duration of a *database session*. In a connection pool, sessions are reused across requests. If a request for Tenant A sets `app.current_tenant_id = 'A'` and the connection is returned to the pool before the variable is cleared, the next request on that connection sees Tenant A's data — regardless of who is authenticated.

This is not a theoretical risk. It is a known production failure mode for RLS + connection pooling that has caused real data leaks. The design does not mention it.

**The fix** — choose one:

1. Set the session variable **inside a transaction** and clear it after (safest with PgBouncer in transaction-pooling mode)
2. Use RDS Proxy with IAM authentication, which provides session isolation guarantees
3. Use `SET LOCAL` instead of `SET` so the variable is transaction-scoped

This should be in the design — or at minimum in the risks register. Its current absence is the most concrete security gap in the entire document.

---

### 5. Eligibility Engine: Wrong Compute Model

**What the design says:** Eligibility Engine as a separate ECS Fargate *task* — invoked by Step Functions, runs to completion, exits.

**The challenge:**

An ECS task has a **cold start overhead** of 10–30 seconds (pulling image, spinning container, initializing runtime). For a process that runs once per counterparty per month, this is acceptable. But the design has a 15-minute SLA for eligibility results. Cold start eats a significant slice of that budget.

**More importantly:** The design puts the eligibility engine in a *separate container* from the API service but uses Python — while the API service is Node.js. Now you have two languages, two Docker images, two deployment pipelines, two sets of dependencies to maintain, two runtimes to patch for CVEs. For a team of 3 developers, this is a meaningful operational burden.

**Challenge the separation itself:** Why is the eligibility engine a separate container? The stated reason in the design is implied (scalability, isolation). But the eligibility calculation is **stateless and CPU-bound** — it reads a contract ruleset, applies it to a file, writes a result. This is a perfect Lambda function:

- No cold start problem for monthly invocations (provisioned concurrency for month-end windows)
- No separate ECS task infrastructure to maintain
- Step Functions integrates with Lambda natively
- Scales horizontally for free if counterparty volume grows
- $0 cost when idle (vs. ECS task startup overhead)

The design chose ECS task because "it fits the architecture pattern." A senior architect asks: does it need to?

---

### 6. The Monolithic API: One Service Doing Too Much

**What the design says:** A single "API Service" (Node.js, ECS Fargate) handles authentication, business logic, file coordination, workflow triggers, and audit ledger writes.

**The challenge:**

Mixing concerns creates **scaling asymmetry**. The portal (human users browsing cycles) has fundamentally different traffic characteristics from file ingestion (burst at month-end). If you need to scale the file ingestion path, you scale the entire API — including the portal endpoints that don't need more capacity.

This is not an argument for microservices. It is an argument for **separation of read and write paths** at minimum:

- **Command path:** File ingestion, workflow triggers, audit writes — event-driven, can tolerate async
- **Query path:** Portal browsing, dashboard, audit queries — synchronous, latency-sensitive

This is the read/write separation pattern (CQRS-lite), not full event sourcing. It does not require a major redesign — it just means the API module structure reflects these two concerns, and scaling rules are configured separately for each ECS service. Maintaining this separation from day one is far cheaper than retrofitting it when month-end load causes portal latency.

**Maintainability implication:** A single Node.js API that grows to handle 26 functional requirements across 8 epics will become a large codebase. Without explicit module boundaries, new engineers will create cross-cutting dependencies. The design should at minimum define the module structure (e.g., `contracts/`, `cycles/`, `audit/`, `ingestion/`), not just the container.

---

### 7. Data Model: Two Hidden Schema Traps

**What the design says:**

```sql
contracts:            rules_json  JSONB
eligibility_results:  result_json JSONB
```

**The challenge on `rules_json`:**

Storing the entire contract ruleset as an opaque JSONB blob is a schema trap. You cannot query it. You cannot validate it at the database layer. You cannot enforce that rule version 2 has the same structure as rule version 1. The design acknowledges the need for "dynamic contract structure" — but dynamic does not mean unstructured.

A more maintainable approach: define a JSON Schema for the rule format (even if the values vary by contract). Validate incoming rule uploads against the schema. Store the schema version alongside the rules blob. Now when the eligibility engine reads a ruleset, it knows which interpreter version to use. This is how production rule engines work.

**The challenge on `result_json`:**

`eligibility_results.result_json JSONB` with `compensation_amount NUMERIC` stored separately. If `result_json` contains the calculation that produced `compensation_amount`, they can diverge. An engineer could update `compensation_amount` without updating `result_json`. The hash-chain audit ledger would catch this (because the compensation amount is presumably in the audit event payload), but the operational database itself is inconsistent.

**More elegant:** Store `compensation_amount` only in `result_json`. Extract it as a generated column:

```sql
compensation_amount NUMERIC
  GENERATED ALWAYS AS ((result_json->>'compensation_amount')::numeric) STORED
```

One source of truth; no divergence possible; still queryable and indexable.

---

### 8. Scalability: The Design Assumes Low Volume

**What the design says:** Up to 20 concurrent file uploads; 5–50 counterparties; `db.r6g.large` ($480/month).

**The challenge:**

The mentor explicitly stated the real production project grew from 5 to 70+ engineers. If the platform succeeds, the counterparty count *will* grow. The design's Option 2 cap of 50 counterparties is not a technical limit — it's an assumption. What happens at counterparty 51?

The design says "migrate to Option 3 (event sourcing)" — but that is a full re-architecture. The migration path is hand-waved in one paragraph. A senior architect would ask:

- What *specific* bottleneck triggers the migration? (CPU? DB connections? Step Functions throughput? Hash chain write speed?) The design does not say.
- Can the database layer be evolved incrementally (add read replicas, partition the audit table by tenant) before full event sourcing is needed?
- The assumption that RLS-based multi-tenancy is "sufficient for 10–30 counterparties" is arbitrary. RLS performance degrades with row count, not tenant count. The actual limit depends on data volume per tenant, not tenant count.

**More elegant:** Add a scalability section that identifies the *specific* architectural components that constrain scale and the *specific* metrics that would trigger each evolution step. This turns "migrate to Option 3 when needed" into a concrete architectural runbook.

**The `db.r6g.large` question:** At $480/month for a system that processes files *monthly*, this is a 4 vCPU, 16GB memory instance running mostly idle. The real cost driver is Multi-AZ (synchronous replication standby), not instance size. A `db.r6g.medium` (2 vCPU, 8GB) could serve the initial load and be upgraded when metrics show it's needed. Right-sizing at design time signals cost discipline to the client.

---

### 9. AWS Transfer Family SFTP: $200/Month for a Maybe

**What the design says:** SFTP via AWS Transfer Family as a fallback, always-on at ~$200/month.

**The challenge:**

AWS Transfer Family charges $0.30/hour regardless of usage — ~$216/month. For a feature that is explicitly a fallback for "counterparties with legacy automation," it may never be used by the initial counterparty wave. Over year 1 that is $2,592 spent on an unused service.

**More pragmatic:** Provision Transfer Family only when a specific counterparty requests it. The architecture supports this — the file ingestion path is the same regardless of upload mechanism. This is a deployment decision, not an architecture decision. Document it as "SFTP enabled on-demand per counterparty" rather than "always-on fallback."

---

### 10. Team Composition: Missing a Platform Engineer

**What the design says:** 1 Architect + 3 Senior Developers + 1 Security Engineer + 1 QA Engineer.

**The challenge:**

Who builds the CI/CD pipeline? Who writes the Terraform (or CDK) for the VPC, RDS, ECS cluster, IAM roles, CloudTrail config, Security Groups? Who manages AWS Organizations and Control Tower? Who responds to the PagerDuty alert at 2am when RDS fails over?

The design deploys to three environments with Multi-AZ RDS, ECS Fargate, CloudFront WAF, and Cognito. This is non-trivial infrastructure. In the proposed team, these tasks fall to the architect and senior developers — which means feature delivery slows or infrastructure quality suffers. Neither is acceptable for a trust-critical platform.

A production-grade deployment of this complexity typically requires at least 0.5 FTE platform/DevOps engineer, even if contracted. The cost model should reflect this or explicitly state that the reinsurer's internal IT team absorbs these responsibilities — which requires knowing their capacity (currently flagged as unknown).

---

### 11. DR Strategy: RPO/RTO Claims Are Optimistic

**What the design says:**
- RTO < 1 hour for full region failover
- RPO = 0 for AZ failure (Multi-AZ synchronous replication)
- RPO = 24h for full region failure (AWS Backup cross-region snapshots)

**The challenge:**

RTO < 1 hour for a full region failover requires:

1. Detecting the outage (CloudWatch alarm → PagerDuty → engineer wakes up): 5–15 min
2. Deciding to fail over (someone must authorize this): 5–30 min
3. Restoring from snapshot in eu-west-1: 20–45 min depending on DB size
4. Updating DNS / CDN origin: 5 min
5. Validating the restored system: 10–20 min

That is a 45–115 minute process under favorable conditions. The 1-hour RTO is achievable but tight — and **no one has tested it**. The design says "DR runbook tested quarterly" but the runbook hasn't been written yet and Phase 1 doesn't include a DR drill.

**More honest framing:** State RTO as a target, not a guarantee, until the runbook is tested. Add a DR drill to the Phase 4 checklist.

**Deeper challenge:** RPO = 24h for a full region failure means up to 24 hours of reconciliation activity could be lost. For a trust-critical system: can a reconciliation cycle that was in-progress during the outage be reconstructed? The hash-chain ledger in the primary region may not be fully replicated at the point of failure. The design does not address cycle reconstruction.

---

### 12. The "Boring Option" Narrative: Right Conclusion, Incomplete Reasoning

**What the design says:** PostgreSQL chosen over blockchain, QLDB, immuDB — "boring and proven."

**The challenge:** The narrative is correct but relies partly on *authority* (mentor's production experience with immuDB) rather than *first principles*. A regulator or CTO reading ADR-001 might push back: "If immuDB had issues with a .NET client, why not use a Go client?" or "QLDB was discontinued but its cryptographic verification model was sound — why not implement the same model in PostgreSQL yourself?"

The design should answer these challenges from first principles:

1. **Why PostgreSQL specifically** (vs. Aurora PostgreSQL, CockroachDB, YugabyteDB)? Aurora PostgreSQL would provide better read scaling (Aurora Replicas) with the same SQL interface. For a growing counterparty book, this matters.

2. **The hash chain is application-level, not database-level.** A DBA with a maintenance window could truncate and rebuild the hash chain without triggering the weekly Lambda. The true protection is a **KMS-signed genesis anchor** combined with **external backup verification** (monthly export to a storage account the reinsurer does not control). Neither is in the design.

---

### 13. The Missing Idempotency Layer

**What the design says:** File submission → S3 upload → audit event → Step Functions workflow start. No mention of idempotency.

**The challenge:**

What happens if a counterparty uploads the same file twice? The design validates SHA-256 checksum on receipt — but does it deduplicate? If a duplicate file triggers a second Step Functions execution and a second eligibility computation, the audit ledger now has two `CYCLE_STARTED` events for the same period. Which is canonical?

For a trust system, duplicate records are a compliance incident, not an edge case. The design must define:

- What makes a file submission unique? (`tenant_id + contract_id + period`? SHA-256 hash?)
- What is the idempotency check? (Before or after S3 write?)
- What error does the counterparty receive on duplicate submission?

This is not mentioned in the functional requirements, the data model, or the risks section.

---

## Scalability & Maintainability Summary

| Concern | Current Design | Challenge | Recommended Approach |
|---|---|---|---|
| Hash chain write contention | Global chain, single sequence | Serial writes block under concurrent load | Per-tenant chain; KMS-signed genesis |
| Hash chain verification window | Weekly Lambda (7-day blind spot) | Tampering undetected for 7 days | Continuous verification on sealed-cycle reads |
| Cognito duplication | Two User Pools | Double the config, double the audit surface | One pool, two identity providers |
| RLS + connection pooling | Session variable, pooled connections | Silent cross-tenant data leak risk | Transaction-scoped `SET LOCAL`; RDS Proxy |
| Eligibility engine compute model | ECS Fargate task (cold start, two runtimes) | 10–30s cold start; dual language maintenance | Lambda with provisioned concurrency |
| API modularity | Single monolith | Read/write asymmetry; uncontrolled growth | Explicit module boundaries; separate scaling rules |
| Contract rules schema | Opaque JSONB | No validation, no versioning, interpreter coupling | JSON Schema + schema version + generated column |
| Scalability trigger | Undefined ("migrate to Option 3") | No concrete signal for when to evolve | Instrument bottlenecks; define migration thresholds |
| SFTP cost | Always-on Transfer Family | $216/month for unused fallback | On-demand provisioning per counterparty request |
| DR runbook | Claimed RTO < 1 hour, untested | Optimistic; no cycle reconstruction plan | Tested DR drill in Phase 4; honest RTO ranges |
| Idempotency | Not addressed | Duplicate file → duplicate audit events | Deduplication check on (tenant, contract, period) |
| Team composition | No platform engineer | CI/CD and infra responsibility falls on devs | 0.5 FTE platform engineer or explicit IT handoff |

---

## The One Question That Reframes Everything

The design recommends Option 2 and defers Option 3 (event sourcing) for "when counterparty volume exceeds 50." But there is a more fundamental question:

**Does the data model need to be the same for the operational system and the audit system?**

The current design uses a CRUD operational database (mutable) + an audit ledger (append-only). This is the right separation. But consider: the reconciliation cycle is inherently a state machine — a sequence of events, not a current state. The "current state" (cycle status, who approved, what amount) is always derivable from the event history.

If you model the operational data as **immutable events from day one** (even just for the reconciliation cycle entity), you get:

- The audit ledger and the operational record are the same thing — no duplication
- Full history replay without a separate hash chain (the append-only structure is the proof)
- Contract rule versioning falls out naturally (each cycle references the rule version in effect at the time)
- No `UPDATE` statements anywhere in the cycle lifecycle

This is **partial event sourcing** — applying event sourcing only to the lifecycle-critical reconciliation cycle entity, not to tenants, contracts, or users. It is simpler than full event sourcing (Option 3) but architecturally cleaner than the current CRUD + hash-chain hybrid. It eliminates the RLS + connection pool race condition for audit writes, eliminates the hash chain write contention, and removes the need for the weekly verification Lambda.

This approach was available but not considered. A senior architect would have it on the table.

---

## What This Exercise Reveals

The design demonstrates strong architectural *breadth* — all the right components are present, all major risks are identified, the technology choices are defensible. The gaps are at the *depth* level: the second and third-order consequences of each decision that only surface when you stress-test them.

**Patterns to internalize:**

1. **Sequential structures are write bottlenecks.** Always ask: can this be partitioned?
2. **Session state + connection pools = silent bugs.** Connection pooling is default in production; design for it explicitly.
3. **Opaque blobs (JSONB) are schema debt.** They feel flexible; they are actually coupling deferred.
4. **Idempotency is not an edge case in trust systems.** It is a first-class requirement.
5. **DR runbooks are not architecture until they are tested.** An untested RTO claim is a guess.
6. **Event sourcing is a spectrum.** You do not have to event-source everything to capture the benefits where they matter most.

---

## Discussion Questions for Next Mentorship Session

1. **Hash chain per-tenant:** Why was a global chain designed instead of a per-tenant chain? What would the migration look like if you wanted to change this after go-live?

2. **RLS + connection pooling:** Walk me through what happens step by step when two requests from different tenants hit the API simultaneously. Where exactly does the tenant ID get set on the database connection? What happens if the pool reuses the connection before it's been reset?

3. **Eligibility engine as Lambda vs. ECS task:** What is your argument for ECS task? What would have to be true about the eligibility calculation for ECS to be the right choice over Lambda?

4. **Partial event sourcing:** If you modelled `reconciliation_cycles` as an immutable event log from the start, what would you no longer need in the current design? Draw the simplified data model.

5. **The SFTP line item:** You included $200/month for Transfer Family. How many counterparties would need to use it to justify that cost? What would you do if none of the first 10 counterparties needed it?
