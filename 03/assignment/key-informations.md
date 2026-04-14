# Case Study 03 — Key Informations

> Extracted from client meeting transcription. Personal data anonymized.
> Speakers: **Solution Architect / Mentor** (consulting side) and **Mentee Architect** (learner side).

---

## Business Context

- **Client type:** Existing enterprise — UK-based reinsurance firm
- **Domain:** Reinsurance — "insurance of insurers"; when insurance companies face large longevity or pension risk, they offload packages to a reinsurer
- **Business model:** Pure B2B — no direct consumer interactions; all counterparties are independent insurance companies
- **Market:** UK-headquartered, with international counterparties across multiple countries (Europe and beyond)
- **Business goal:** Automate the inter-company reconciliation process and reduce the reconciliation manager headcount by 2–4× (illustratively: from ~100 managers to 25–50)
- **Investment framing:** Part of the client's innovation strategy; budget is not the primary constraint

## Current Technical Landscape

- **Primary tool:** Microsoft Excel — all reconciliation logic lives in Excel spreadsheets ("Excel magic")
- **Exchange mechanism:** Files sent back and forth between parties via email or manual file transfer
- **Process owners:** Large team of reconciliation managers who validate, proof, and sign off on each monthly cycle
- **Contracts:** Defined separately (legal documents); reconciliation managers manually apply contract rules to incoming data files
- **No existing platform:** No shared digital infrastructure between the reinsurer and its counterparties for this process

## Business Flow

1. **Contract established** — reinsurer and an insurer agree on a contract defining rules, formulas, percentages, eligible populations, and total risk coverage
2. **Monthly data file received** — the insurer sends a file listing people still alive within the covered pension/longevity package
3. **Eligibility determination** — the reinsurer's team applies contract rules to the file to calculate who is eligible for compensation and how much
4. **Compensation flows** — money moves B2B (from reinsurer to insurer or vice versa, depending on the contract conditions); this is **not** consumer payment — no payment service provider integration is needed
5. **Multi-round reconciliation** — parties exchange files, proposals, and adjustments multiple times until both sides sign off (chain of 2–4+ people per cycle)
6. **Backtracks and adjustments** — corrections from prior months are folded into subsequent cycles as explicit adjustment records

### File Content Types (within a reconciliation cycle)

| File type | Purpose |
|-----------|---------|
| People tables | List of insured individuals still alive (defines active risk exposure) |
| Money movement tables | Calculated compensation amounts per contract conditions |
| Special condition tables | Exceptions or edge cases defined per contract |
| Adjustment records | Corrections for prior-month mistakes or reclassifications |
| Contract exceptions | Deviations from standard contract terms for specific cases |

## Technical Guidance from Meeting

### Why Trust Is the Core Architectural Challenge

Insurance companies are fully independent, often multi-national entities that inherently do not trust each other. Today, **armies of people** establish this trust through manual verification. The platform must replace this human trust layer with a **verifiable, tamper-evident digital trust layer** — so that any party can confirm:

- The file received is the file that was sent (no tampering)
- The calculations applied are consistent with the agreed contract
- Every change, adjustment, and sign-off is recorded and traceable
- Money movements are backed by a signed, auditable record

### On Blockchain (Explicitly Out of Scope)

The blockchain approach is a common instinct for multi-party trust problems, but was ruled out for this type of system:

- Blockchain overhead (consensus protocols, node synchronization, throughput limits) is designed for **trustless multi-party environments with no central custodian**
- Here, the reinsurer **is** the custodian — a single trusted party hosts the platform
- A single-custodian auditable database achieves the same trust guarantees without blockchain overhead
- Lesson learned from a related financial project: a single-party system convinced of needing blockchain was eventually redesigned around a standard database — saving significant operational complexity

### Immutability Technology Options

| Option | Notes |
|--------|-------|
| AWS QLDB | Fully managed single-party immutable ledger; now discontinued by AWS |
| immuDB | Go-based open-source immutable + mutable hybrid (SQL + key-value); consistency and transaction issues emerged in production when integrated from .NET via gateway |
| PostgreSQL + immutability plugin | Pragmatic recommendation; PostgreSQL's extension ecosystem (pgaudit, temporal tables) covers most immutability requirements; battle-tested operationally |

**Guideline:** Prefer the boring, proven option. Specialized databases often look attractive in development but surface consistency and transaction management problems at production load. PostgreSQL with extensions almost always suffices.

### Contract Flexibility

Contracts between reinsurer and insurer vary — different formulas, different eligible populations, different percentage structures. The system must:

- Accept a contract definition as structured metadata (not hardcode contract logic)
- Parse incoming data files against the contract's rules dynamically
- Not constrain contract authors to a rigid schema that breaks when a new contract type is introduced

## Task Breakdown (Architecture Approach)

1. **Domain research** — study reinsurance domain, longevity risk, Solvency II framework, UK FCA audit requirements
2. **Discovery questionnaire** — pre-fill assumptions from this meeting; send to client for validation
3. **Trust architecture** — define the trust model: what is the authoritative record, how is tamper-evidence established, what does a "signed off" state mean
4. **Solution design** — document architecture options with trade-offs; recommend the approach that is auditable, maintainable, and avoids over-engineering

## Key Constraints

- ✅ **Multi-party, multi-country** — counterparties are independent international entities; data residency and regulatory jurisdiction are open questions
- ✅ **Trust by design** — every file, change, and approval must be cryptographically verifiable or at minimum audit-logged to an immutable record
- ✅ **Dynamic contract structure** — the system must not be constrained by a rigid schema; contract rules define structure at runtime
- ❌ **No blockchain** — overhead not justified; the reinsurer is the single custodian
- ❌ **No consumer payment integration** — money movements are B2B bank transfers handled outside the platform
- ❌ **No client adoption concern** — counterparties are bound by contract and will onboard; adoption strategy is out of scope
- ⚠️ **Budget** — not the primary constraint; this is an innovation initiative
- ⚠️ **Regulatory compliance** — UK FCA, Solvency II (EU/UK), and GDPR (EU counterparties) all have implications — requires domain research
- ⚠️ **Legacy Excel logic** — reconciliation managers may claim the Excel formulas are too complex to extract; this has been overcome on similar projects before

## Key Differences from Case Studies 01 & 02

- **01 (TourLens):** Greenfield consumer mobile app — business logic and UX were the primary design surface
- **02 (E-commerce platform):** Enterprise data pipeline — ETL, analytics, and ML recommendation engine
- **03 (Reinsurance):** B2B trust infrastructure — the design challenge is **not** business logic or feature richness, but establishing a verifiable, auditable, multi-party trust layer
- Unlike 01 and 02, there are no end consumers and no user-facing product features to design; the system's core value is correctness, auditability, and trust — not engagement or analytics

## Assignment Context (Meta)

- This case study is based on a real production project that started with a team of 5 and grew to 70+ engineers over time
- The assignment is intentionally open-ended and abstract — there is no single correct architecture; discovery and framing are as important as the solution itself
- Follow-up questions may be sent asynchronously between sessions; the mentor will respond without waiting for the next meeting
- Domain research into reinsurance (longevity risk, Solvency II, contract lifecycle) is part of the architect's expected work before completing discovery

---

**Extracted by:** Solution Architect
**Date:** 2026-04-14
**Source:** Meeting transcription (VTT recording)
