# Architecture Challenge — Case 03: Reinsurance Reconciliation Platform

**Type:** AI-assisted architecture review  
**Author:** Tomasz Mosur  
**Date:** 2026-04-27  
**Subject:** Senior consultant challenge of the Option 2 solution design

---

## Challenge Summary

The solution design recommends **Option 2** — a full platform with an application-layer state machine and a dual-layer audit ledger (S3 Object Lock + PostgreSQL hash-chain). The recommendation is broadly sound: the problem domain is well understood, the technology choices are proven, and the phased delivery plan is realistic.

However, several design decisions warrant challenge. Some introduce hidden complexity; one leaves the core trust requirement only half-solved. A targeted set of changes — outlined below — would produce a simpler, more trustworthy, and more commercially resilient architecture without changing scope or budget materially.

---

## What the Design Gets Right

Before challenging, it is worth anchoring what is already correct:

- **Contract rules as expression trees** is the right abstraction for avoiding hardcoded logic. The approach is extensible and can be validated at upload time.
- **Row-Level Security at the database layer** is the correct place to enforce tenant isolation — not just at the API layer.
- **Application-layer state machine over AWS Step Functions** is the right call for a domain where the state transition logic is deeply coupled to business rules that will change during Phase 1.
- **Decimal strings in JSON rather than IEEE 754 floats** for financial amounts is a critical correctness decision often missed at design time.
- **The phased gate structure** (Excel regression before eligibility engine, first counterparty UAT before full go-live) reflects mature delivery thinking.
- **The Investigation Period** as the first post-signing phase is correct; committing to architecture before extracting three real contracts from Excel is a significant risk.
- **10-year audit retention** for Solvency II and the data residency model (eu-west-2 primary, eu-west-1 DR) are correctly specified.

---

## Eight Challenges

### Challenge 1 — The Trust Gap: Counterparties Cannot Independently Verify

**Observation.** The design's core premise is replacing "trust via humans" with a cryptographic audit trail. Yet the reinsurer controls 100% of the infrastructure. S3 Object Lock prevents *deletion* but does not prevent the platform owner from writing a new version of an object before locking it. The PostgreSQL hash-chain is verified weekly — by a job running inside the reinsurer's own infrastructure. The counterparty has no mechanism to verify that what was sealed matches what they submitted.

**Risk.** A sophisticated counterparty's legal team will identify this gap during onboarding. The "tamper-evident audit" claim does not hold against an adversarial reinsurer. This undermines the platform's core value proposition in any dispute.

**Recommendation.** At cycle seal, generate a signed receipt: a KMS-signed JSON document containing the cycle ID, tenant ID, sealed-at timestamp, file SHA-256 hashes, and the hash of the audit ledger entry. Deliver this receipt to the counterparty (via email + portal download) at the moment of sealing. The counterparty stores it independently. If a dispute arises, both parties can compare receipts. This costs nothing architecturally and fully closes the trust gap — which is what the requirements document describes as "verifiable, tamper-evident digital trust layer."

---

### Challenge 2 — Dual-Layer Audit Adds Operational Complexity Without Full Coherence

**Observation.** The design proposes dual-write: write to S3 Object Lock first (system of record), then write to PostgreSQL hash-chain (query layer). If the S3 write succeeds but the PostgreSQL write fails, the two layers diverge. The design does not describe a compensation or reconciliation mechanism for this failure mode.

**Risk.** Under the dual-write model, the weekly verification job could detect chain gaps caused by transient infrastructure failures rather than actual tampering — creating false-positive audit alerts. Operationally, investigating whether a gap is a bug or a breach is expensive and stressful during a regulatory audit.

**Recommendation.** Invert the architecture: make PostgreSQL the authoritative system of record (append-only `audit.events` table with hash-chain, backed by RLS so no application user can UPDATE or DELETE). Use S3 with Object Lock as the cold archive and backup target, written asynchronously. A single PostgreSQL hash-chain is simpler to audit (one chain, one verification tool, one source of truth), and the asynchronous S3 copy removes the dual-write atomicity problem entirely. Combined with CloudTrail logging of all DML, this exceeds the tamper-evidence requirement.

---

### Challenge 3 — Option 3 (Event Sourcing) Was Not Dismissed on the Right Grounds

**Observation.** The design dismisses Option 3 as "highest complexity and cost." This is true if event sourcing is implemented as full CQRS with separate read models and an event store framework. But it misses a simpler framing: reconciliation *is naturally event-based*. A monthly cycle produces a fixed sequence of events: `FilesReceived`, `EligibilityCompleted`, `ReviewStarted`, `AdjustmentProposed`, `CounterpartySigned`, `CycleSealed`. These events are the business record. If you store them in an append-only events table, the current state is always derivable by replaying the log — and you no longer need a *separate* audit ledger, because the event log *is* the audit trail.

**Risk.** The current design maintains two representations of truth: the application state (in relational tables) and the audit ledger (hash-chain). Keeping them in sync is the source of several design risks the document identifies (dual-write failure, adjustment handling, snapshot vs. delta debate).

**Recommendation.** Do not switch to full event sourcing (the design's concern about complexity is valid if taken to the extreme). Instead, consider whether the `audit.events` table can be promoted to the primary write target, with application state derived from it rather than maintained separately. This is "event log as source of truth" without CQRS overhead. The state machine becomes a validation layer over the event log rather than an independent state store. Worthy of an ADR that explicitly compares the two models before Phase 2 begins.

---

### Challenge 4 — Aurora Serverless v2 Is the Wrong Choice for a Monthly-Burst Workload

**Observation.** Aurora Serverless v2 scales compute up and down based on load. Monthly reconciliation means near-zero load for ~25 days, then a burst over 3–5 days when counterparties submit files and eligibility runs. The design itself acknowledges cold starts as a risk (Risk R-08). Aurora Serverless v2 does not fully cold-start (it maintains a minimum ACU floor), but scaling from minimum to processing 20 concurrent eligibility jobs takes time, and the minimum ACU floor adds cost even during idle periods.

**Risk.** For 10–30 counterparties, month-end peak load is predictable and bounded. Aurora Serverless auto-scaling brings billing unpredictability and operational uncertainty without meaningful benefit at this scale. The "right size" changes between phases as counterparty count grows, creating repeated infrastructure debates.

**Recommendation.** Use RDS PostgreSQL (db.t4g.medium or db.r7g.large) with Multi-AZ in eu-west-2. The monthly cost is comparable to Aurora Serverless at low ACU floors, there are no cold-start surprises, and the instance can be right-sized at each phase gate based on real load data. Migrate to Aurora (provisioned or Serverless) only if the counterparty count genuinely exceeds 50 and query patterns demand it.

---

### Challenge 5 — Expression Tree Phase 1 Risk Is Underestimated

**Observation.** The design correctly identifies extracting Excel formulas as a risk (Risk R-01) but rates it "Medium likelihood." The Phase 1 gate requires expressing three contract types as JSON expression trees. In practice, Excel-based actuarial rules often contain:
- Implicit column-header logic (`IF($B$3="Type A", ...)`)
- Circular references or iterative calculation modes
- Embedded lookups in named ranges that reference other sheets
- Rule exceptions added verbally by account managers, not in the formula

None of these translate cleanly into expression trees.

**Risk.** If the three pilot contracts cannot be expressed within the defined node types, the Phase 1 gate fails or is waved through with technical debt. The design notes "if >20% of contracts need new node types, escalate to DSL" — but this check happens *after* Phase 1, not before.

**Recommendation.** During the Investigation Period, extract and document the three pilot contracts in a human-readable rule specification *before* designing the expression tree schema. Use that specification to define the required node types bottom-up. This inverts the risk: the schema is validated against real contracts before a line of code is written. Add this as an explicit Investigation Period deliverable.

---

### Challenge 6 — AWS Transfer Family SFTP Is the Wrong Primary Integration Pattern

**Observation.** The design includes AWS Transfer Family (SFTP) in the OPEX baseline (~$216/month) and frames it as a counterparty integration path. For a 2024–2025 platform targeting reinsurance firms (primarily pension administrators and large insurers), SFTP requires counterparties to maintain SFTP client configuration, key management, and scheduled transfer scripts. This is non-trivial operational overhead on the counterparty side and creates a support burden for the platform team.

**Risk.** SFTP adoption friction could slow counterparty onboarding and delay the "first counterparty live" milestone — the most commercially critical gate in the delivery plan.

**Recommendation.** The primary integration pattern should be the web portal (secure authenticated file upload via pre-signed S3 URLs — already in the design). SFTP should be a fallback for counterparties with legacy batch export infrastructure. Remove AWS Transfer Family from the OPEX baseline; provision it on-demand when the first SFTP-requiring counterparty is confirmed. This reduces OPEX, removes an operational dependency, and keeps onboarding simpler for the majority case.

---

### Challenge 7 — SAML Deferred to Phase 2 Creates Enterprise Onboarding Risk at the Worst Moment

**Observation.** ADR-005 defers SAML/federated identity to Phase 2+. The design's first live counterparty (targeting Month 7.5) will therefore use Cognito username/password with MFA. For reinsurance counterparties — large pension funds, global insurers, Lloyd's syndicates — federated SSO via their corporate identity provider is standard security policy. Many will have internal IT policies *prohibiting* the creation of third-party username/password accounts for staff accessing financial platforms.

**Risk.** The pilot counterparty discovers during onboarding that SAML is not available. Escalating to their CISO delays sign-off. The first-counterparty-live milestone slips, which delays the business case validation and puts the break-even timeline at risk.

**Recommendation.** Bring basic SAML support (Cognito User Pools with SAML federation) into Phase 2, not deferred beyond it. Cognito's SAML integration is a configuration exercise, not a significant engineering effort. The Investigation Period should include asking the two most likely pilot counterparties whether they require federated identity — if yes, Phase 2 must deliver it before the Phase 3 go-live.

---

### Challenge 8 — Modular Monolith Boundaries Are Underspecified

**Observation.** ADR-006 selects a modular monolith on ECS Fargate and acknowledges that "module boundaries must be enforced by convention during development." The design does not define those boundaries explicitly. Without a published module inventory (e.g., `ingestion`, `eligibility`, `workflow`, `audit`, `portal`, `notifications`), developers will organise code according to their own mental models. Six months into development, the "modular monolith" will be a conventional monolith with unclear extraction paths.

**Risk.** If the platform grows toward Option 3 or toward SaaS commercialisation (both mentioned in the evolution roadmap), extracting services from an ill-bounded monolith is the hardest possible migration. The design's stated future migration path depends on the boundaries being real.

**Recommendation.** Add a module boundary diagram to the solution design — six to eight named modules with explicit public interfaces (what each module exports vs. what it must import). Mandate a lint rule (e.g., ArchUnit for JVM, or a custom module graph check) that fails the build if a module imports from another module's internal package. This is a one-day investment that protects the entire delivery.

---

## Alternative Architecture: Simplified Trust-First Design

The challenges above point to a coherent alternative that simplifies the current design while strengthening its core trust claim.

### Core Changes

| Current Design | Alternative |
|---|---|
| Dual-write: S3 Object Lock (primary) + PostgreSQL hash-chain | Single PostgreSQL append-only event log (primary) + async S3 archive |
| State machine + separate audit ledger | Event log is both state history and audit trail |
| Aurora Serverless v2 | RDS PostgreSQL (provisioned, right-sized per phase) |
| AWS Transfer Family SFTP (in OPEX baseline) | Portal upload primary; SFTP provisioned on demand |
| No counterparty receipt | KMS-signed cycle receipt issued to counterparty at seal |
| SAML deferred past Phase 2 | SAML in Phase 2, before first counterparty live |

### What This Eliminates

- Dual-write atomicity problem and its compensation complexity
- False-positive audit alerts from infrastructure-induced chain gaps
- Aurora Serverless cold-start risk and billing unpredictability
- Standing SFTP infrastructure cost (~$216/month) before it is needed
- The trust gap that leaves counterparties unable to independently verify

### What This Preserves

- All eight functional epics (no scope change)
- The expression tree eligibility engine (no change)
- The approval workflow state machine (no change — it becomes an event-emitting layer)
- The multi-tenant RLS model (no change)
- The phase gate structure and delivery timeline (no material change)
- The $757K CAPEX and OPEX estimates (minor reduction from removing Transfer Family baseline)

### Trade-offs

The event-log-as-source-of-truth model requires developers to think in events rather than mutable state when writing new features. This is a discipline cost. It pays off in auditability and in the eventual Option 3 migration path (the event log is already the foundation). If the team has no event-sourcing experience, the Investigation Period should include a one-week spike.

---

## Verdict

**Option 2 is the right recommendation.** The scope, timeline, and technology choices are sound for this problem domain and scale.

The design should be strengthened in three high-priority areas before Phase 1 begins:

1. **Add signed cycle receipts** (closes the trust gap — high value, near-zero cost)
2. **Replace dual-layer audit with a single PostgreSQL append-only event log** (removes dual-write atomicity risk and simplifies the operational model)
3. **Replace Aurora Serverless with provisioned RDS** (removes cold-start risk and billing unpredictability for a bounded monthly-burst workload)

Two medium-priority improvements for Phase 1:

4. **Add explicit module boundary diagram and enforce it at build time**
5. **Move SAML federation into Phase 2** and confirm pilot counterparty identity requirements during the Investigation Period

One investigation-period change:

6. **Extract pilot contract rules first, then design the expression tree schema bottom-up** (not top-down as currently implied)

None of these changes affect the fundamental architecture. Option 2 remains the correct choice. These refinements close its most significant gaps.
