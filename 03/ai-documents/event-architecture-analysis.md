# Data & Event Architecture Analysis — Reinsurance Reconciliation Platform

**Type:** AI-assisted Architecture Analysis
**Author:** Tomasz Mosur
**Date:** 2026-04-26
**Subject:** Comparative analysis of data and event architecture options

---

## 1. Purpose and Scope

This document evaluates five data and event architecture options for the reinsurance reconciliation platform. The current recommendation is Option 1 (PostgreSQL + S3 Object Lock). The question being answered is whether that recommendation holds under scrutiny, or whether a PostgreSQL-only approach, event sourcing, or an outbox-based model is more appropriate given the system's actual workload, team size, and regulatory constraints.

The audience is the architect who designed the system. This document challenges the current recommendation honestly and, where S3 Object Lock is still the right answer after examining alternatives, says so directly.

---

## 2. Context Signal: The Scale Problem

Before evaluating any architecture, the single most important contextual fact must be stated plainly:

**This system processes 15–20 counterparty files once a month.**

That is approximately 180–240 meaningful business events per year. The peak load is simultaneous file submission at month-end — not a high-frequency stream, not a continuous flow. It is a monthly batch with a 15-minute SLA per counterparty.

This context matters because event-driven architectures earn their operational cost through two mechanisms: decoupling producers from consumers at high throughput, and enabling temporal decoupling (the producer does not wait for the consumer). At 180 events/year, neither benefit applies with enough force to justify the operational investment required. Every architecture analysis below is assessed against this baseline.

---

## 3. The Superuser Question (Cross-Cutting Concern)

The Solvency II Art. 259 question — can a superuser alter audit records, and is that detectable, and when? — must be answered consistently across all five options. This is the regulatory crux of the entire architecture choice.

The relevant legal threshold is not stated explicitly in Art. 259 itself, which requires that undertakings maintain "appropriate systems and structures" for record-keeping. UK FCA SYSC 9.1 similarly requires records to be "complete and accurate." Neither regulation specifies "tamper-impossible" as the technical standard. However:

- The practical regulatory expectation, as interpreted by Big 4 audit firms in Solvency II engagements, is that the platform operator cannot unilaterally alter records without detection.
- "Tamper-detectable within N days" is legally defensible if the detection window is short enough that no regulatory submission cycle could be completed without the tampering being caught first.
- "Tamper-impossible" is a stronger position and eliminates the need to argue the detection window at all.

The distinction matters because it governs whether S3 Object Lock is a requirement or a belt-and-suspenders addition.

---

## 4. Option Analysis

### Option 1: PostgreSQL + S3 Object Lock (Current Recommendation)

**Architecture summary:** Mutable operational state in PostgreSQL (RLS, hash-chain index). Every audit event written to an S3 Object Lock Compliance Mode bucket (WORM). PostgreSQL is the query layer; S3 is the immutability guarantee. Dual-write on every audit event.

**Superuser attack surface:** A PostgreSQL superuser can UPDATE or DELETE any row in the audit schema, including setting `event_hash` and `previous_hash` to recomputed values that would survive the next verification sweep — *if* the attacker can regenerate a consistent chain hash. They cannot generate a valid KMS-signed genesis anchor without the CMK, which is IAM-controlled and logged in CloudTrail. So in practice: pre-genesis events cannot be forged (KMS barrier), but post-genesis events can be altered if the attacker has superuser access and can recompute SHA-256 hashes (which is computationally trivial). Detection: the next weekly verification sweep. Detection window: up to 7 days.

The S3 Object Lock record is unaffected by any PostgreSQL operation. An auditor can always compare the PostgreSQL chain against the S3 archive and detect divergence. This is the key difference from the outbox-only approach.

**The dual-write consistency problem — prescribing the correct pattern:**

The architecture review noted this as an open gap. The correct resolution is: **S3 is the system of record; PostgreSQL is a rebuildable query index.** The write sequence must be:

1. Write the audit event JSON to S3 (Object Lock WORM, retention 10 years). On success, store the S3 key and ETag in the PostgreSQL row.
2. Write the PostgreSQL hash-chain row, referencing the S3 key.
3. If step 2 fails: the S3 record exists and is permanent. The PostgreSQL index is inconsistent and must be repaired. A background reconciliation job compares S3 event objects against the PostgreSQL index and re-inserts any missing rows.

If step 1 fails: nothing is written. The transaction rolls back. The cycle retries.

This means S3-first, with async PostgreSQL index repair as the failure recovery path. The PostgreSQL chain is never the source of truth; it is a derived, queryable representation of the S3 archive.

**Operational failure modes (confirmed from architecture review):**
- Break-glass superuser access corrupts the PostgreSQL chain silently for up to 7 days (S3 Object Lock record is unaffected — the divergence is detectable by comparing them).
- Aurora PITR restore after a storage incident loses the in-flight PostgreSQL chain tip. The S3 archive is unaffected. Repair: rebuild PostgreSQL index from S3 events after restore.
- KMS CMK rotation breaks genesis signature verification for tenants provisioned before the rotation unless the verification Lambda handles multi-version keys.

**Fit for modular monolith + ECS Fargate:** Excellent. The dual-write is a synchronous call from the application service. No new infrastructure components beyond S3 bucket configuration.

**Assessment:** This is the right answer for Solvency II and for a 6-person team. The PostgreSQL-only hash chain is operationally necessary for query performance (audit trail queries by cycle, tenant, date range). S3 Object Lock is the immutability guarantee that makes the "tamper-impossible" answer available to auditors. The dual-write complexity is real but manageable with the S3-first pattern prescribed above.

---

### Option 2: Full Event Sourcing

**Architecture summary:** No mutable state tables. All current state is derived by replaying an append-only event log (EventStoreDB, DynamoDB Streams, or a PostgreSQL append-only table). PostgreSQL, if present, is a pure projection/read model that can be rebuilt at any time from the event log.

**Superuser attack surface:** In EventStoreDB: no UPDATE/DELETE API exists; the storage layer is append-only by design. A superuser with direct filesystem access to the EventStoreDB data directory can corrupt it, but this requires physical server access, not just DB credentials — a substantially higher attack surface. In a DynamoDB Streams variant: DynamoDB does support DeleteItem and UpdateItem — so a sufficiently privileged AWS IAM principal can alter records. The IAM audit trail in CloudTrail provides detection, but the records themselves are mutable. In a home-grown PostgreSQL append-only table: functionally identical to the PostgreSQL outbox (Option 4) — superuser can UPDATE rows.

**The scale argument against event sourcing:**

Full event sourcing is architecturally elegant. It is also genuinely expensive to operate:

- **Projection rebuilds:** When you need to answer "what was the state of cycle X at time T?" you either maintain a snapshot or replay all events up to T. For 180 events/year over 10 years = 1,800 events total. A full replay from genesis takes milliseconds. This is actually the *counterargument* — at this scale, projection rebuilds are trivially cheap, which removes the main operational objection.
- **Event schema migration:** You can never change the shape of a past event. When business rules change (and they will — reinsurance contracts evolve), historical events are frozen in the old schema. Versioning strategies (upcasters, schema registry) add complexity that a 6-person team must own indefinitely. A single schema migration that would be 2 hours of Flyway migration script in a relational model becomes a multi-week event migration exercise in event sourcing.
- **Specialist knowledge:** The team needs to understand event sourcing patterns deeply — not just append-only inserts, but snapshot management, projection consistency, causation IDs, correlation IDs, and idempotent consumer design. This knowledge is non-trivial to acquire and maintain at a 6-person scale.
- **The payload is wrong-shaped for this domain:** Event sourcing shines when the business process is fundamentally a stream of user-initiated events (e-commerce, banking ledgers). The reinsurance reconciliation workflow is a structured state machine with a fixed lifecycle. The state machine in PostgreSQL (`AWAITING_FILES` → `ELIGIBILITY_RUNNING` → `REINSURER_REVIEW` → `CYCLE_SEALED`) is already a correct and complete model of the domain. Replacing it with an event log adds no information; it changes the storage medium.

**Second-order problem:** 15 counterparties × 12 cycles/year × ~30 events/cycle = ~5,400 business events per year. This is the volume of a quiet afternoon on a medium-scale e-commerce platform. The infrastructure required to operate EventStoreDB correctly (cluster sizing, projections, catch-up subscriptions, competing consumers) is sized for thousands of events per second. Running it for 5,400 events per year is analogous to containerising a static HTML page.

**Verdict:** Full event sourcing is not justified here. The scale does not warrant the operational investment. The domain model (a structured state machine with a fixed lifecycle) is better represented by an explicit state machine than by an implicit projection over an event stream. The architecture review's scoring of 1/5 on operational complexity is correct.

---

### Option 3: CQRS-lite — Event-Driven with Read Models

**Architecture summary:** Events are the primary write path. PostgreSQL is a projected read model built from events, not the source of truth. No requirement to rebuild all state from events — projections are kept up to date incrementally. Event bus: SQS or EventBridge.

**Superuser attack surface:** The event bus (SQS or EventBridge) does not store events permanently — SQS messages are deleted after consumption, EventBridge events are transient by default. If PostgreSQL is the read model and events are gone, a superuser who alters the PostgreSQL read model leaves no detectable trace once the bus event is gone. For Solvency II purposes, this is the *weakest* audit model of the five options unless a durable event archive is added (at which point it converges to Option 1 with extra steps).

**The eventual consistency boundary:**

CQRS-lite introduces eventual consistency between the write path (event emission) and the read model (PostgreSQL projection). The architecture review correctly identifies this as the critical design question. For this system:

- **Approval click → manager's view not updated immediately:** If a reconciliation manager approves a proposal and the read model update is delayed by 500ms due to SQS message propagation, the manager sees the "awaiting approval" state for a brief moment. This is tolerable.
- **Approval click → counterparty's portal not updated immediately:** Same as above. Tolerable.
- **Approval click → the cycle state machine transitions incorrectly:** This is *not* tolerable. If the Step Functions state machine reads the PostgreSQL read model to decide which state to transition to, and the read model is stale, the state machine could take the wrong branch. This is a correctness problem, not a UX problem.

The consistency boundary must therefore be: **the Step Functions state machine and the eligibility engine must read from the write path (the canonical event log or the strongly consistent operational store), not from the CQRS read model.** The read model is for portal display only.

This constraint fundamentally limits the value of CQRS-lite for this system. The two most latency-sensitive consumers (Step Functions, eligibility engine) cannot use the eventual-consistent read model. They need the strongly consistent write path. If those consumers are already using the strongly consistent PostgreSQL operational store directly, the CQRS read model is only serving portal display queries — which could be served by the operational store with read replicas at this scale.

**Fit for modular monolith + ECS Fargate:** Poor. CQRS-lite introduces an event bus (SQS or EventBridge), a projection updater process, and eventual consistency management — three new operational concerns — to serve portal display queries that the operational database already answers adequately.

**Verdict:** CQRS-lite is over-engineered for this workload. The eventual consistency it introduces creates correctness risks in the state machine that require careful boundary management. The benefit (decoupled read scalability) is not needed at 15–20 counterparties. The architecture review's concern about event-driven architecture earning its operational cost applies here directly.

---

### Option 4: PostgreSQL Outbox Pattern (No S3)

**Architecture summary:** Everything in PostgreSQL. State changes and outbox events written in the same DB transaction. Background worker delivers outbox events. No S3. Immutability guaranteed by the PostgreSQL hash chain and replication/backup, not by WORM storage.

**Superuser attack surface:** This is the central problem with this option.

A PostgreSQL superuser can:
1. UPDATE any row in the `audit.events` table, including `event_hash` and `previous_hash`.
2. Recompute the SHA-256 chain consistently from the tampered row forward.
3. The weekly verification sweep will not detect the tampering if the chain is consistently recomputed.

The *only* protection is the KMS-signed genesis anchor: an attacker cannot forge the genesis `previous_hash` without the CMK. But the genesis anchor only protects against inserting a *replacement* chain from scratch. It does not protect against in-place modification of post-genesis events if the attacker can recompute the chain forward from the tampered point.

To be precise: if the attacker modifies row N and recomputes the hash of row N and all subsequent rows, the chain will appear valid. The weekly sweep will pass. There is no detection mechanism.

This is not a theoretical risk. A DR restore from a snapshot, followed by a team member running a one-line SQL fix to resolve a data integrity issue, followed by a manual chain recompute, is a realistic scenario. The audit trail is silently incorrect. This is the scenario that a regulatory auditor asking "can your team alter audit records?" is specifically testing for.

**The "tamper-detectable in 7 days" framing in the prior architecture is too optimistic:** The hash chain detects tampering if the attacker *does not* recompute the chain. A PostgreSQL superuser who knows the hash chain algorithm (it is documented in the solution design) can recompute the chain trivially. Detection requires the KMS genesis anchor — but only for complete chain replacement, not for in-place modification.

**Is "tamper-detectable" sufficient for Solvency II Art. 259?** As noted in Section 3, UK regulatory practice accepts tamper-detectable if the detection window is short and the detection mechanism is independent of the operational team. A weekly sweep run by a Lambda function is *not* independent — the operational team can disable the Lambda. S3 Object Lock is independent of the operational team — not even the account root user can delete objects within the retention period.

**Verdict:** The outbox pattern is a useful pattern for reliable event emission (used in Option 1 to guarantee S3 audit event delivery). As a *replacement* for S3 Object Lock, it is not acceptable for a Solvency II-regulated platform. The hash chain provides tamper detection only against unsophisticated tampering. A motivated insider with superuser access can alter records undetectably.

---

### Option 5: PostgreSQL with Extensions

This option asks: can PostgreSQL alone — with the right extensions — handle both operational state and immutable audit, eliminating S3 entirely?

**5a. pgaudit**

pgaudit logs all SQL statements (session audit) or specific object accesses (object audit) to the PostgreSQL log. The log destination can be `csvlog`, `syslog`, or a foreign table.

Limitations:
- pgaudit logs are written to the PostgreSQL log, which is a file on the DB server filesystem. A superuser can rotate, truncate, or disable the log.
- Even if logs are shipped to CloudWatch Logs, a superuser with the IAM role to modify CloudWatch log groups can delete them (unless CloudWatch log group retention is locked, which requires a separate IAM policy).
- pgaudit records *SQL operations*, not *business events*. For Solvency II purposes, the audit trail needs to record "Reconciliation Manager Alice approved Cycle C-2026-04 at 14:32 UTC" — not "INSERT INTO audit.events executed by role app_writer." pgaudit does not replace a structured business event log.

**Verdict on pgaudit for Solvency II compliance:** Insufficient. It is a useful supplementary control (detecting unexpected DML on production tables) but not a substitute for a structured, immutable event archive.

**5b. temporal_tables**

temporal_tables implements bi-temporal row versioning using PostgreSQL triggers. Every UPDATE creates a new "current" row and archives the old row to a history table with `valid_from`/`valid_to` timestamps. The history table preserves every state transition.

What this provides: complete point-in-time reconstruction of any row's state. For the operational database (contracts, reconciliation cycles, eligibility results), this is valuable and worth implementing regardless of the audit storage decision.

What this does not provide:
- The history table is a regular PostgreSQL table. A superuser can UPDATE or DELETE rows in the history table.
- There is no hash chain — tampering with a historical row is undetectable unless separately hashed.
- temporal_tables records state transitions at the row level, not business events. It cannot record "who approved what and why" — only "what the row looked like before and after."

**Verdict on temporal_tables for Solvency II compliance:** Useful as a supplementary data integrity mechanism for the operational store. Not a substitute for the structured audit event log. Recommend implementing on key tables (contracts, reconciliation_cycles, eligibility_results) alongside the audit ledger.

**5c. WAL + Logical Replication to S3**

The WAL (Write-Ahead Log) is PostgreSQL's internal append-only change log. Logical replication decodes WAL changes and can stream them to a consumer. AWS DMS or pglogical can stream decoded changes to S3.

This is a genuinely interesting option that deserves careful analysis.

**What WAL-to-S3 replication provides:**
- Every INSERT, UPDATE, DELETE on any table is captured in the WAL before it is applied.
- The WAL is append-only during normal operation — PostgreSQL does not retroactively alter WAL entries.
- If WAL changes are streamed to S3 in near-real-time, an attacker who modifies the database after the fact has already had the original state captured in S3.

**The attack surfaces:**
- A superuser who modifies a row *before* the WAL change is replicated to S3 cannot prevent the change from appearing in S3 (WAL is written synchronously before the transaction commits).
- However: a superuser who can modify the replication slot configuration, pause the replication stream, modify rows, and then resume replication gets a window where changes are not replicated. The WAL itself still exists in the primary's `pg_wal` directory — but if the replication slot is dropped and recreated after the modification, the gap may not be detectable.
- AWS DMS replication gaps are logged in CloudTrail. A gap in the replication stream is detectable, but only if someone is monitoring for it.

**Is WAL-to-S3 equivalent to S3 Object Lock Compliance Mode?**

No. The difference is fundamental:

| Property | WAL-to-S3 | S3 Object Lock Compliance Mode |
|---|---|---|
| Immutability mechanism | Append-only WAL stream; S3 objects not locked | WORM at object level; no API can overwrite or delete within retention period |
| Superuser bypass | Yes — pause replication, modify row, resume | No — not even account root user |
| Detection if bypassed | Detectable via DMS gap monitoring (if alerting configured) | Not applicable — bypass is physically impossible |
| Regulatory claim | "Tamper-detectable with monitoring" | "Tamper-impossible by AWS infrastructure guarantee" |
| Audit evidence for regulator | Show DMS monitoring config and alert history | Show S3 Object Lock configuration — self-evident |

WAL-to-S3 replication is a strong *operational* control. It is not equivalent to S3 Object Lock Compliance Mode from a regulatory standpoint. A Solvency II auditor asking "can the platform operator alter records?" receives a different quality of answer: "we would detect it" vs. "it is impossible."

That said, WAL-to-S3 replication (via AWS DMS) is a useful *additional* layer that the current recommendation should consider: it captures all database changes (not just audit events) and provides a recovery path independent of Aurora backups.

**5d. pg_partman**

pg_partman manages partition lifecycle for audit tables. It is relevant to the 10-year retention requirement: partitioning the `audit.events` table by `created_at` (monthly or annual partitions) allows old partitions to be archived to S3 Glacier via a scheduled job without touching the current partition.

This is an operational convenience tool, not a security or compliance control. It does not affect the tamper-resistance analysis.

**Recommendation on pg_partman:** Implement. Partition `audit.events` by year. Annual partitions older than 3 years are exported to S3 Glacier and the partition detached. This is already implied by the OPEX table (AWS Backup + S3 Glacier) but the mechanism should be explicit.

---

## 5. Scoring

### Rubric

| Dimension | Weight |
|---|---|
| Fit for monthly-batch workload (not high-frequency) | 20% |
| Operational complexity for 6-person team | 20% |
| Audit trail strength (Solvency II Art. 259, tamper resistance) | 20% |
| Query flexibility (reporting, cycle history, counterparty views) | 15% |
| DR / data recovery story | 15% |
| Schema evolution over time | 10% |

### Scores

**Scale: 1 = poor / 5 = excellent**

#### Option 1: PostgreSQL + S3 Object Lock (Current Recommendation)

| Dimension | Score | Rationale |
|---|---|---|
| Fit for monthly batch | 5 | PostgreSQL is optimised for relational queries; S3 Object Lock adds no batch-processing friction; write pattern (one event per state transition) is trivially compatible with synchronous dual-write |
| Operational complexity | 4 | Dual-write adds one failure mode (S3-first pattern with async PG repair resolves it); no new infrastructure beyond S3 bucket config; the rest is standard RDS + application code |
| Audit trail strength | 5 | S3 Object Lock Compliance Mode is tamper-impossible; PostgreSQL hash chain provides fast query capability; together they deliver both the compliance answer and the operational query answer |
| Query flexibility | 5 | PostgreSQL is the query layer; standard SQL, full-text search, JSONB operators, date range queries — all supported natively |
| DR / data recovery | 4 | S3 Object Lock survives Aurora DR restore (S3 is independent); PostgreSQL index is rebuildable from S3 archive; Aurora Multi-AZ covers AZ failure; cross-region S3 replication for bucket DR |
| Schema evolution | 4 | JSONB payload in audit events absorbs schema changes without table DDL; new event types additive; audit table schema itself changes rarely |

**Weighted total:** (5×0.20) + (4×0.20) + (5×0.20) + (5×0.15) + (4×0.15) + (4×0.10) = 1.00 + 0.80 + 1.00 + 0.75 + 0.60 + 0.40 = **4.55**

#### Option 2: Full Event Sourcing

| Dimension | Score | Rationale |
|---|---|---|
| Fit for monthly batch | 3 | Append-only log is technically compatible with batch workloads but adds projection rebuild complexity; EventStoreDB's streaming model is designed for continuous event flows, not monthly batch cycles |
| Operational complexity | 1 | Projection management, event schema migration (upcasters), snapshot management, catch-up subscription coordination — all requiring specialist knowledge the 6-person team does not have |
| Audit trail strength | 5 | Event log replay is the strongest possible model; every historical state reconstructible; EventStoreDB append-only by design |
| Query flexibility | 2 | Queries require projections; ad-hoc queries against event log are expensive; reporting requires purpose-built read models; significant upfront projection design required |
| DR / data recovery | 4 | Event log is the single source of truth; any projection can be rebuilt from it; strong recovery story but requires full replay on DR |
| Schema evolution | 1 | Cannot change past events; every schema change requires versioned upcaster; the operational burden compounds over 10 years of Solvency II retention |

**Weighted total:** (3×0.20) + (1×0.20) + (5×0.20) + (2×0.15) + (4×0.15) + (1×0.10) = 0.60 + 0.20 + 1.00 + 0.30 + 0.60 + 0.10 = **2.80**

#### Option 3: CQRS-lite with Event Bus

| Dimension | Score | Rationale |
|---|---|---|
| Fit for monthly batch | 2 | Event bus (SQS/EventBridge) adds latency and operational overhead for a workload where synchronous write-through is perfectly adequate; no throughput benefit at this scale |
| Operational complexity | 2 | Event bus, projection updater, eventual consistency boundary management, DLQ handling — four new operational concerns for no meaningful benefit at this scale |
| Audit trail strength | 2 | SQS messages are transient; EventBridge events are transient; without a durable event archive, the read model is the only record, and it is mutable |
| Query flexibility | 4 | Read models can be optimised for specific query patterns; but at this scale PostgreSQL serves all query patterns adequately without separate projections |
| DR / data recovery | 2 | If read models are the only durable store and events are transient, DR requires rebuilding projections from... what? Requires a durable event archive to be useful, at which point it converges to Option 1 |
| Schema evolution | 3 | Events can evolve independently of read models; but event schema versioning is still required |

**Weighted total:** (2×0.20) + (2×0.20) + (2×0.20) + (4×0.15) + (2×0.15) + (3×0.10) = 0.40 + 0.40 + 0.40 + 0.60 + 0.30 + 0.30 = **2.40**

#### Option 4: PostgreSQL Outbox Pattern (No S3)

| Dimension | Score | Rationale |
|---|---|---|
| Fit for monthly batch | 5 | Everything in one database; synchronous writes; no external dependencies; perfectly matched to batch workload |
| Operational complexity | 5 | Simplest possible model; outbox worker is a standard background job; no new infrastructure |
| Audit trail strength | 2 | Hash chain is detectable-but-not-impossible (superuser can recompute chain consistently, bypassing weekly sweep); no independent immutable record; insufficient for the stronger Solvency II compliance position |
| Query flexibility | 5 | Full PostgreSQL query capability; no read model management |
| DR / data recovery | 3 | Single database is a single point of failure for the audit trail; Aurora PITR restore can lose recent audit events; no independent copy |
| Schema evolution | 4 | Standard PostgreSQL migration tooling; JSONB payload absorbs most changes |

**Weighted total:** (5×0.20) + (5×0.20) + (2×0.20) + (5×0.15) + (3×0.15) + (4×0.10) = 1.00 + 1.00 + 0.40 + 0.75 + 0.45 + 0.40 = **4.00**

#### Option 5: PostgreSQL with Extensions (No S3)

*Assessed as the best realistic PostgreSQL-only configuration: pgaudit + temporal_tables + WAL-to-S3 via DMS + pg_partman. Note: WAL-to-S3 uses S3 standard storage, not Object Lock.*

| Dimension | Score | Rationale |
|---|---|---|
| Fit for monthly batch | 5 | All extensions are passive additions to the PostgreSQL operational model; no write-path changes required |
| Operational complexity | 3 | temporal_tables triggers add trigger maintenance overhead; DMS replication slot requires monitoring; pg_partman adds scheduled maintenance jobs; more moving parts than Option 4 but fewer than Option 1 |
| Audit trail strength | 3 | WAL-to-S3 captures all changes before they are applied; gap in replication stream is detectable; but not equivalent to Object Lock (replication can be paused by a superuser with appropriate IAM permissions); temporal_tables adds row versioning but history rows are mutable |
| Query flexibility | 4 | temporal_tables enables as-of queries natively; pg_partman supports efficient range queries on large audit tables; standard SQL throughout |
| DR / data recovery | 3 | WAL-to-S3 provides an independent change log; but it is a change log, not a structured business event archive — rebuilding application state from WAL requires a WAL decoder, which is significantly more complex than rebuilding from structured event JSON |
| Schema evolution | 3 | WAL schema (column names, types) is tightly coupled to the PostgreSQL schema; a table schema change generates WAL in the new format immediately, breaking any WAL consumer that expects the old format |

**Weighted total:** (5×0.20) + (3×0.20) + (3×0.20) + (4×0.15) + (3×0.15) + (3×0.10) = 1.00 + 0.60 + 0.60 + 0.60 + 0.45 + 0.30 = **3.55**

---

## 6. Summary Scorecard

| Option | Batch Fit (20%) | Ops Complexity (20%) | Audit Strength (20%) | Query Flexibility (15%) | DR / Recovery (15%) | Schema Evolution (10%) | **Weighted Total** |
|---|---|---|---|---|---|---|---|
| 1: PostgreSQL + S3 Object Lock | 5 | 4 | 5 | 5 | 4 | 4 | **4.55** |
| 2: Full Event Sourcing | 3 | 1 | 5 | 2 | 4 | 1 | **2.80** |
| 3: CQRS-lite / Event Bus | 2 | 2 | 2 | 4 | 2 | 3 | **2.40** |
| 4: PostgreSQL Outbox (no S3) | 5 | 5 | 2 | 5 | 3 | 4 | **4.00** |
| 5: PostgreSQL + Extensions (no Object Lock) | 5 | 3 | 3 | 4 | 3 | 3 | **3.55** |

---

## 7. Recommendation

### Winner: Option 1 — PostgreSQL + S3 Object Lock

Option 1 wins on a weighted basis by a meaningful margin (4.55 vs 4.00 for the nearest alternative). More importantly, it is the only option that answers "tamper-impossible" to a Solvency II auditor without qualification.

The rationale is not that S3 Object Lock is conceptually superior to a hash chain — it is that S3 Object Lock is *independent of the operational team's privileges*. The hash chain in PostgreSQL is a strong deterrent against casual tampering and an excellent operational query tool. But it relies on the KMS genesis anchor and the weekly verification Lambda being intact. S3 Object Lock Compliance Mode relies on AWS infrastructure guarantees that no customer IAM principal can override. These are qualitatively different assurances.

**Fit with the modular monolith + ECS Fargate decision:** This is the best fit. The audit service is a synchronous call from the application service (ECS Fargate task). No event bus, no projection management, no new infrastructure other than an S3 bucket with Object Lock configuration. The application writes to S3 first, then writes to PostgreSQL. Both are synchronous calls within the request cycle. This is standard application code, not distributed systems engineering.

**The dual-write pattern, prescribed explicitly:**

The architecture review identified the dual-write consistency gap. The resolution:
- S3 is always written first. The S3 key and ETag are stored in the PostgreSQL audit row.
- PostgreSQL index write failure is non-fatal: a background reconciliation job (run nightly) compares S3 event objects (listed by tenant prefix) against PostgreSQL index rows and re-inserts any missing rows.
- S3 write failure is fatal for the request: the calling transaction rolls back and the client receives a retryable error.
- The PostgreSQL hash chain is always built from confirmed S3-written events. A row with no `s3_key` is invalid by schema constraint.

### Under What Conditions Would You Pick a Different Option?

**Option 4 (PostgreSQL Outbox) — if the regulatory position changes:**
If legal counsel advises that "tamper-detectable within 7 days" is sufficient for Solvency II Art. 259 in your specific jurisdiction and regulatory engagement, Option 4 is operationally simpler and eliminates S3 Object Lock entirely. The hash chain provides tamper detection that is *practically* strong for unsophisticated tampering. The simplification saves ~$5/month OPEX and removes the S3-first write pattern complexity. This is only worth considering if you have explicit regulatory guidance, not as an assumption.

**Option 5 (PostgreSQL + Extensions) — if you want a stronger operational audit supplement:**
Implement temporal_tables on the operational store (`contracts`, `reconciliation_cycles`, `eligibility_results`) regardless of which audit option you choose. This is a no-cost addition that enables as-of queries on operational data. WAL-to-S3 via AWS DMS is worth adding as a *supplementary* layer (independent change capture, useful for debugging and DR) but should not replace S3 Object Lock. Use Option 5's extensions as additions to Option 1, not as replacements.

**Option 2 (Full Event Sourcing) — never for this system as currently scoped:**
The scale does not justify it. If the platform grows to 200+ counterparties and real-time notification of downstream systems becomes a requirement, revisit. At that scale, an event bus (EventBridge) with durable event archive is worth the investment. At 15–20 counterparties, it is not.

**Option 3 (CQRS-lite) — only if reporting queries become expensive:**
If the operational PostgreSQL database begins to show query contention between the approval workflow writes and compliance reporting reads (unlikely at this scale but possible after 5 years of data), a separate read replica with dedicated reporting projections is a legitimate response. This is a scale-driven decision, not an initial architecture choice.

### Immediate Actions for the Current Design

Three specific gaps in the existing solution design need addressing regardless of which option is chosen:

1. **Prescribe the S3-first dual-write pattern explicitly.** The current design describes the audit ledger as a PostgreSQL schema with S3 backup, but does not specify the write ordering or the failure recovery path. Add an ADR or an operational runbook section covering: S3-first, ETag stored in PG row, background reconciliation job for PG index repair.

2. **Add temporal_tables to the operational store schema.** The current data model does not include row versioning on `contracts`, `reconciliation_cycles`, or `eligibility_results`. These are the three tables where historical state reconstruction is most likely to be requested during a regulatory audit. temporal_tables adds this capability at zero operational cost.

3. **Extend the verification Lambda to handle multi-version KMS signatures.** The genesis anchor verification currently assumes the CMK is at a single version. After any KMS key rotation (manual or automatic), genesis anchors provisioned before the rotation must be verified against the prior key version. AWS KMS retains old key versions; the Lambda must pass the explicit key version ID when calling `Verify`, not rely on the default (current) version.

---

## 8. The Scale Argument — Final Statement

Every event-driven architecture pattern in this analysis — event sourcing, CQRS, pub/sub, outbox with downstream consumers — exists to solve a throughput and decoupling problem. This system does not have a throughput problem. It has a *correctness and compliance* problem: how do you create a tamper-evident record of structured business events that survives a motivated insider with database credentials?

The answer to that question is not an event bus. It is write-once storage with access controls that are independent of the operational team's privilege level. S3 Object Lock Compliance Mode is exactly that. PostgreSQL with a hash chain is a fast, queryable *index* over those records. Used together, with S3 as system of record and PostgreSQL as query layer, Option 1 is correct.

The PostgreSQL extensions (temporal_tables, pg_partman) are worth adding. WAL-to-S3 via DMS is worth adding as a supplementary layer. Full event sourcing and CQRS-lite are not appropriate for this domain, team size, or workload cadence.

---

*This document is an AI-assisted internal analysis and is not a client-facing deliverable.*
