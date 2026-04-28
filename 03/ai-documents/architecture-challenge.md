# Architecture Challenge — Reinsurance Reconciliation Platform

**Type:** AI-assisted architecture challenge
**Author:** Tomasz Mosur
**Date:** 2026-04-28
**Source document:** `03/docs/solution-design.adoc` (rev 1.0, 2026-04-16)

---

## Executive Summary

- The core trust architecture — selective event sourcing on the cycle aggregate, RLS-enforced `cycle_events`, and KMS-signed receipts at `CycleSealed` — is the right answer for this problem. The blockchain rejection is correct. The design is not overengineered.
- **Debezium CDC as the compliance archive is the highest-risk operational decision in the document.** A crashed replication slot fills PostgreSQL WAL storage and can bring down the primary database. The design mentions lag monitoring but does not address slot accumulation — the scenario that causes actual outages.
- **The expression tree evaluator is a bet on a discovery that hasn't happened yet.** UK longevity reinsurance contracts use age/gender-banded mortality tables and present-value annuity calculations — the initial node set (AND/OR/range/tiered/flat) is almost certainly insufficient. The fallback "constrained formula DSL" is referenced but not designed.
- The `DISPUTED` state is a dead end in the state machine with real compliance implications: a cycle that never reaches `CycleSealed` has no signed receipt, no sealed audit record, and no Solvency II-compliant closure.
- Two targeted changes — replacing Debezium with a simpler archive write and hardening the expression tree gate to 100% coverage before Phase 2 starts — would materially reduce delivery risk with negligible architectural downside.

---

## Critical Issues

### 1. Debezium CDC sidecar: WAL slot accumulation risk is unaddressed

The design runs Debezium as a sidecar in the ECS Fargate task and monitors CDC lag with a 5-minute alert. The problem is not lag — it is replication slot stale accumulation.

PostgreSQL holds WAL segments for every registered replication slot until that slot confirms consumption. If the Debezium sidecar crashes (container restart, deployment, network partition), the slot accumulates unconsumed WAL. On a `db.t4g.medium` with typical storage allocation, a stalled slot can fill the disk and crash the primary database within hours. This is a well-documented failure mode for Debezium in production.

The design does not describe:
- How the replication slot is monitored for slot lag (distinct from CDC processing lag)
- What happens during a zero-downtime deployment when the sidecar is briefly stopped
- How Debezium handles schema changes in `cycle_events` (column additions require Debezium schema registry or manual connector reconfiguration)
- The recovery procedure when the slot falls far behind

A 5-minute lag alert detects slow processing. It does not detect a stalled slot before storage fills.

**Simpler alternative within Option 2:** In the same transaction as the `cycle_events` INSERT, write to a `cycle_events_export` staging table. A scheduled job (cron, every 15 minutes) bulk-exports new rows to S3 Glacier as Parquet and deletes them from the staging table. No WAL slot. No Debezium connector. The compliance archive is 15 minutes behind the live event log — acceptable for a 10-year Solvency II archive.

### 2. Expression tree evaluator: gate condition is wrong and fallback is undefined

The Phase 1→2 gate says: if more than 20% of extracted contract types require node types beyond the initial set, escalate to a "constrained formula DSL."

This is the wrong gate in two ways.

First, the threshold is wrong. A 20% failure rate means Phase 2 is built with an engine that cannot handle one-in-five contracts. Those contracts need a second code path with divergent auditing, different testing, and separate contract-version semantics. The gate should be: all identified contract types are fully expressible in the initial node set, or Phase 2 does not start.

Second, the fallback is undefined. "Constrained formula DSL" is named but not designed. If the gate fails, the team must design a DSL from scratch mid-project, which adds months of scope and invalidates the Phase 2 timeline. The fallback needs to be designed in Phase 1, Week 1 — not after the gate result is known.

On the likelihood of gate failure: UK longevity reinsurance contracts regularly require mortality rate lookups (age × gender × health class tables), present-value annuity factor calculations, and in some cases portfolio-level aggregation across individuals. None of these fit the initial node set of AND/OR/range/tiered/flat. If the first three representative contracts are selected from the least-complex end of the book, the gate passes — but the engine fails on the first production contract that uses a mortality table.

The "complexity ceiling assessment" in Phase 1 needs to deliberately include the most complex contract types, not the most accessible ones.

### 3. Multi-tenancy: RLS session bleed is not covered by the described tests

The design correctly uses `SET LOCAL` for transaction-scoped tenant context and acknowledges the production failure mode where connection pool reuse exposes one tenant's data to the next request. The mitigation is an automated RLS penetration test on every deployment.

The test is not described. If it tests only the obvious scenario — authenticated user A cannot query authenticated user B's records — it misses the session bleed case entirely. Session bleed requires a test that:

1. Opens a database connection from the pool
2. Sets tenant context to Tenant A and reads data
3. Returns the connection to the pool without committing (or after a rollback)
4. Reacquires the same connection from the pool with no `SET LOCAL` call
5. Confirms that Tenant A's context is not visible on the recycled connection

Without this test, the protection depends entirely on the API framework reliably beginning an explicit transaction before every DB call — which is a framework guarantee, not an application test.

There is also no mention of whether read replicas (if added for compliance query offload) enforce the same RLS policies and tenant context protocol.

### 4. Adjustment chain: contract version applied to corrections is ambiguous

The design states: "contract version locked at cycle opening; mid-cycle changes apply to the next cycle only."

This policy covers the original cycle. It does not explicitly cover adjustment cycles. An adjustment is a cross-cycle correction: month N's liability is recalculated in month N+3 because an error was found. The design says the adjustment "triggers a full eligibility recalculation" and records `prior_cycle_id` and `root_cycle_id`. But it does not state which contract version governs the recalculation.

Two defensible answers exist: use the contract version that was active when the original cycle (month N) was opened, or use the contract version active when the adjustment cycle (month N+3) is opened. Either is auditable if documented. Neither is currently documented.

This gap surfaces in the `EligibilityCompleted` event payload, which must include the contract version for Solvency II Art. 259 reproducibility. For adjustments, the payload must also record which cycle's contract version was applied, not just which contract version is current.

### 5. `DISPUTED` state is a terminal dead end with no closure path

The state machine shows `DISPUTED` as reachable from `Reinsurer_Review`. No transitions out of `DISPUTED` are defined anywhere in the document.

A cycle in `DISPUTED` never reaches `CycleSealed`. That means:
- No KMS-signed receipt is delivered to the counterparty
- No `CycleSealed` event is appended to `cycle_events`
- The Debezium CDC archive (or any archive) has no sealed record for this cycle
- The cycle has no Solvency II-compliant closure record

For a reconciliation platform where compliance is the primary design requirement, an indefinitely open cycle with no defined resolution path is a material gap. Disputes in reinsurance are escalated to a legal/compliance process; the platform needs at minimum a `DisputeEscalated` event and a `DisputeResolved` transition that allows the cycle to reach a compliant terminal state (either sealed with adjustments, or formally written off with a documented reason).

### 6. Month-end eligibility concurrency: the 15-minute SLA has no mechanism

The NFR requires eligibility results within 15 minutes of file submission, with up to 20 concurrent submissions. The application runs as a modular monolith in a single ECS Fargate task. The eligibility engine runs inside the same task as the REST API.

Under month-end load, 20 simultaneous eligibility jobs compete for CPU with API requests in the same container. The design does not describe:
- Whether eligibility jobs run in a dedicated thread pool or process pool, isolated from API request handling
- What the task autoscaling policy is (the OPEX table shows "2 tasks base, 4 tasks at month-end" but doesn't describe the scaling trigger or warm-up time)
- What the maximum file size is for a counterparty submission, and whether large-file eligibility computation blocks the task indefinitely
- Whether the 15-minute SLA is per-counterparty from that counterparty's file submission, or from the start of the month-end window (which would require knowing when all counterparties have submitted)

The SLA is stated as a requirement but the mechanism to satisfy it under concurrent load is not designed.

---

## Questionable Assumptions

**1. "The reinsurer is the sole trusted custodian — counterparties accept this."**
The KMS-signed receipt at `CycleSealed` proves the sealed state. It does not prove that intermediate states (the eligibility proposal, the adjustment amounts, the L1/L2 approval decisions) were not manipulated before sealing. A counterparty can dispute the eligibility calculation itself, not just the fact that a cycle was sealed. The inter-party trust gap is closed at the seal event but remains open throughout the negotiation phase. The design accepts this implicitly; it should be stated explicitly as a known limitation.

**2. "100 reconciliation managers currently."**
The ROI model is built on this figure. The conservative break-even assumes 50 remaining managers (2× reduction) saving £2.75M/year. If the actual headcount is 40 managers with more modest salary expectations, the break-even extends considerably. This number must be validated with the client before the proposal is presented — the document should not carry it as a given.

**3. "The expression tree covers all contract types."**
UK longevity reinsurance contracts are among the most formula-intensive financial instruments in the market. Assumed away as a Phase 1 gate item. This assumption carries more schedule risk than any other single technical decision in the design.

**4. "10-30 counterparties at launch; RLS single-schema multi-tenancy is sufficient."**
This is reasonable at 30. At 50+, schema migration complexity grows proportionally and cross-tenant platform-operator queries (for compliance reporting across all tenants) become increasingly painful in a single-schema model. The assumption is probably correct for Phase 1 but should be explicitly revisited at the Phase 4 retrospective.

**5. "Budget is not the primary constraint; ~$700K CAPEX is acceptable."**
The document states this but does not validate it. If the expression tree gate fails and a DSL is needed, CAPEX could reach $900K–$1M before Phase 2 is complete. The innovation initiative framing suggests budget flexibility, but no upper bound is stated. A ~$300K overrun may still be acceptable; the design should say so rather than treating budget as unlimited.

**6. "Monthly submission cadence; load test covers the real workload."**
The load test simulates 20 concurrent month-end file uploads. If the actual counterparty book includes annual longevity contracts that submit significantly larger files (hundreds of thousands of individuals per file rather than tens of thousands), the 15-minute eligibility SLA and the load test design may not represent the real peak.

---

## Alternative Designs

### Option A: Excel-as-a-Service + Workflow Portal (radically simpler)

**What changes:** Do not build a custom expression tree evaluator. Wrap the existing Excel spreadsheet files as server-side calculation services — Python with openpyxl executes the existing Excel formulas on the server. Reconciliation managers continue to maintain contracts in Excel (version-controlled in S3). Build everything else from the current design: the portal, the workflow state machine, the audit ledger (`cycle_events` append-only), RLS multi-tenancy, Cognito authentication.

Replace the expression tree evaluator with the Excel engine in Phase 1. Migrate contracts to an expression tree one by one in Phase 2 as the business validates each formula set.

**CAPEX:** ~$400K | **Timeline:** 6 months | **Team:** 1 Architect + 2 Senior Devs + 1 QA

| Pros | Cons |
|------|------|
| No formula extraction risk; Excel correctness is assumed, not re-proven | Excel files become server-side deployment artifacts needing version control and CI/CD |
| Phase 1→2 gate trivially passes — no new engine to validate | Excel is not designed for concurrent server execution; scaling beyond 20 concurrent calculations requires careful locking |
| First counterparty live in 4 months instead of 7.5 | Does not achieve the "eliminate Excel dependency" goal without a later Phase 2 expression tree migration |
| Reconciliation managers remain empowered; adoption friction reduced | Harder to audit the exact calculation steps at the formula level |
| Eligibility output still recorded in `cycle_events` for compliance | Long-term: two calculation engines (Excel + expression tree) must be maintained in parallel during migration |

**When to choose this:** If the formula extraction risk is assessed as high during the Phase 1 discovery (more than half of contracts have undocumented or individually held Excel formulas), Option A de-risks the platform launch and defers the harder problem. It is not a cop-out — it is a risk-sequencing decision.

---

### Option B: Option 2 without Debezium — Direct Archive Write

**What changes:** Keep Option 2 in full (portal, expression tree evaluator, RLS, state machine, KMS receipts). Replace the Debezium CDC sidecar with a simpler pattern:

1. In the same transaction as every `cycle_events` INSERT, write to a `cycle_events_export` table (identical schema, staging buffer).
2. A scheduled job (every 15 minutes) bulk-exports new rows from `cycle_events_export` to S3 Glacier as Parquet and deletes the exported rows.
3. `cycle_events_export` is a staging buffer, not a compliance archive — the operational `cycle_events` table (RLS-enforced, Multi-AZ, RPO=0) remains the authoritative record.

The compliance archive lag increases from near-real-time to 15 minutes. For a 10-year Solvency II retention archive, this is acceptable.

**CAPEX:** ~$680K (saves ~$20K in CDC engineering) | **Timeline:** 9 months | **Same team**

| Pros | Cons |
|------|------|
| Eliminates all WAL replication slot risk | Compliance archive is 15 minutes behind the live event log, not near-real-time |
| No Debezium connector management, schema registry, or crash recovery | A system failure between events and the next export job could lose up to 15 minutes of archive entries — though `cycle_events` in RDS Multi-AZ is unaffected and remains the authoritative record |
| Audit archive readable directly from S3 without Athena | Slightly more application-layer code (staging table + export job) vs. a sidecar |
| Easier to explain to compliance team: "we write every event to S3 every 15 minutes" | |
| Removes a moving part that requires specialist knowledge to operate | |

**When to choose this:** Unless the compliance team or a regulator specifically requires near-real-time archive synchronisation, Option B's simplification is worth taking. The 15-minute lag has no practical impact on a 10-year compliance archive.

---

## Final Recommendation

**Adopt Option 2 with two targeted modifications.**

**Modification 1 — Replace Debezium with direct archive write.**
The WAL replication slot failure mode is a real operational risk with no elegant recovery path. The simplification is architecturally clean: same atomicity guarantee (both `cycle_events` and the export record are committed in the same transaction), same S3 Glacier destination, simpler operational model. The 15-minute archive lag is not a compliance issue. Do this in Phase 2 when the audit ledger is built, not as a later refactor.

**Modification 2 — Harden the expression tree gate to 100% coverage, with fallback defined in Phase 1.**
Change the gate condition from "fewer than 20% of contracts need additional node types" to "all identified contract types are fully expressible in the initial node set, or the fallback approach is designed and scoped before Phase 2 budget is committed." Spend the first two weeks of Phase 1 on the most complex contracts in the book — not the most accessible ones. If mortality table lookups are needed, design the `lookup` node type in Phase 1. Do not build a 7-node evaluator and discover the gap at the gate.

Everything else in Option 2 stands. The modular monolith on ECS Fargate is the right compute pattern for a monthly-burst workload with a 6-person team. RLS multi-tenancy is pragmatic for the stated counterparty scale and correctly implemented with `SET LOCAL`. The KMS-signed receipt at `CycleSealed` is an elegant and sufficient solution to the inter-party trust problem without blockchain. The `cycle_events` append-only log with RLS-enforced INSERT-only is the right audit architecture for this problem.

The design is not overengineered. Two specific operational risks — Debezium and the expression tree gate — are worth fixing before Phase 1 begins. Everything else should be built as designed.
