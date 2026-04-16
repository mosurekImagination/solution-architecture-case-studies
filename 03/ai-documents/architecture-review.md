# Exercise 03 — Architecture Review (AI-Assisted)

**Exercise:** Reinsurance Reconciliation Platform — B2B Trust Infrastructure
**Author:** Tomasz Mosur
**Date:** 2026-04-16
**Type:** AI-assisted architecture review — produced as part of the mentorship exercise simulation

---

## Overall Assessment

**Grade: Strong Pass — Production-Ready Thinking**

This is a well-executed discovery-to-design cycle. The work demonstrates genuine architectural thinking rather than template-filling. The core insight — that the problem is *trust*, not workflow automation — is correct, non-obvious, and drives every downstream decision well. The deliverable is at a standard suitable for presenting to a CTO or compliance board.

---

## What Was Done Well

### 1. Problem Framing (Excellent)

The design correctly identified the central tension: two independent entities with conflicting financial interests must agree on numbers — and the current process relies entirely on human goodwill and email chains. This is not a "build a portal" problem; it is a "replace trust infrastructure" problem. That reframe is the hardest part of this exercise, and it landed correctly.

### 2. Technology Choice Rationale (Excellent)

The decision to use PostgreSQL + SHA-256 hash chain over blockchain, QLDB, or immuDB is the right call, and it is argued well. ADR-001 captures the thinking clearly:

- Blockchain: immutability comes with operability cost; no consortium governance model fits
- QLDB: AWS discontinued the service; lock-in risk
- immuDB: production incidents on prior projects; opaque internals
- PostgreSQL hash chain: auditable, well-understood, team-maintainable, battle-tested

This is an example of *principled simplicity* — the goal was not to use the flashiest tool but to solve the actual problem.

### 3. Three-Option Structure (Good)

Presenting three options with a clear recommendation is correct consulting practice. The options are meaningfully differentiated:

- Option 1: MVP/POC — intentionally limited; honest about scale ceiling
- Option 2: Full Platform — recommended; pragmatic balance of capability and risk
- Option 3: Event-Sourced — future-proof but over-engineered for current scale

The cost/timeline spread ($165K–$1.1M, 3–13 months) gives the client a real choice, not a false one.

### 4. Architecture Decision Records (Good)

Five ADRs documented with context, options considered, and rationale. This is not just a record of *what* was decided — it captures *why*. Future engineers will understand the reasoning, not just the outcome. ADR-002 (RLS over schema-per-tenant) and ADR-003 (Step Functions over custom state machine) are particularly solid.

### 5. Cost Model Transparency (Good)

The cost breakdown is specific and honest:

- Team costs itemized by role and duration
- 20% contingency included and explained
- OPEX broken out by AWS service (11 services listed)
- 3-year TCO calculated
- Phase cost distribution shown

This level of transparency builds client trust and prevents scope disputes.

### 6. Post-Launch Plan (Strong)

Most junior architects stop at "go live." This design includes a 4-week hypercare plan, a 7-step counterparty onboarding runbook, and a hash-chain integrity monitoring schedule. This is what separates architectural deliverables from academic exercises.

---

## Areas for Improvement

### 1. Eligibility Engine Design Gap (Critical)

**What's missing:** The eligibility engine is the core business logic of the platform — it applies contract rules to determine what money is owed. The design correctly flags that Excel formulas must be extracted, but it does not address *how* those rules will be encoded, tested, or maintained.

**Why this matters:** Excel formula extraction is notoriously risky. Reconciliation managers often do not fully understand the formulas they maintain — they know the inputs and outputs but not the derivation. An architect needs to answer:

- What is the metadata schema for a contract rule? (JSON structure, example provided)
- How does the engine execute a rule? (interpreted vs. compiled DSL vs. code-generated functions)
- How do you validate the engine output matches the historical Excel output? (regression test dataset needed)
- What happens when a rule changes mid-cycle? (versioning strategy)

**Recommendation:** Add a contract rule schema example and a testing approach for eligibility validation (compare engine output to 12 months of Excel history for 2–3 representative counterparties).

### 2. Multi-Tenancy Isolation Depth (Moderate)

**What's good:** RLS is correctly chosen. The data model shows `tenant_id` on operational tables.

**What's missing:** The security model does not address:

- What happens if a Cognito token is stolen? Can a counterparty escalate to another tenant's data by replaying a request?
- How are API-layer tenant assertions validated beyond JWT claims? (Defense in depth: the application layer should enforce tenant isolation independently of RLS)
- How are cross-tenant reporting queries handled for the reinsurer's compliance users who need a view across all counterparties?

**Recommendation:** Add a brief security threat model covering cross-tenant access scenarios. Two scenarios are sufficient: credential theft and privilege escalation.

### 3. Regulatory Compliance Specificity (Moderate)

**What's good:** Solvency II and FCA record retention (10 years) are correctly cited. The audit ledger design is framed around these requirements.

**What's missing:**

- **Solvency II Pillar III (Article 259):** Requires documented audit trail of actuarial computations. The hash-chain ledger addresses tamper-evidence, but the design does not confirm whether the *content* of audit events (the actual calculation inputs and outputs) meets Article 259's data granularity requirements.
- **FCA SYSC 9.1:** Requires records of all client-facing communications. The current design logs file submissions and approvals but does not explicitly capture negotiation messages (adjustment requests and responses) in the audit ledger.
- **GDPR Article 17 (Right to Erasure):** The append-only audit ledger explicitly cannot delete records. This creates a legal tension if counterparty employees' personal data (names, email addresses) are embedded in audit events. The design does not address this.

**Recommendation:** Add a compliance gap analysis table (3 rows: Solvency II, FCA SYSC, GDPR erasure) with the proposed handling for each. The GDPR issue in particular needs a resolution — the standard approach is to store personal identifiers as references to a separate mutable identity table, not inline in the audit log.

### 4. Counterparty Onboarding Friction (Moderate)

**What's good:** The onboarding runbook is included. SAML federation is planned for the reinsurer's internal users.

**What's missing:** Counterparty technical capabilities vary widely. Some may be able to federate via SAML (large insurers). Others may be smaller firms with no corporate IdP. The design shows a Cognito external user pool but does not differentiate:

- SAML-capable counterparties → federate directly
- Non-SAML counterparties → Cognito username/password with MFA
- SFTP-only counterparties → no portal, file-based only

**Recommendation:** Add a counterparty integration tier model with 2–3 tiers and the authentication/file-exchange mechanism for each. A small table is sufficient.

### 5. Gantt Chart Missing Phase Gates (Minor)

**What's good:** 8-month timeline, 4 phases, first go-live at end of Phase 3.

**What's missing:** Phase gates — explicit pass/fail criteria that must be met before the next phase begins. Without gates, a project can slide from Phase 1 into Phase 2 before the domain knowledge extraction is complete, leading to rework.

**Recommended gates:**

- Phase 1 → Phase 2 gate: Eligibility engine reproduces 100% of historical Excel output for 3 counterparty contract types; compliance workshop complete and findings resolved
- Phase 2 → Phase 3 gate: RLS penetration test passed; hash-chain tamper detection verified with 6-month synthetic dataset
- Phase 3 → Phase 4 gate: First counterparty UAT signed off; month-end cycle completed end-to-end in staging

---

## Structural Observations

### Domain Primer Quality

The domain primer is exceptional for this exercise. It is written as if the author needed to teach themselves from first principles — which is the correct approach when entering an unfamiliar domain. The visual walkthrough of the before/after reconciliation cycle is particularly clear. If this document existed when the first reconciliation manager joined, onboarding time would halve.

### Questionnaire Pre-Fill Strategy

Pre-filling the questionnaire before sending it to the client is a sound technique. It signals preparation, anchors the client's answers to the right framework, and surfaces assumptions for validation rather than leaving them implicit. The 14 flagged questions are the right ones — they are the items where the wrong assumption would change the architecture.

### ADR Format

The ADRs are well-structured. One suggestion: add a **"Revisit trigger"** field to each ADR — a condition that would prompt reconsidering the decision. For example: ADR-001 should be reconsidered if the number of counterparties exceeds 100 and cross-chain query performance degrades. This prevents ADRs from becoming fossilized decisions.

---

## Summary Scorecard

| Dimension | Score | Notes |
|---|---|---|
| Problem framing | 5/5 | Core trust insight landed correctly |
| Technology choices | 5/5 | PostgreSQL hash chain is correct and well-argued |
| Architecture coverage | 4/5 | Strong; eligibility engine and compliance specificity gaps |
| Options analysis | 4/5 | Three options well-differentiated; cost model honest |
| Risk & assumptions | 4/5 | 6 risks identified; GDPR/regulatory depth could improve |
| Client-readiness | 4/5 | Suitable for CTO/compliance presentation with minor additions |
| Domain depth | 4/5 | Primer excellent; regulatory specifics need Phase 1 workshop |
| Post-launch plan | 5/5 | Hypercare, monitoring, knowledge transfer all included |

**Overall: 4.4 / 5 — Exercise complete. Ready for client presentation with minor additions.**

---

## Key Questions for Self-Reflection

1. **Eligibility engine:** How would you approach validating that your implementation matches the existing Excel logic? What would your regression test dataset look like?

2. **GDPR vs. append-only ledger:** A counterparty requests deletion of an employee's data under Article 17. What do you do?

3. **Phase gate definition:** What would cause you to *not* proceed from Phase 1 to Phase 2? What does a failed phase gate look like in practice?

4. **Excel formula extraction risk:** You discover in Week 3 of Phase 1 that the reconciliation manager cannot explain how three of the five formula columns work — they inherited the Excel file and have been running it without understanding it. What do you do?

5. **Counterparty resistance:** A major counterparty says they will not use the portal and will continue sending Excel files by email. How does your architecture handle them, and at what cost?
