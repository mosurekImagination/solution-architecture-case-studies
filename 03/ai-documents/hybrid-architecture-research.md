# Hybrid Architecture Research — Case 03: How Others Solved This

**Type:** AI-assisted architecture research  
**Author:** Tomasz Mosur  
**Date:** 2026-04-27  
**Subject:** Alternative databases, partial event sourcing, and industry patterns for financial audit + reconciliation

---

## The Real Problem Statement

Before reviewing alternatives, it is worth sharpening the question. The system has two structurally different concerns:

1. **Configuration state** — contracts, counterparties, users, file type definitions. This data is relatively stable, rarely changes, and benefits from standard relational query patterns. Nobody needs to audit every field change on a contract with sub-second latency.

2. **Cycle lifecycle state** — what happened during a reconciliation cycle, in what order, who approved what, when, and what was the financial outcome. This data is audit-critical, legally sensitive, and must be immutable once sealed.

The current Option 2 design treats both concerns with the same architecture (relational tables + bolt-on audit log). Most of the complexity — dual-write, hash-chain maintenance, snapshot-based adjustments — comes from forcing concern #2 into a model designed for concern #1.

Almost every financial platform that has solved this problem well solved it by using different models for these two concerns.

---

## How Financial Companies Actually Solved This

### Stripe — Idempotent Append-Only Ledger for Financial Events

Stripe does not use event sourcing in the academic sense. Their core insight is simpler: **financial records are ledger entries, not mutable rows**. A payment is not a record with a `status` field that transitions from `pending` to `completed`. It is a series of ledger entries: `payment.created`, `payment.captured`, `payment.settled`. The ledger is append-only. The balance at any point is the sum of entries up to that point.

For non-financial data (merchant profiles, pricing rules, API keys), they use conventional CRUD.

The pattern is called the **double-entry bookkeeping ledger**. It is 700 years old. It is what their payments-at-scale architecture is built on.

**Relevance here:** Eligibility results, compensation amounts, and adjustments are financial facts. They should be ledger entries, not mutable rows. The reconciliation cycle state machine — which file arrived when, who approved what — is the audit trail for those financial facts.

---

### Monzo — Event Sourcing for One Aggregate, CRUD for the Rest

Monzo's engineering blog documents their approach explicitly: they use event sourcing for the **account aggregate** (balance, transaction history, holds) because immutability is the core requirement there. For everything else — customer profiles, KYC records, product configuration — they use PostgreSQL with conventional patterns.

The key lesson: **event sourcing should be applied to the aggregate where immutability is the primary requirement, not to the entire system.** Applying it everywhere creates unjustified projection overhead for data that does not need it.

**Relevance here:** The reconciliation cycle is the equivalent of Monzo's account aggregate. It is the bounded context where events matter. Counterparty profiles and contract definitions are the equivalent of customer profiles — CRUD is fine.

---

### ING Bank — Axon Framework: Selective Event Sourcing in Practice

ING Bank's core banking modernisation used the Axon Framework (Java/JVM) with event sourcing applied selectively to financial aggregates. Their published finding: applying event sourcing to 15-20% of their domain model (the financial transactions, the account lifecycle) accounted for 80% of the audit and compliance value. The remaining 80% of the domain (product catalogue, customer data, pricing) used conventional JPA/relational patterns with no meaningful loss.

The Axon team's reported observation across 200+ enterprise implementations: the most common mistake is applying event sourcing to entities that change infrequently (configuration, master data) where the projection overhead is unjustified.

**Relevance here:** For this system, the reconciliation cycle aggregate is the 15-20% that delivers 80% of the audit value.

---

### Goldman Sachs / kdb+ — Purpose-Built Temporal Database for Financial Time Series

At the extreme end, Goldman Sachs and many hedge funds use **kdb+** (from Kx Systems) as their financial data store — a column-oriented, time-series database where every record is timestamped and the data model is inherently append-only. Queries are temporal by default: "what was the position in this contract at 14:32:05 on settlement date?"

This is over-engineered for a reinsurance reconciliation platform. Monthly cycles do not require microsecond temporal resolution. But the underlying insight is important: **purpose-built temporal databases eliminate the need to engineer immutability as a secondary concern** because immutability is their default behaviour.

---

### Revolut — PostgreSQL + Append-Only Tables (No External Event Store)

Revolut's early architecture (well-documented in engineering blog posts) used PostgreSQL exclusively but with a strict schema convention: financial transaction tables are **never updated**. The application layer enforces this by only calling `INSERT` on transaction tables, never `UPDATE` or `DELETE`. RLS policies block mutations at the database layer. A separate `transactions` table serves as the ledger; account balance is always computed from it.

The innovation: they did not use an event store, Kafka, or a specialised database. They used PostgreSQL with **application-layer discipline enforced by database constraints**. Any attempt to UPDATE a transaction row fails at the database level, not the application level.

**Relevance here:** This is the lightest-weight approach to immutability that is production-proven at financial scale. It does not require event sourcing, a separate audit log, or dual-write. It requires schema discipline.

---

### Grab Financial Services — CDC as the Audit Layer

Grab (Southeast Asia's super-app) uses **Change Data Capture (CDC)** via Debezium to capture all database mutations as events without changing application code. The application writes to PostgreSQL in the conventional way. Debezium reads the PostgreSQL Write-Ahead Log (WAL) and publishes every INSERT, UPDATE, and DELETE as a structured event to Kafka. The Kafka topic is the immutable audit archive.

The elegance: **the application does not know about the audit layer**. No dual-write. No event publishing code in the application. The database WAL is the source of events. Debezium is infrastructure, not application logic.

For Grab's financial reconciliation, the CDC stream feeds a compliance read store (Elasticsearch or S3 Parquet) that is query-optimised for audit investigations. The production PostgreSQL is never queried for historical reconstructions.

**Relevance here:** This is directly applicable. The Option 2 design's dual-write problem disappears if audit events are derived from the WAL rather than written by application code.

---

## Database Alternatives Worth Considering

### Option A — EventStoreDB (Purpose-Built Event Store)

EventStoreDB is an open-source database built specifically for event sourcing. Streams are append-only by design. Optimistic concurrency is built in. Persistent subscriptions allow projections to be rebuilt. It supports both HTTP and gRPC APIs.

**Strengths for this system:**
- Optimistic concurrency on streams out of the box (no custom version-check queries)
- Built-in stream subscriptions drive projection updates
- Native support for competing consumers (useful for parallel eligibility processing)
- Data is immutable at the storage layer, not enforced by application convention

**Weaknesses:**
- New infrastructure dependency (another service to operate, monitor, back up)
- Not AWS-managed; runs on EC2 or ECS — adds operational burden
- The team must learn EventStoreDB's projection system (JavaScript-based)
- For 10–30 counterparties at monthly cadence, EventStoreDB is operationally heavy for the scale

**Verdict:** Technically sound but operationally over-engineered for a 10–30 counterparty system. Would reconsider if the platform scales to 200+ counterparties or moves toward real-time processing.

---

### Option B — Datomic (Immutable Database, Value-Based Model)

Datomic, designed by Rich Hickey (creator of Clojure), stores facts as immutable datoms: `[entity, attribute, value, transaction-time]`. The database never deletes or updates — it only asserts new facts. Time-travel queries ("what did the database look like at time T?") are first-class operations. The entire history of any entity is always available.

Datomic is used in production at Nubank (Latin America's largest neobank), Walmart Labs, and several financial analytics firms.

**Strengths:**
- Immutability at the data model level — not at the application level
- Time-travel queries built into the query language (Datalog)
- No schema migration for new attributes — just assert new facts
- The entire audit requirement is satisfied by the data model itself

**Weaknesses:**
- Clojure/JVM ecosystem; requires Clojure or Java team
- Not AWS-managed; Datomic Cloud runs on DynamoDB + Lambda + S3 (Cognitect/Nubank controls it)
- Datalog is unfamiliar to most backend developers
- Expensive at scale (Datomic Pro licence)
- No SQL interface; existing tooling (reporting, compliance exports) must use Datalog or REST

**Verdict:** Philosophically the most aligned database to this domain. Practically, the ecosystem dependency is too constraining for a 6-person team on a 9.5-month delivery window. Worth noting as the ideal model for a greenfield reinsurance data platform with a larger team.

---

### Option C — CockroachDB with AS OF SYSTEM TIME

CockroachDB is a distributed SQL database with built-in temporal query support. The `AS OF SYSTEM TIME` clause returns the state of any query as it was at a given timestamp — for up to 25 hours by default (configurable to days/weeks). It also supports `SHOW JOBS` for audit of DDL changes.

**Strengths:**
- Standard SQL; no new query language
- Built-in temporal queries without temporal table engineering
- Distributes naturally for future multi-region data residency requirements
- Strongly consistent (serialisable isolation by default)

**Weaknesses:**
- Temporal history is a garbage-collected window (25 hours default), not infinite retention
- Unlimited temporal retention requires custom change data capture on top
- Distributed SQL adds latency vs. single-node PostgreSQL for a single-region system
- Higher operational complexity than RDS PostgreSQL
- Overkill for 10–30 counterparties in a single AWS region

**Verdict:** Interesting for multi-region data residency scenarios. Not justified at current scale for temporal query alone when PostgreSQL temporal tables achieve the same for stable entities.

---

### Option D — PostgreSQL with Temporal Tables (SQL:2011)

PostgreSQL 16+ supports temporal table syntax natively (via `GENERATED ALWAYS AS ROW START/END`). Earlier versions achieve the same via `valid_from` / `valid_to` columns and trigger-managed history tables.

**Strengths:**
- No new infrastructure
- Standard SQL for time-travel queries
- Directly applicable to the contract entity (the design already mentions temporal tables for contracts)
- Supported by most PostgreSQL ORMs

**Weaknesses:**
- Temporal tables track *who changed what, when* — they are a change history mechanism, not an immutable event log
- A malicious administrator can still UPDATE a temporal table's history rows if RLS is not properly configured
- Not sufficient alone for the reconciliation cycle audit requirement

**Verdict:** Correct choice for the contract entity (already in the design) and for counterparty configuration. Not sufficient for the reconciliation cycle audit trail. Should be combined with another approach for cycle lifecycle events.

---

## The Clever Middle Ground: Selective Event Sourcing

Based on how Monzo, ING, and Stripe approached this, the most elegant architecture for this specific system applies different models to different parts of the domain:

```
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL (single RDS instance)      │
│                                                         │
│  ┌─────────────────────┐   ┌──────────────────────────┐ │
│  │  CRUD Zone          │   │  Event Log Zone          │ │
│  │  (stable config)    │   │  (cycle lifecycle)       │ │
│  │                     │   │                          │ │
│  │  tenants            │   │  cycle_events            │ │
│  │  counterparties     │   │  ├── stream_id (cycle)   │ │
│  │  contracts          │   │  ├── version (seq)       │ │
│  │  contract_versions  │   │  ├── event_type          │ │
│  │  users              │   │  ├── payload JSONB        │ │
│  │  file_type_defs     │   │  ├── occurred_at         │ │
│  │                     │   │  └── actor_id            │ │
│  │  (temporal tables   │   │                          │ │
│  │   for contracts)    │   │  INSERT only — RLS       │ │
│  │                     │   │  blocks UPDATE/DELETE    │ │
│  └─────────────────────┘   └──────────────────────────┘ │
│                                    │                    │
│                         ┌──────────▼──────────┐        │
│                         │  Materialized Views  │        │
│                         │  (cycle state,       │        │
│                         │   approvals, files)  │        │
│                         └─────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### The Revolut Constraint: RLS Blocks Mutations on `cycle_events`

```sql
-- No UPDATE or DELETE ever reaches cycle_events
CREATE POLICY cycle_events_insert_only ON cycle_events
  AS RESTRICTIVE
  FOR ALL
  USING (false);  -- blocks SELECT without tenant filter

CREATE POLICY cycle_events_tenant_insert ON cycle_events
  AS PERMISSIVE
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

The application can only INSERT into `cycle_events`. Any attempt to UPDATE or DELETE fails at the database layer. No application convention to enforce — the database enforces it. This is the Revolut pattern applied to one table.

### What Goes in `cycle_events`

Approximately 12 event types for the entire cycle lifecycle:

```
FilesRequested
FileSubmitted          (by counterparty)
FileRejected           (validation failure)
FileNormalisationCompleted
EligibilityStarted
EligibilityCompleted   (with results hash)
ReviewStarted          (reinsurer L1)
AdjustmentProposed     (reinsurer to counterparty)
AdjustmentAccepted
AdjustmentRejected
CounterpartySigned
CycleSealed            (with final hash, triggers receipt generation)
```

### What Stays as CRUD

Contracts, counterparties, users, and configuration stay in standard relational tables with temporal versioning for the contract entity. No events, no projections. The only immutable zone is `cycle_events`.

### Projections as Materialized Views

The cycle state machine becomes a PostgreSQL function that derives state from the event log:

```sql
-- Refresh on every new event via trigger
CREATE MATERIALIZED VIEW cycle_state AS
SELECT
  stream_id                                         AS cycle_id,
  MAX(version)                                      AS latest_version,
  (array_agg(event_type ORDER BY version DESC))[1]  AS current_state,
  MAX(occurred_at)                                  AS last_event_at
FROM cycle_events
GROUP BY stream_id;
```

Six materialized views cover all portal query needs. Each refreshes on INSERT into `cycle_events` via a trigger. Refresh is fast (append-only table, incremental materialized view refresh available in PostgreSQL 16).

### The Grab Pattern: CDC to S3 for Compliance Archive

Debezium (running as a Fargate sidecar or as MSK Connect) captures the `cycle_events` WAL stream and publishes to S3 as Parquet files. The compliance read store for regulatory investigations is S3 Athena — not PostgreSQL. This:

- Removes the S3 Object Lock from the hot path (no dual-write)
- Provides the 10-year Solvency II retention in S3 at near-zero cost (Glacier)
- Enables SQL-based compliance queries against 10 years of cycle events without touching production PostgreSQL
- The CDC stream is the audit archive, not a secondary concern

### How This Solves the Trust Gap

At `CycleSealed`:
1. Application inserts the `CycleSealed` event with the final eligibility result hash and the hash of all preceding events in the stream (chained hash)
2. A PostgreSQL trigger fires, calling a function that:
   - Computes a KMS-signed receipt (AWS Lambda or application layer)
   - Stores the receipt in S3 (non-Object-Lock bucket; the event log is the authoritative record)
   - Emails the signed receipt to the counterparty (via SES)
3. The counterparty receives a receipt they can verify independently

The signed receipt contains:
```json
{
  "cycle_id": "...",
  "tenant_id": "...",
  "sealed_at": "2025-11-30T23:59:59Z",
  "file_hashes": { "lives_data": "sha256:...", "schedule_data": "sha256:..." },
  "event_chain_hash": "sha256:...",
  "signature": "KMS-RSA-PSS:..."
}
```

---

## Comparison: Five Approaches Against Requirements

| Approach | Audit Strength | Operational Complexity | Team Learning Curve | Scales to 200+ CPs | Eliminates Dual-Write |
|---|---|---|---|---|---|
| Current Option 2 (dual-write) | Medium (two representations) | High | Low | Partial | No |
| Full event sourcing (all aggregates) | High | High | High | Yes | Yes |
| **Selective ES (cycle only) + CDC** | **High** | **Low–Medium** | **Low** | **Yes** | **Yes** |
| Revolut append-only tables only | Medium-High | Low | Low | Yes | Yes (partial) |
| Datomic | Very High | High | Very High | Yes | Yes |
| EventStoreDB | High | Medium | Medium | Yes | Yes |

---

## Recommendation

**Apply selective event sourcing to the reconciliation cycle aggregate only, using PostgreSQL as the sole database, with Debezium CDC as the compliance archive.**

This is the ING/Monzo pattern applied to the minimum viable domain. It:

1. **Keeps PostgreSQL as the only database** — no new infrastructure
2. **Makes `cycle_events` the single source of truth for cycle lifecycle** — one table, append-only, RLS-enforced
3. **Keeps all configuration data as CRUD** — contracts, counterparties, users — with temporal tables for contracts
4. **Derives cycle state via materialized views** — six views cover all query needs, refreshed on INSERT
5. **Uses Debezium CDC to stream `cycle_events` to S3** — the compliance archive is async, zero dual-write risk
6. **Generates KMS-signed receipts at `CycleSealed`** — closes the trust gap without blockchain
7. **Eliminates ADR-008** (adjustments as events, not snapshots)
8. **Eliminates S3 Object Lock from the hot path** (CDC-derived archive handles retention)
9. **Reduces OPEX** (removes AWS Transfer Family baseline; Debezium runs on existing ECS)

The learning curve is limited to one aggregate and one table. The team writes INSERT statements, not a full event sourcing framework. The Revolut constraint (RLS blocks mutations) enforces immutability at the database layer. The Grab pattern (CDC to S3) provides the 10-year archive without application-layer dual-write.

This is, I believe, the most elegant architecture for this specific domain: a 700-year-old ledger pattern, enforced by a 30-year-old database, with a receipt signed by a managed key service, distributed to counterparties by email. Simple primitives, deep trust.
