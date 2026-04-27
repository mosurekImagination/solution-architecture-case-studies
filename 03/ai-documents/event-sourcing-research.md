# Event Sourcing Research — Case 03: Would It Simplify or Complicate?

**Type:** AI-assisted architecture research  
**Author:** Tomasz Mosur  
**Date:** 2026-04-27  
**Subject:** Focused analysis of whether event sourcing simplifies or complicates the Option 2 design

---

## The Precise Question

The architecture challenge document raised the possibility of promoting the `audit.events` table to the primary write target and deriving application state from it — "event log as source of truth without CQRS overhead." This report investigates whether that change would simplify or complicate the design, grounded in the specific constraints of this system.

This is not a general assessment of event sourcing. The domain context matters: 10–30 counterparties, monthly reconciliation cycles, bounded event sequences, a paramount audit requirement, and a 6-person delivery team with a 9.5-month window.

---

## What Event Sourcing Actually Means Here

Full CQRS/ES (separate read models, event bus, projectors as separate services) is not what is being considered. The proposal is narrower:

**Current model (Option 2):**
- Application state lives in relational tables (`reconciliation_cycles`, `approval_steps`, `eligibility_results`, etc.)
- Every state change is *also* written to `audit.events` (dual-write)
- The audit ledger is a secondary representation maintained in sync with primary state

**Proposed model:**
- Application state is derived *from* `audit.events` via PostgreSQL materialized views or lightweight projections
- `audit.events` is the only write target; all other state is read-only derived
- One place to write, multiple ways to query

The question is whether the proposed model reduces or increases total complexity for this specific system.

---

## Where Event Sourcing Simplifies

### 1. Eliminates the Dual-Write Atomicity Problem

This is the most concrete simplification. The current design writes application state AND audit events in a single transaction. In theory this is safe; in practice it means every state-changing operation carries two writes that must remain consistent. If they ever diverge (bug, partial failure during deployment, schema migration), the audit ledger and the application state tell different stories. Debugging that divergence during a regulatory audit is expensive.

With event sourcing, there is no divergence to manage. There is one write (the event). Application state tables do not exist as first-class entities — they are projections that can be rebuilt from the event log at any time. If a projection is wrong, you drop it and replay. You cannot have an "audit ledger out of sync with application state" problem because there is no separate application state.

**Verdict: material simplification.**

### 2. Adjustment Handling Becomes Trivial

The current design has an entire ADR (ADR-008) dedicated to snapshot-based adjustments and explicitly acknowledges that delta-based adjustments were considered and rejected. The complexity exists because the application state must be updated retroactively: an adjustment to Cycle N affects the current state of the `reconciliation_cycles` table.

With event sourcing, an adjustment is an `AdjustmentRecorded` event appended to the log. There is no retroactive update. The projection for a cycle's current state is defined as "replay all events for this cycle, in order." An adjustment naturally flows into the projection. ADR-008 becomes unnecessary.

**Verdict: removes an entire architectural decision problem.**

### 3. Audit Trail Is Intrinsic, Not Engineered

The current design engineers a tamper-evident audit trail on top of a mutable relational model. S3 Object Lock, hash-chains, weekly verification jobs, dual-write — all of these exist because the primary data model is mutable and the audit requirement demands immutability. This is architecturally awkward: you are fighting the primary model to bolt on a property it was not designed to have.

Event sourcing has immutability as its core invariant. The append-only log is not a secondary audit mechanism — it is the system. Regulatory auditors asking "what happened to Cycle 42 for Counterparty X" get the raw event log, in order, with timestamps, user IDs, and hashes. There is nothing else to show them because there is nothing else.

**Verdict: aligns architecture with the primary business requirement instead of layering it on top.**

### 4. Temporal Queries Are Free

"What was the eligibility result for individual 12345 under contract C at the end of Cycle 7?" is a temporal query. The current design handles this via temporal tables on the contract entity and careful versioning logic — but the design only applies temporal tables to contracts, not to all entities. For eligibility results and approval history, the audit ledger is the only temporal record.

With event sourcing, any point-in-time state is obtained by replaying events up to a given timestamp. This is not an optimised query pattern, but for a compliance investigation (not a real-time operation) it is adequate and requires no special schema engineering.

**Verdict: removes a class of schema complexity.**

### 5. Cycle Sealing Becomes a Natural Boundary

The current design defines a "Cycle_Sealed" terminal state. Sealing involves writing to the audit ledger, locking the hash-chain entry, and updating application state tables. These are three coordinated operations.

With event sourcing, sealing is a single `CycleSealed` event. The event is immutable by definition. No separate locking operation. The signed counterparty receipt (recommended in the architecture challenge document) is generated from this single event's hash. Clean, atomic, auditable.

**Verdict: simplifies the most compliance-critical operation.**

---

## Where Event Sourcing Complicates

### 1. Projection Maintenance

Every query that needs current state — "which cycles are currently in Adjustment_Loop?", "how many files has Counterparty X submitted this month?" — requires a projection. In the current design, this is a SQL query against a relational table. With event sourcing, it requires a maintained materialized view or in-memory projection built from the event log.

For this specific system, count the projections needed:
- `cycle_state_projection` — current state of each reconciliation cycle (state machine position, phase, counterparty)
- `file_ingestion_projection` — which files have been received, their status, record counts
- `eligibility_results_projection` — latest eligibility outcome per cycle
- `approval_workflow_projection` — current approval step, who has acted, who is pending
- `counterparty_dashboard_projection` — summary view for counterparty portal
- `compliance_summary_projection` — regulatory reporting aggregates

Six projections. In PostgreSQL this means six materialized views with refresh triggers on the `audit.events` table, or an incremental projection update mechanism.

**Verdict: adds 6 projection artefacts that do not exist in the current design. Non-trivial but bounded.**

### 2. Event Schema Evolution Is Harder Than Table Migration

In a relational model, changing what data is stored on an eligibility result requires a single `ALTER TABLE`. In an event-sourced model, the `EligibilityCompleted` event format is frozen once events exist in the log. Adding a field to old events requires either: (a) an "upcaster" that transforms old event shapes to the new shape at read time, or (b) a new event version (`EligibilityCompleted_v2`) with dual-handling code for old events.

Over a 9.5-month build with evolving requirements, this happens more than once. Teams that do not plan for event versioning from day one accumulate upcasters rapidly.

**Verdict: genuine operational complexity that does not exist in the current design. Must be addressed by design, not discovered.**

### 3. Read Performance for Complex Projections Under Load

At month-end, with 20–30 counterparties running eligibility concurrently, the portal needs to render current cycle state for 20–30 cycles. If projections are derived on-demand by replaying events, and each cycle has 50+ events, this is 1,000+ event reads per page load. Unacceptable.

The standard mitigation is snapshot tables: periodically persist the projected state so replay starts from the snapshot rather than the beginning. This adds another artefact to maintain (snapshot tables, snapshot schedules, snapshot invalidation on new events).

For this system, month-end cycles are bounded in event count and run for 3–5 days. A snapshot after each major state transition (EligibilityCompleted, ReviewStarted) would keep replay costs low. But this must be designed in.

**Verdict: requires snapshot strategy to be designed upfront. Adds complexity but is well-understood.**

### 4. Developer Cognitive Overhead

Most developers are trained to think in terms of current state: "read the record, update the field, save." Event sourcing requires thinking in terms of past events: "what events led to the current state, and what event should I append to transition it?" This is a different mental model that takes time to internalise.

For a 6-person team over 9.5 months, with at least some developers likely unfamiliar with event sourcing, the first 4–6 weeks will be slower than an equivalent CRUD implementation. The speed difference closes as the team builds familiarity, but Phase 1 delivery is most at risk.

**Verdict: real team velocity risk in Phase 1. Mitigable but not eliminable.**

### 5. Tooling Overhead

PostgreSQL is not a native event store. Using it as one requires:
- An append-only `audit.events` table with a schema that handles polymorphic event payloads (typically JSONB `payload` column with `event_type` discriminator)
- An optimistic concurrency mechanism (stream version check on insert to prevent concurrent writes to the same cycle)
- A projection rebuild mechanism (truncate and replay for full rebuilds, incremental update for live projections)
- A versioning convention for event types

None of this is off-the-shelf. It is hand-rolled infrastructure. Axon, EventStoreDB, or Marten (.NET) provide this — but introducing a new infrastructure dependency was not in the Option 2 design. Using raw PostgreSQL means building it.

**Verdict: 1–2 sprint investment in event store infrastructure before any business logic can be written.**

---

## Domain Factors That Tip the Balance

The complications above are real. Whether they outweigh the simplifications depends on domain-specific factors. For this system:

| Factor | Impact on Decision |
|---|---|
| **Monthly cadence — not high-frequency** | Event count per cycle is bounded (~20–80 events). Replay is cheap. Snapshot complexity is low. |
| **Audit is the primary requirement, not a secondary concern** | Event sourcing achieves the audit requirement intrinsically. The current design engineers it expensively on top. |
| **Small event type vocabulary** | The domain produces ~12 distinct event types. Schema evolution risk is lower than in complex domains. |
| **Regulatory queries are retrospective, not real-time** | Temporal replay queries are acceptable for compliance use cases. They do not need sub-second performance. |
| **Adjustment handling is a core feature** | Event sourcing eliminates the most complex ADR in the current design (ADR-008). |
| **9.5-month delivery window** | Projection maintenance and event versioning overhead could compress Phase 1. Risk is real. |
| **6-person team, unknown ES experience** | Cognitive overhead is the most controllable risk. A one-week Investigation Period spike determines actual team readiness. |

---

## The Architectural Trap to Avoid

The worst outcome is not choosing event sourcing or not choosing it. The worst outcome is the current design: **maintaining both a mutable relational model AND an append-only audit log** and treating them as co-equal sources of truth. This is not event sourcing (the relational tables are the primary state) and it is not pure CRUD (the audit log must be kept in sync). It inherits the complexity of both models without the full benefits of either.

If the team is not ready for event sourcing, the correct Option 2 response is to **demote the audit ledger to a secondary, async, read-only archive** — not maintain it as a co-primary source of truth. The application state is in relational tables; the audit log is an asynchronous projection of those tables, written by database triggers or a CDC pipeline, not by application dual-write.

If the team is ready for event sourcing, the correct move is to **promote the audit log to the sole primary write target** and derive all other state from it.

The middle ground — dual-write with two co-primary sources of truth — is the architectural anti-pattern to avoid.

---

## Verdict

**Event sourcing would simplify this architecture, conditional on three requirements being met:**

| Condition | Why It Is Non-Negotiable |
|---|---|
| Event schema versioning strategy defined before Phase 1 starts | Without it, schema evolution creates upcaster debt within 3 months |
| Projections built as PostgreSQL materialized views (not in-memory) | In-memory projections are lost on restart; materialized views are queryable and rebuildable |
| One-week Investigation Period spike to validate team readiness | If the team has no ES experience, Phase 1 velocity risk is too high to absorb |

If all three conditions are met, event sourcing:
- Eliminates the dual-write atomicity problem (the most fragile part of Option 2)
- Makes the audit requirement intrinsic rather than engineered
- Removes ADR-008 (adjustment handling) as a design problem
- Provides a cleaner foundation for the Option 3 migration path referenced in the evolution roadmap

If any condition cannot be met — particularly team readiness — the correct fallback is **not** Option 2 as currently designed. The correct fallback is Option 2 with the audit log demoted to an async CDC-derived archive, eliminating the dual-write without requiring event sourcing discipline.

**The binary is not "event sourcing vs. current Option 2." It is "event sourcing vs. single-source-of-truth CRUD + async audit." The current dual-write design should not be the fallback position.**

---

## Recommended ADR

An ADR should be written and decided during the Investigation Period:

> **ADR-011: Primary Write Model — Event Log vs. Relational State**
>
> **Options:**
> - A: Event log primary, projections derived (event sourcing)
> - B: Relational tables primary, async CDC-derived audit archive
> - C: Dual-write (current design) — explicitly rejected as architectural anti-pattern
>
> **Decision gate:** One-week spike during Investigation Period. Team builds a single reconciliation cycle (file ingestion through cycle seal) in both models. Whichever model produces cleaner code and clearer audit semantics is adopted for Phase 1.
